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

# Import services
from app.services.core.case_service import CaseService
from app.services.core.document_service import DocumentService
from app.services.core.template_service import TemplateService

# Import optimization utilities
from app.agents.workflows.drafting.cache import cache_content
from app.agents.workflows.drafting.loop_prevention import LoopPreventor, check_workflow_health

# Global loop preventor instance (per workflow run)
# In production, this would be stored in state or session
loop_preventor = LoopPreventor(
    max_total_iterations=10,
    max_section_revisions=3,
    max_writer_reviewer_cycles=2
)

# --- Data Loader Node ---

@cache_content(ttl=300)  # Cache for 5 minutes
async def load_case_data(company_id: str, case_id: str):
    """Load case data with caching."""
    case_service = CaseService()
    case = case_service.get_case_by_id(company_id, case_id)
    return case.model_dump() if case else None

@cache_content(ttl=300)  # Cache for 5 minutes
async def load_template_data(company_id: str, template_id: str):
    """Load template with caching."""
    template_service = TemplateService()
    template = template_service.get_template(company_id, template_id)
    if template:
        return {
            "data": template.model_dump(),
            "content": template.content
        }
    return None

async def load_documents_lazy(company_id: str, case_id: str, limit: int = None):
    """
    Lazy load documents - only load what's needed.

    For cost optimization:
    - Only loads documents with aiStatus='completed'
    - Can limit number of documents loaded
    - Sorts by importance (newest first)
    """
    document_service = DocumentService()
    documents = document_service.get_documents(company_id, case_id)

    # Filter to only completed documents
    completed_docs = [doc for doc in documents if doc.aiStatus == "completed"]

    # Sort by creation date (newest first)
    completed_docs.sort(key=lambda x: x.createdAt, reverse=True)

    # Apply limit if specified
    if limit:
        completed_docs = completed_docs[:limit]

    return [doc.model_dump() for doc in completed_docs]

async def load_data_node(state: DraftState):
    """
    Load case data, documents, and template before planning starts.
    Uses caching and lazy loading for cost optimization.
    """
    print("--- [DataLoader] Loading case data and documents ---")

    case_id = state.get("case_id")
    company_id = state.get("company_id")
    template_id = state.get("template_id")

    # Validate inputs
    if not case_id or not company_id:
        print(f"  [Error] Missing required keys: case_id={case_id}, company_id={company_id}")
        return {"error": "Missing case_id or company_id in state"}
    case_data = await load_case_data(company_id, case_id)
    if not case_data:
        return {"error": f"Case {case_id} not found"}

    print(f"  Loaded case: {case_data.get('caseName', 'Unknown')}")

    # Lazy load only completed documents (optimized for cost)
    # Limit to 10 most recent documents to reduce processing
    documents_data = await load_documents_lazy(company_id, case_id, limit=10)
    print(f"  Loaded {len(documents_data)} documents (completed only)")

    # Load template (cached)
    template_content = ""
    template_data = None
    if template_id:
        template_result = await load_template_data(company_id, template_id)
        if template_result:
            template_data = template_result["data"]
            template_content = template_result["content"]
            print(f"  Loaded template: {template_data.get('name', 'Unknown')}")
        else:
            print(f"  Warning: Template {template_id} not found")
    else:
        print("  No template_id provided, will use fallback plan")

    return {
        "case_data": case_data,
        "documents": documents_data,
        "template_content": template_content,
        "template_data": template_data,
        "case_type": case_data.get("caseType", "unknown")
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

def route_after_review(state: DraftState):
    """
    Simplified routing after QA Review with strict loop limit.

    - FAIL on first attempt: One redraft allowed (route to prepare_redraft → Writer)
    - FAIL on second attempt: Force human review (fundamental issues)
    - PASS/WARNINGS: Store section and continue

    Max loops: 1 (configurable via MAX_SECTION_REDRAFTS)
    """
    MAX_SECTION_REDRAFTS = 2  # Reduced to 2 per user request

    report = state.get("current_qa_report")
    current_section = state.get("current_section")

    # Get current section's redraft count
    section_redraft_count = state.get("section_redraft_count", 0)
    
    # Check for missing info using REPORT and DRAFT content (Native logic)
    missing_info_detected = False
    
    # 1. Check draft content for explicit markers (Ground truth)
    if current_section and state.get("current_draft"):
        content = state["current_draft"].content
        if "[MISSING:" in content:
            missing_info_detected = True
            print("  ⚠️  Draft contains [MISSING: ...] markers -> Human input required")

    # 2. Check Critical Issues in Report
    if not missing_info_detected and report:
        for issue in report.issues:
            if issue.severity == "Critical":
                desc = issue.description.lower()
                if "missing" in desc or "provide" in desc or "not provided" in desc:
                    missing_info_detected = True
                    print(f"  ⚠️  Critical issue indicates missing info: '{issue.description}' -> Human input required")
                    break

    if report and report.status == QAStatus.FAIL:
        # PRIORITY 1: If data is missing, Writer cannot fix it alone. Ask Human immediately.
        if missing_info_detected:
             print(f"  ⚠️  Missing information detected. Routing to Human Review immediately.")
             return "human_review_section"

        # PRIORITY 2: Check retry limits for quality/style issues
        if section_redraft_count > MAX_SECTION_REDRAFTS:
            # We already asked human (at count=MAX), and they refined, but it FAILED again.
            # Stop the loop. Force finish.
            print(f"  ⚠️  Max iterations exceeded ({section_redraft_count} > {MAX_SECTION_REDRAFTS}). Forcing progress.")
            print(f"  → Routing to increment_section (Accepting draft as-is)")
            return "increment_section"
        
        elif section_redraft_count == MAX_SECTION_REDRAFTS:
             # Hit the autonomous limit. Ask Human for help ONE time.
             print(f"  ⚠️  Autonomous limit reached ({section_redraft_count}). Requesting Human intervention.")
             return "human_review_section"

        else:
            # Still in autonomous zone
            print(f"  → Routing to prepare_redraft (current count: {section_redraft_count}, max: {MAX_SECTION_REDRAFTS})")
            return "prepare_redraft"

    # Section approved
    print(f"  → Section approved, moving to next")
    return "increment_section"

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
        await context_manager.store_drafted_section(state, current_draft)
        # The store_drafted_section updates section_memory and fact_registry
        # We need to return those updates
        section_memory = state.get("section_memory", [])
        section_memory.append(current_draft)

        return {
            "current_section_idx": state.get("current_section_idx", 0) + 1,
            "current_draft": None,
            "current_qa_report": None,
            "section_memory": section_memory,
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

def route_after_increment(state: DraftState):
    """
    After storing a section, check if more sections remain or if all done.
    """
    plan = state.get("plan")
    current_idx = state.get("current_section_idx", 0)

    if not plan:
        return AgentNode.HUMAN  # Error case

    total_sections = len(plan.sections)

    if current_idx >= total_sections:
        # All sections completed! Go to final refiner
        print(f"--- [WorkflowComplete] All {total_sections} sections drafted! Moving to final refiner ---")
        return AgentNode.REFINER
    else:
        # More sections to draft
        print(f"--- [NextSection] Moving to section {current_idx + 1}/{total_sections} ---")
        return AgentNode.WRITER

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

def route_after_section_human_review(state: DraftState):
    """
    Route based on human verdict for a section loop.
    """
    verdict = state.get("human_verdict")
    print(f"--- [HumanReview] Verdict received: {verdict} ---")
    
    if verdict == "approve":
        # Force approval: Move to increment section
        return "increment_section"
    
    # refine or reject: Back to Writer to fix
    # refine or reject: Back to Writer to fix via redraft loop logic
    return "prepare_redraft"

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
workflow.add_node("feedback_processor", feedback_processing_node) # REPLACED: Context Manager now handles feedback
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
workflow.add_conditional_edges(
    AgentNode.REVIEWER,
    route_after_review,
    {
        "prepare_redraft": "prepare_redraft",  # Increment counter and redraft if FAIL
        "increment_section": "increment_section",  # Store and continue if PASS
        "human_review_section": "human_review_section"  # Human input needed
    }
)

# After prepare_redraft, go to Writer
workflow.add_edge("prepare_redraft", AgentNode.WRITER)

# After section human review, Process Feedback first
workflow.add_edge("human_review_section", "feedback_processor")

# After feedback processing, route based on verdict
workflow.add_conditional_edges(
    "feedback_processor",
    route_after_section_human_review,
    {
        "increment_section": "increment_section", # Approved -> Done
        "prepare_redraft": "prepare_redraft"      # Reject/Refine -> Increment Count & Rewrite
    }
)

# After increment: more sections? → Writer, all done? → Final Refiner
workflow.add_conditional_edges(
    "increment_section",
    route_after_increment,
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
