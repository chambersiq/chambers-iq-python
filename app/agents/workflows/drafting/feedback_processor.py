from app.agents.workflows.drafting.state import DraftState
from app.agents.workflows.drafting.schema import FactEntry
from app.agents.workflows.drafting.llm_utils import create_cached_llm
from langchain_core.messages import SystemMessage, HumanMessage
import json
import re

class FeedbackProcessor:
    def __init__(self):
        from app.core.config import settings
        self.llm = create_cached_llm(
            model=settings.LLM_MODEL,
            provider=settings.LLM_PROVIDER
        )

    async def process_feedback(self, state: DraftState) -> dict:
        """
        Agent Node: Process human feedback to extract and persist facts.
        """
        print("--- [FeedbackProcessor] Processing Human Feedback ---")
        
        feedback = state.get("human_feedback")
        fact_registry = state.get("fact_registry", {})
        
        if not feedback:
            print("  No feedback to process")
            return {}

        # Use LLM to extract facts
        print(f"  Extracting facts from: '{feedback[:50]}...'")
        
        system_prompt = """You are a Legal Fact Extractor.
Your goal is to extract structured facts from human feedback and update the Fact Registry.

Input:
1. Current Fact Registry (JSON)
2. Human Feedback (Text)

Output:
JSON dict of NEW or UPDATED facts (key-value pairs).
Ignore feedback that is purely instructional (e.g., "rewrite this", "make it shorter") unless it contains factual data.

Format:
{
  "court_name": "Delhi High Court",
  "marriage_date": "2015-03-10"
}

If no facts are present, return {}.
"""
        
        def get_fact_value(v):
            if isinstance(v, dict):
                return v.get('value', 'unknown')
            if hasattr(v, 'value'):
                return v.value
            return str(v)

        existing_facts_summary = {k: get_fact_value(v) for k, v in list(fact_registry.items())[:20]}
        
        user_msg = f"""Current Registry Sample:
{json.dumps(existing_facts_summary, indent=2)}

Human Feedback:
"{feedback}"

Extract facts:"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_msg)
            ])
            
            content = response.content
            # Extract JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                new_facts = json.loads(json_match.group())
                
                if new_facts:
                    print(f"  ✓ Extracted {len(new_facts)} new facts: {list(new_facts.keys())}")
                    
                    # Update registry
                    for k, v in new_facts.items():
                        fact_registry[k] = FactEntry(
                            key=k,
                            value=v,
                            source="human_feedback",
                            confidence=1.0,
                            is_verified=True
                        )
                    
                    return {
                        "fact_registry": fact_registry,
                        "workflow_logs": state.get("workflow_logs", []) + [{
                            "agent": "FeedbackProcessor",
                            "message": f"Extracted facts from feedback: {', '.join(new_facts.keys())}",
                            "timestamp": "now"
                        }]
                    }
                else:
                    print("  No new facts found in feedback")
                    # Still return logs
                    return {
                         "workflow_logs": state.get("workflow_logs", []) + [{
                            "agent": "FeedbackProcessor",
                            "message": "Processed guidance (no new facts extracted)",
                            "timestamp": "now"
                        }]
                    }
            
        except Exception as e:
            print(f"  ⚠️ Extraction failed: {e}")

        return {}

feedback_processor = FeedbackProcessor()

async def feedback_processor_node(state: DraftState):
    return await feedback_processor.process_feedback(state)
