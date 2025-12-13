from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver # For dev, use Postgres for prod

from app.agents.workflows.drafting.state import DraftState
from app.agents.workflows.drafting.schema import AgentNode, QAStatus

# Import Nodes
from app.agents.workflows.drafting.planner import planning_node
from app.agents.workflows.drafting.context_manager import context_init_node, context_manager
from app.agents.workflows.drafting.writer import writer_node
from app.agents.workflows.drafting.reviewer import reviewer_node
from app.agents.workflows.drafting.assembler import assembler_node
from app.agents.workflows.drafting.refiner import refiner_node

# Import Router
from app.agents.workflows.drafting.router import router

# Import optimization utilities
from app.agents.workflows.drafting.loop_prevention import LoopPreventor, check_workflow_health

# Global loop preventor instance (per workflow run)
# In production, this would be stored in state or session
loop_preventor = LoopPreventor(
    max_total_iterations=10,
    max_section_revisions=3,
    max_writer_reviewer_cycles=2
)

# --- Data Loader Node ---

async def load_data_node(state: DraftState):
    """
    Load case data, documents, and template before planning starts.
    Now delegated to ContextManager for centralized handling.
    """
    return await context_manager.load_initial_data(state)

# --- Smart Resolution Node ---

async def smart_resolution_node(state: DraftState):
    """
    Attempt to resolve missing information using AI deduction.
    Uses explicit missing_keys_detected from Reviewer (preferred) or falls back to heuristics.
    """
    print("--- [SmartResolution] Attempting to deduce missing facts ---")

    # PRIORITY 1: Use explicit missing keys from Reviewer (most reliable)
    missing_keys = state.get("missing_keys_detected", [])

    if missing_keys:
        print(f"  ✓ Using explicit missing keys from Reviewer: {missing_keys}")
    else:
        # FALLBACK: Use dynamic regex extraction (backwards compatibility)
        print("  ⚠️  No explicit missing keys from Reviewer. Using fallback regex extraction.")
        import re

        # Extract [MISSING: key] patterns from QA Report issues (dynamic - works for any field)
        report = state.get("current_qa_report")
        if report:
            for issue in report.issues:
                if issue.severity == "Critical":
                    matches = re.findall(r'\[MISSING:\s*([^\]]+)\]', issue.description)
                    missing_keys.extend(matches)

        # Extract [MISSING: key] from draft content (primary fallback source)
        draft = state.get("current_draft")
        if draft:
            matches = re.findall(r'\[MISSING:\s*([^\]]+)\]', draft.content)
            missing_keys.extend(matches)

        missing_keys = list(set(missing_keys))  # Dedupe

    if not missing_keys:
        print("  No missing keys found (neither explicit nor heuristic). Passing to Human Review.")
        return {"resolution_result": None}

    # Call Context Manager
    result = await context_manager.resolve_missing_info(missing_keys, state)
    
    # Construct targeted human feedback if needed
    message = ""
    if result.resolved_facts:
        resolved_list = "\n".join([f"- {r.key}: {r.value} (Confidence: {r.confidence})" for r in result.resolved_facts])
        message += f"✅ I successfully deduced the following:\n{resolved_list}\n\n"
    
    if result.human_input_needed:
        message += f"🛑 I still need you to provide the following details:\n"
        message += "\n".join([f"- {k}" for k in result.human_input_needed])
        message += "\n\nPlease provide these values."
    
    # Store partial result in state so we can merge later
    # CRITICAL FIX: Explicitly return updated fact registry from resolved facts
    # This ensures state persistence even if in-place modification failed
    updated_registry = state.get("fact_registry", {}).copy()
    if result.resolved_facts:
        for res in result.resolved_facts:
            # Re-create entry to ensure it's in the dict
            # We must import FactEntry here to ensure availability if context_manager failed
            from app.agents.workflows.drafting.schema import FactEntry
            
            updated_registry[res.key] = FactEntry(
                key=res.key,
                value=res.value,
                source_document=f"AI_Inference ({res.confidence})",
                confidence=res.confidence,
                used_in_sections=[],
                # is_verified=False, # Removed invalid field
            )

    return {
        "resolution_result": result,
        "fact_registry": updated_registry, 
        "human_readable_feedback": message if message else None, 
        "workflow_logs": state.get("workflow_logs", []) + [{
            "agent": "SmartResolution",
            "message": f"Resolved {len(result.resolved_facts)}/{len(missing_keys)} facts. Human needed for: {len(result.human_input_needed)}",
            "timestamp": "now"
        }]
    }




# --- Conditionals ---

async def prepare_redraft(state: DraftState):
    """
    Increment redraft counter before sending section back to Writer.
    This node is called when Reviewer FAILS a draft and we allow a redraft.
    """
    section_redraft_count = state.get("section_redraft_count", 0)
    section_redraft_count += 1
    print(f"  → Preparing redraft attempt (count now: {section_redraft_count})")
    return {
        "section_redraft_count": section_redraft_count
    }



def route_after_human(state: DraftState):
    """
    Decide where to go after Human Review.
    """
    verdict = state.get("human_verdict")
    # ... logic ...
    return AgentNode.ASSEMBLER 

# ... (keeping simplified routing) ...

def route_after_section_human_review(state: DraftState):
    """
    Route based on human verdict for a section loop.
    """
    verdict = state.get("human_verdict")
    print(f"--- [HumanReview] Verdict received: {verdict} ---")
    
    if verdict == "approve":
        # Force approval: Move to increment section
        return "increment_section"
    
    # refine or reject: Back to Writer via prepare_redraft to increment counter
    return "prepare_redraft"

async def increment_section(state: DraftState):
    """
    After section approval, store it in section memory and move to next section.
    Also increments iteration count for loop prevention.
    """
    current_draft = state.get("current_draft")
    iteration_count = state.get("iteration_count", 0)

    # Increment iteration count
    iteration_count += 1

    # Check total iterations limit
    can_continue, error = loop_preventor.check_total_iterations(iteration_count)
    if not can_continue:
        print(f"  [LoopPrevention] {error}")
        return {
            "error": error,
            "iteration_count": iteration_count
        }

    # Store the approved section
    if current_draft:
        print(f"--- [SectionComplete] Storing section {state.get('current_section_idx', 0) + 1} in memory ---")

        # CRITICAL FIX: Use the returned state updates from store_drafted_section
        storage_updates = await context_manager.store_drafted_section(state, current_draft)

        # Merge the updates with our own updates
        return {
            "current_section_idx": state.get("current_section_idx", 0) + 1,
            "current_draft": None,
            "current_qa_report": None,
            "section_memory": storage_updates.get("section_memory"),  # Use updated memory
            "fact_registry": storage_updates.get("fact_registry"),     # Use updated registry
            "completed_section_ids": state.get("completed_section_ids", []) + [current_draft.section_id],
            "iteration_count": iteration_count,
            "section_redraft_count": 0  # Reset counter for next section
        }

    return {
        "current_section_idx": state.get("current_section_idx", 0) + 1,
        "current_draft": None,
        "current_qa_report": None,
        "iteration_count": iteration_count,
        "section_redraft_count": 0  # Reset counter for next section
    }



async def human_review_section_node(state: DraftState):
    """
    Human review checkpoint for a specific section.
    Used when section needs human input (missing data) or stuck in loops.

    Workflow will pause here (interrupt_before) waiting for human input.
    Counter is NOT reset - after human provides guidance, if section still fails,
    it will immediately return to human review (preventing automated loops).
    """
    print("--- [HumanReview] Waiting for human input on current section ---")
    print("    Workflow paused. Waiting for human feedback via API...")
    # Don't reset counter - this ensures if Writer fails again after human input,
    # it goes back to human review immediately rather than allowing more automated redrafts
    return {}



# --- Graph Contruction ---

from app.agents.workflows.drafting.context_manager import context_init_node, feedback_processing_node

workflow = StateGraph(DraftState)

# 1. Add Nodes
workflow.add_node("load_data", load_data_node)
workflow.add_node(AgentNode.PLANNER, planning_node)
workflow.add_node(AgentNode.CONTEXT, context_init_node)
workflow.add_node(AgentNode.WRITER, writer_node)
workflow.add_node(AgentNode.REVIEWER, reviewer_node)
workflow.add_node("prepare_redraft", prepare_redraft)  # Increment counter before redraft
workflow.add_node("increment_section", increment_section)
workflow.add_node("human_review_section", human_review_section_node)  # Section-level human review
workflow.add_node("feedback_processor", feedback_processing_node)
workflow.add_node("smart_resolution", smart_resolution_node) # NEW: Smart Resolution Engine
workflow.add_node(AgentNode.REFINER, refiner_node)  # Final document refiner
workflow.add_node(AgentNode.ASSEMBLER, assembler_node)

# Final human review node
def human_review_final(state: DraftState):
    print("--- [HumanReview] Final document review ---")
    pass  # Wait for input
workflow.add_node(AgentNode.HUMAN, human_review_final)


# 2. Add Edges - Simplified workflow

# Initial setup
workflow.set_entry_point("load_data")
workflow.add_edge("load_data", AgentNode.PLANNER)
workflow.add_edge(AgentNode.PLANNER, AgentNode.CONTEXT)
workflow.add_edge(AgentNode.CONTEXT, AgentNode.WRITER)

# Section drafting loop
workflow.add_edge(AgentNode.WRITER, AgentNode.REVIEWER)

# After review: FAIL → prepare_redraft → Writer, PASS → increment_section, stuck → human_review_section
# After review: FAIL → prepare_redraft → Writer, PASS → increment_section, stuck → human_review_section
workflow.add_conditional_edges(
    AgentNode.REVIEWER,
    router.route_after_review,
    {
        "prepare_redraft": "prepare_redraft",  # Increment counter and redraft if FAIL
        "increment_section": "increment_section",  # Store and continue if PASS
        "human_review_section": "human_review_section",  # Manual routing fallback
        "smart_resolution": "smart_resolution" # NEW: Try AI resolution first
    }
)

# Smart Resolution Routing
workflow.add_conditional_edges(
    "smart_resolution",
    router.route_resolution,
    {
        "prepare_redraft": "prepare_redraft", # Resolved! Go back to Writer (via prep) to fill gaps
        "human_review_section": "human_review_section" # Failed! Ask Human
    }
)

# After prepare_redraft, go to Writer
workflow.add_edge("prepare_redraft", AgentNode.WRITER)

# After section human review, Process Feedback first
workflow.add_edge("human_review_section", "feedback_processor")

# After feedback processing, route based on verdict
workflow.add_conditional_edges(
    "feedback_processor",
    router.route_after_section_human_review,
    {
        "increment_section": "increment_section", # Approved -> Done
        "prepare_redraft": "prepare_redraft"      # Reject/Refine -> Increment Count & Rewrite
    }
)

# After increment: more sections? → Writer, all done? → Final Refiner
workflow.add_conditional_edges(
    "increment_section",
    router.route_after_increment,
    {
        AgentNode.WRITER: AgentNode.WRITER,  # More sections
        AgentNode.REFINER: AgentNode.REFINER  # All sections done → Final refiner
    }
)

# After final refiner: Assembler → Final human review
workflow.add_edge(AgentNode.REFINER, AgentNode.ASSEMBLER)
workflow.add_edge(AgentNode.ASSEMBLER, AgentNode.HUMAN)
workflow.add_edge(AgentNode.HUMAN, END)

# 3. Checkpointer
checkpointer = MemorySaver()

# 4. Compile
app = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=[
        "human_review_section",  # Pause before section-level human review
        AgentNode.HUMAN  # Pause before final human review
    ]
)
