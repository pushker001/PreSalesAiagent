import os
import sys

# Add the backend directory to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import SessionLocal
from models.lead import Lead
from workflow.graph import app

def run_test():
    db = SessionLocal()
    try:
        # Grab the very first lead in your database that has an org_id assigned
        lead = db.query(Lead).filter(Lead.org_id.isnot(None)).first()
        if not lead:
            print("No leads found in the database. Please analyze a lead first.")
            return

        print(f"Testing LangGraph with Lead ID: {lead.id} (Org: {lead.org_id})")

        # 1. Create our initial state dictionary (Pretend a qualification just finished)
        initial_state = {
            "lead_id": lead.id,
            "org_id": lead.org_id,
            "current_event": "qualification_created"
        }

        print("\n--- Starting LangGraph Workflow ---")
        
        # 2. Invoke the graph! 
        # This will pass the dictionary through load_context -> evaluate -> booking -> action -> wait -> memory
        final_state = app.invoke(initial_state)

        print("\n--- Workflow Completed! ---")
        print(f"Outcome: {final_state.get('outcome')}")
        print(f"Requires Approval: {final_state.get('requires_approval')}")
        if "latest_action" in final_state and final_state["latest_action"]:
            print(f"Action Created: {final_state['latest_action']['title']}")
        
        print("\nSuccess! A new Agent Action was just created autonomously by LangGraph!")

    finally:
        db.close()

if __name__ == "__main__":
    run_test()