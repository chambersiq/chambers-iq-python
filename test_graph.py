import asyncio
from app.agents.workflows.drafting.graph import app
from app.agents.workflows.drafting.state import DraftState
import uuid

async def test_graph():
    print("Initializing Graph...")
    
    initial_state = {
        "case_id": "case-123",
        "case_type": "divorce",
        "client_id": "client-abc",
        "created_at": "2023-01-01",
        "plan": None,
        "current_section_idx": 0,
        "completed_section_ids": [],
        "iteration_count": 0
    }
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print(f"Starting Workflow (Thread: {thread_id})...")
    
    # Run until first interruption (Human Review)
    async for event in app.astream(initial_state, config=config):
        for key, value in event.items():
            print(f"Finished Node: {key}")
            if key == "draft_master_planner":
                print(f"Plan Generated: {len(value['plan'].sections)} sections")

if __name__ == "__main__":
    asyncio.run(test_graph())
