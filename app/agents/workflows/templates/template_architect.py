from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.workflows.templates.state import LegalWorkflowState
from app.core.config import settings
import os

# Helper to get LLM client lazily
def get_llm():
    if not settings.ANTHROPIC_API_KEY:
        print("⚠️ WARNING: ANTHROPIC_API_KEY not found. Agent will fail unless in simulation mode.")
        return None
        
    return ChatAnthropic(
        model="claude-sonnet-4-20250514", 
        temperature=0.2,
        api_key=settings.ANTHROPIC_API_KEY
    )

def load_system_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "../../prompts/system_prompts/templates/template_architect.md")
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
    
    
    from app.infrastructure.aws.s3_client import S3Client
    from app.core.config import settings
    import io
    
    # Initialize S3 Client
    import urllib.parse
    
    # Initialize S3 Client
    s3 = S3Client()
    
    MAX_TOTAL_CHARS = 100000 
    current_chars = 0
    
    samples_block = "Analyze these uploaded sample documents:\n\n"
    
    for i, raw_s3_key in enumerate(state["sample_docs"], 1):
        if not raw_s3_key:
            continue
            
        # Handle potential encoding issues
        s3_key = urllib.parse.unquote(raw_s3_key)
        print(f"  📥 Processing Sample {i}: {s3_key}")
        
        filename = s3_key.split('/')[-1].lower()
        text = ""

        try:
            # 1. Download from S3
            response = s3.client.get_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
            file_content = response['Body'].read()
            
            # 2. Extract Text based on extension OR content header
            is_pdf = filename.endswith(".pdf") or file_content.startswith(b'%PDF-')
            
            if is_pdf:
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(io.BytesIO(file_content))
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted + "\n"
                    print(f"    ✓ Extracted {len(text)} chars from PDF")
                except ImportError:
                    print("    ❌ pypdf not installed, cannot read PDF")
                    text = "[Error: pypdf not installed]"
                except Exception as e:
                    print(f"    ❌ PDF Parse Error: {e}")
                    text = f"[Error parsing PDF: {str(e)}]"
            else:
                # Assume text
                text = file_content.decode('utf-8', errors='ignore')
                print(f"    ✓ Extracted {len(text)} chars from Text file")

            if not text.strip():
                 print("    ⚠️ Warning: Extracted text is empty")
                 text = "[Empty Document]"

        except Exception as e:
            print(f"    ❌ Error reading file {s3_key}: {e}")
            text = f"[Error reading file (Key: {s3_key}): {str(e)}]"

        # 3. Append to block
        header = f"--- DOCUMENT {i}: {filename} ---\n"
        if current_chars + len(text) > MAX_TOTAL_CHARS:
            valid_len = MAX_TOTAL_CHARS - current_chars
            samples_block += f"{header}{text[:valid_len]}...[TRUNCATED]\n\n"
            print(f"    ⚠️ Truncated output (limit reached)")
            break
        
        samples_block += f"{header}{text}\n\n"
        current_chars += len(text) + len(header)
    
    print(f"  Note: Total context size: {current_chars} chars")

    messages = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ]
        }
    ]

    user_content = [
        {
            "type": "text",
            "text": samples_block,
            "cache_control": {"type": "ephemeral"}
        }
    ]

    if state.get("attorney_feedback"):
        feedback_msg = f"\n\nCRITICAL FEEDBACK FROM ATTORNEY (REVISION REQUIRED):\n{state['attorney_feedback']}\n\nPlease revise the template. \nIMPORTANT: Output the response in XML format:\n<summary>\nA brief, friendly summary of what you changed (max 2 sentences).\n</summary>\n<template>\nThe full revised template markdown content.\n</template>"
        user_content.append({
            "type": "text",
            "text": feedback_msg
        })
    
    messages.append({
        "role": "user",
        "content": user_content
    })
    
    llm = get_llm()
    if not llm:
        return {
            "template": "# ERROR: Missing API Key\n\nPlease set ANTHROPIC_API_KEY in backend .env to generate real templates.",
            "status": "awaiting_attorney_review",
            "current_step": "human_review",
            "revision_summary": "Failed: API Key missing."
        }

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
