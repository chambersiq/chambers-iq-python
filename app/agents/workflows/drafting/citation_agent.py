from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import ToolMessage, AIMessage, SystemMessage, HumanMessage
import json
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from app.agents.workflows.drafting.state import DraftState
from app.agents.tools.indian_kanoon_tools import citation_tools
from typing import Dict, Any
from functools import lru_cache

class DraftCitationAgent:
    def __init__(self):
        from app.agents.workflows.drafting.llm_utils import create_cached_llm
        from app.core.config import settings

        try:
             # Use shared factory
             base_llm = create_cached_llm(
                 model=settings.LLM_MODEL,
                 provider=settings.LLM_PROVIDER,
                 temperature=0
             )
             self.llm = base_llm.bind_tools(citation_tools)
        except Exception as e:
             # Fallback or error handling
             print(f"Warning: Could not init Citation Agent LLM: {e}")
             self.llm = None

    async def perform_research(self, query: str) -> str:
        """
        Executes a research loop: Query -> LLM -> Tool -> LLM.
        """
        if not self.llm:
            return "Citation Agent unavailable (LLM not initialized)."
            
        system_prompt = load_drafting_prompt("citation_agent")
        
        # Tool Map
        tool_map = {t.name: t for t in citation_tools}
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]
        
        # Max steps to prevent infinite loops
        for _ in range(5):
            response = await self.llm.ainvoke(messages)
            messages.append(response)
            
            if not response.tool_calls:
                return response.content
                
            # Execute tools
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                if tool_name in tool_map:
                    print(f"    [CitationAgent] Calling tool {tool_name} with {tool_args}")
                    try:
                        tool_result = await tool_map[tool_name].ainvoke(tool_args)
                        # Ensure result is string
                        content = str(tool_result)
                    except Exception as e:
                        content = f"Error executing tool: {str(e)}"
                else:
                    content = "Error: Tool not found"
                    
                messages.append(ToolMessage(
                    content=content,
                    tool_call_id=tool_call["id"]
                ))
        
        return "Research limit reached. Partial results: " + str(messages[-1].content)

# Helper with caching
import os
from app.agents.workflows.drafting.cache import cache_prompt

@cache_prompt
def load_drafting_prompt(filename: str) -> str:
    """Load system prompt with automatic caching."""
    path = os.path.join(os.path.dirname(__file__), f"../../prompts/system_prompts/drafting/{filename}.md")
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "You are an expert legal assistant."

# Wrapper
@lru_cache
def get_citation_agent():
    return DraftCitationAgent()

# Note: In the final graph, this might be a subgraph or a tool-calling node.
# For now, we define the class structure.
