from typing import TypedDict, Optional, Literal, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from app.core.config import settings
import json
import os

# Define Agent State
class DocumentAnalysisState(TypedDict):
    document_text: str
    client_position: str # e.g., "Petitioner", "Respondent"
    category: Optional[Literal["A", "B", "C", "D"]]
    doc_type: Optional[str]
    scan_quality: Optional[str]
    specialist_analysis: Optional[str] # Output from Specialist
    final_advice: Optional[str] # Output from Strategist
    is_bundle: bool

# Initialize LLM (Lazy Load helper)
def get_llm():
    if not settings.ANTHROPIC_API_KEY:
        print("⚠️ WARNING: ANTHROPIC_API_KEY not found. Agent will fail.")
        return None
    return ChatAnthropic(
        model="claude-sonnet-4-20250514", 
        temperature=0.0, # Low temp for extraction
        api_key=settings.ANTHROPIC_API_KEY
    )

def load_prompt(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), f"../../agent-prompts/system_prompts/document_summarizer/{filename}.md")
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: Prompt {filename} not found."

# --- NODES ---

def router_node(state: DocumentAnalysisState):
    """Step 1: Classify document"""
    print("🚦 Router: Classifying document...")
    llm = get_llm()
    if not llm:
        return {"category": "D", "doc_type": "Error", "scan_quality": "Low"}
        
    prompt = load_prompt("router")
    
    # Shared Cache Strategy:
    # 1. Document Block (Cached)
    # 2. Instruction Block (Specific)
    # This allows the Specialist node to reuse the cache created here.
    
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Document Text:\n\n{state['document_text']}",
                    "cache_control": {"type": "ephemeral"}
                },
                {
                    "type": "text",
                    "text": f"\n\nINSTRUCTIONS:\n{prompt}"
                }
            ]
        }
    ]
    
    response = llm.invoke(messages)
    content = response.content
    
    # Parse JSON
    try:
        # Simple heuristic to extract JSON if wrapped in markdown code blocks
        clean_content = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_content)
        category = data.get("category", "D") # Default to D if fail
        if category not in ["A", "B", "C", "D"]:
            category = "D"
            
        return {
            "category": category,
            "doc_type": data.get("doc_type"),
            "scan_quality": data.get("scan_quality"),
            "is_bundle": str(data.get("is_bundle")).lower() == "true"
        }
    except Exception as e:
        print(f"Router Parse Error: {e}")
        return {"category": "D", "doc_type": "Unknown", "scan_quality": "Unknown"}

def specialist_node(state: DocumentAnalysisState):
    """Step 2: Deep Extraction based on category"""
    category = state.get("category", "D")
    print(f"🕵️ Specialist {category}: Analyzing...")
    
    prompt_map = {
        "A": "specialist_a",
        "B": "specialist_b",
        "C": "specialist_c",
        "D": "specialist_d"
    }
    
    prompt_file = prompt_map.get(category, "specialist_d")
    specialist_instruction = load_prompt(prompt_file)
    
    llm = get_llm()
    if not llm:
        return {"specialist_analysis": "Error: AI not available."}
        
    # Reuses the exact same Document Block structure as Router to hit Cache
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Document Text:\n\n{state['document_text']}",
                    "cache_control": {"type": "ephemeral"}
                },
                {
                    "type": "text",
                    "text": f"\n\nINSTRUCTIONS:\n{specialist_instruction}"
                }
            ]
        }
    ]
    
    response = llm.invoke(messages)
    print(f"✅ Specialist {category} Finished.")
    
    # In merged mode, the Specialist Output IS the Final Advice
    return {
        "specialist_analysis": response.content,
        "final_advice": response.content # Duplicate to satisfy schema
    }

# --- GRAPH BUILD ---

workflow = StateGraph(DocumentAnalysisState)

workflow.add_node("router", router_node)
workflow.add_node("specialist", specialist_node)

workflow.set_entry_point("router")
workflow.add_edge("router", "specialist")
workflow.add_edge("specialist", END)

doc_analysis_app = workflow.compile()
