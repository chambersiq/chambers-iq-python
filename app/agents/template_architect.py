from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.state import LegalWorkflowState
from app.core.config import settings
import os

# Initialize Claude
# Ensure ANTHROPIC_API_KEY is set in your environment or .env
if not settings.ANTHROPIC_API_KEY:
    print("⚠️ WARNING: ANTHROPIC_API_KEY not found in settings. Agent may fail.")
    
    
llm = ChatAnthropic(
    model="claude-sonnet-4-20250514", 
    temperature=0.2,
    api_key=settings.ANTHROPIC_API_KEY
)

def load_system_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "../../agent-prompts/system_prompts/template_architect.md")
    try:
        with open(prompt_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "You are an expert legal drafter."

def template_architect_agent(state: LegalWorkflowState):
    """Agent 1: Creates template from samples"""
    print("🔍 Template Architect analyzing samples...")
    
    # Mock Mode Check
    if state.get("is_simulation"):
        print("🤖 SIMULATION MODE: Returning mock response")
        import time
        time.sleep(2) # Simulate latency
        
        # Check if this is a revision (has feedback)
        if state.get("attorney_feedback"):
             return {
                "template": "# MOCKED REVISION\n\nThis template has been updated based on feedback.\n\n## Revisions\n- Added simulated clauses.\n- Fixed formatting.",
                "status": "awaiting_attorney_review",
                "current_step": "human_review",
                "revision_summary": f"I have revised the template to address your feedback: '{state['attorney_feedback']}'. Added simulated clauses and fixed formatting."
            }
            
        return {
            "template": "# MOCKED TEMPLATE\n\nThis is a simulated response for UI testing.\n\n## Section 1\nContent based on samples...",
            "status": "awaiting_attorney_review",
            "current_step": "human_review",
            "revision_summary": None
        }
    
    system_prompt = load_system_prompt()
    
    MAX_TOTAL_CHARS = 60000 
    current_chars = 0
    
    user_message = "Analyze these samples:\n\n"
    for i, doc in enumerate(state["sample_docs"], 1):
        if len(doc) > 20000:
            doc = doc[:20000] + "...[TRUNCATED]"
            
        if current_chars + len(doc) > MAX_TOTAL_CHARS:
            user_message += f"SAMPLE {i}:\n{doc[:MAX_TOTAL_CHARS - current_chars]}...[TRUNCATED DUE TO SIZE LIMIT]\n\n"
            break
            
        user_message += f"SAMPLE {i}:\n{doc}\n\n"
        current_chars += len(doc)
        
    if state.get("attorney_feedback"):
        user_message += f"\n\nCRITICAL FEEDBACK FROM ATTORNEY (REVISION REQUIRED):\n{state['attorney_feedback']}\n\nPlease revise the template. \nIMPORTANT: Output the response in XML format:\n<summary>\nA brief, friendly summary of what you changed (max 2 sentences).\n</summary>\n<template>\nThe full revised template markdown content.\n</template>"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]
    
    response = llm.invoke(messages)
    content = response.content
    
    # Check if we need to parse XML (only if revision was requested, or if LLM decided to use it)
    # Simple extraction logic
    final_template = content
    revision_summary = None
    
    if "<template>" in content and "</template>" in content:
        import re
        template_match = re.search(r'<template>(.*?)</template>', content, re.DOTALL)
        summary_match = re.search(r'<summary>(.*?)</summary>', content, re.DOTALL)
        
        if template_match:
            final_template = template_match.group(1).strip()
        if summary_match:
            revision_summary = summary_match.group(1).strip()
    
    return {
        "template": final_template,
        "status": "awaiting_attorney_review",
        "current_step": "human_review",
        "revision_summary": revision_summary
    }

def human_review_node(state: LegalWorkflowState):
    """Human checkpoint - workflow pauses here"""
    # This node doesn't actually do work, it just marks the state
    return {
        "status": "awaiting_attorney_review",
        "current_step": "human_review"
    }

def check_approval(state: LegalWorkflowState):
    """Routing function - decides next step based on approval"""
    if state.get("template_approved"):
        return "variable_collector"
    else:
        # Loop back for revision
        return "template_architect"

def variable_collector_agent(state: LegalWorkflowState):
    """Agent 2: Collects case variables"""
    print("📝 Collecting case variables...")
    
    # In a real app, this might use another LLM call to extract variables from the template
    # For now, we simulate extraction
    
    return {
        "case_variables": {
            "status": "Variables extracted automatically." 
        },
        "status": "variables_collected",
        "current_step": "document_drafter"
    }

def document_drafter_agent(state: LegalWorkflowState):
    """Agent 3: Generates final document"""
    print("📄 Drafting final document...")
    
    # Mocking the final drafting for this iteration
    return {
        "final_document": state["template"], # In real world, we'd fill the variables
        "status": "completed",
        "current_step": "completed"
    }

# Build the workflow graph
workflow = StateGraph(LegalWorkflowState)

workflow.add_node("template_architect", template_architect_agent)
workflow.add_node("human_review", human_review_node)
workflow.add_node("variable_collector", variable_collector_agent)
workflow.add_node("document_drafter", document_drafter_agent)

# Define the flow
workflow.set_entry_point("template_architect")
workflow.add_edge("template_architect", "human_review")

# Conditional routing after human review
workflow.add_conditional_edges(
    "human_review",
    check_approval,
    {
        "variable_collector": "variable_collector",
        "template_architect": "template_architect"     
    }
)

workflow.add_edge("variable_collector", "document_drafter")
workflow.add_edge("document_drafter", END)

# Compile with checkpointing
memory = MemorySaver()
agent_app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["human_review"]
)
