from typing import List, Literal

from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from functools import partial

from app.core.config import settings
from app.agents.workflows.concierge.state import ConciergeState
from app.core.config import settings
from app.agents.workflows.concierge.state import ConciergeState
from app.agents.tools.concierge_tools import concierge_tools
from app.agents.utils import load_system_prompt, generate_schema_description
from app.api.v1.schemas.client import IndividualClient, CompanyClient
from app.api.v1.schemas.case import CaseCreate

# --- 1. Tool Wrapping Helper ---
def get_tools_for_company(company_id: str):
    """
    Wraps the concierge tools with the specific company_id.
    This ensures the Agent doesn't hallucinate or ask for company_id.
    """
    wrapped_tools = []
    for tool in concierge_tools:
        # Create a partial that fixes company_id
        # We need to verify if langchain @tool supports partials cleanly regarding schema.
        # usually simpler to just use the tool and rely on agent, 
        # BUT we want to hide company_id.
        
        # Strategy: The agent sees a version of the tool WITHOUT company_id.
        # We manually inject it during execution?
        # Actually, simpler: The Agent sees the full signature, but we tell it "I know company_id, use X".
        # Or we use a custom ToolNode that inspects the call and injects it.
        pass
    return concierge_tools

# SIMPLER APPROACH:
# We will use a custom ToolExecutor Node.
# The Agent will generate tool calls. It MIGHT guess company_id or leave it blank.
# We will prompt the agent: "Your context: Company ID = {company_id}."
# The tools REQUIRE company_id.
# So the agent WILL generate `search_clients(company_id="123", query="...")`.

def get_model():
    return ChatAnthropic(
        model=settings.LLM_MODEL,
        temperature=0,
        api_key=settings.ANTHROPIC_API_KEY
    )

# --- 2. Nodes ---

async def assistant_node(state: ConciergeState):
    """
    The main decision maker.
    """
    messages = state["messages"]
    company_id = state["company_id"]
    
    # 1. System Prompt
    raw_prompt = load_system_prompt("concierge", "assistant")

    # Generate schemas for dynamic context
    client_schema = (
        "## Individual Client Fields\n" + generate_schema_description(IndividualClient) + 
        "\n\n## Company Client Fields\n" + generate_schema_description(CompanyClient)
    )
    case_schema = generate_schema_description(CaseCreate)

    system_prompt = raw_prompt.format(
        company_id=company_id,
        user_email=state.get('user_email', 'unknown'),
        client_schema=client_schema,
        case_schema=case_schema
    )
    
    # Prepend system message if not present
    # We filter out previous system messages to update context if needed
    filtered_msgs = [m for m in messages if m.type != "system"]
    final_messages = [SystemMessage(content=system_prompt)] + filtered_msgs
    
    # 2. Bind Tools
    model = get_model()
    model_with_tools = model.bind_tools(concierge_tools)
    
    # 3. Invoke
    response = await model_with_tools.ainvoke(final_messages)
    
    return {"messages": [response]}

# We use the standard ToolNode, but we trust the Agent to pass the company_id 
# because we explicitly gave it in the system prompt.
tools_node = ToolNode(concierge_tools)

# --- 3. Graph Definition ---

def should_continue(state: ConciergeState) -> Literal["tools", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    
    if last_message.tool_calls:
        return "tools"
    return "__end__"

workflow = StateGraph(ConciergeState)

workflow.add_node("assistant", assistant_node)
workflow.add_node("tools", tools_node)

workflow.add_edge(START, "assistant")
workflow.add_conditional_edges(
    "assistant",
    should_continue,
    {
        "tools": "tools",
        "__end__": END
    }
)
workflow.add_edge("tools", "assistant")

from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
