from db.session import SessionLocal
from services.lead_service import get_lead_by_id
from services.qualification_service import get_latest_qualification_by_lead_id
from services.reports_service import get_reports_by_lead_id
from services.lead_activity_service import get_lead_activities, create_lead_activity
from models.enums import AgentName, AgentActionType, AgentActionPriority
from services.agent_action_service import create_agent_action, find_open_agent_action
from datetime import datetime, timedelta, timezone

def load_context(state):
    """Fetches broad lead context (placeholder for future expansion)."""
    return state

def evaluate_trigger(state):
    """
    Placeholder: The actual routing logic (deciding which agent to run) 
    will happen using LangGraph's Conditional Edges in graph.py.
    """
    return state

def run_booking_agent(state):
    """Calls your existing AI logic to generate a booking message."""
    from services.booking_service import build_booking_suggestion
    db = SessionLocal()
    try:
        lead = get_lead_by_id(db, state["lead_id"], state["org_id"])
        qualification = get_latest_qualification_by_lead_id(db, state["lead_id"])
        reports = get_reports_by_lead_id(db, state["lead_id"])
        activities = get_lead_activities(db, state["lead_id"])
        
        report_json = reports[0].full_report_json if reports else {}
        
        # Call Groq LLM
        suggestion = build_booking_suggestion(lead, qualification, report_json, activities)

        if not suggestion.get("should_push_booking"):
            return {
                "latest_action": None,
                "outcome": "booking_not_ready",
            }
        
        # Determine the action type
        action_type = AgentActionType.SEND_BOOKING_LINK

        if suggestion.get("booking_mode") == "booking_reminder":
            action_type = AgentActionType.SEND_BOOKING_REMINDER

        if suggestion.get("booking_mode") == "booking_abandonment_recovery":
            action_type = AgentActionType.SEND_RECOVERY_MESSAGE
        
        due_at = None

        if action_type == AgentActionType.SEND_BOOKING_REMINDER:
            due_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        if action_type == AgentActionType.SEND_RECOVERY_MESSAGE:
            due_at = datetime.now(timezone.utc) + timedelta(hours=48)
        

            
        # Update the State with the drafted action
        latest_action = {
            "org_id": state["org_id"],
            "lead_id": state["lead_id"],
            "agent_name": AgentName.BOOKING,
            "action_type": action_type,
            "priority": AgentActionPriority.HIGH,
            "title": suggestion.get("subject_line", "Automated Booking Link"),
            "message": suggestion.get("message", ""),
            "cta": suggestion.get("suggested_cta"),
            "metadata_json": {"source": "langgraph_workflow"},
            "due_at": due_at
        }
        
        return {"latest_action": latest_action}
    finally:
        db.close()

def run_follow_up_agent(state):
    return state # Placeholder for future

def run_conversation_agent(state):
    return state # Placeholder for future

def create_action(state):
    """Reads the 'latest_action' from the State and physically saves it to PostgreSQL."""
    action_data = state.get("latest_action")

    if action_data:
        db = SessionLocal()
        try:
            existing = find_open_agent_action(
                db,
                action_data["org_id"],
                action_data["lead_id"],
                action_data["action_type"],
            )

            if existing:
                return {
                    "latest_action": None,
                    "outcome": "duplicate_action_skipped",
                }

            created_action = create_agent_action(db, action_data)
            return {
                "latest_action": action_data,
                "outcome": "action_created",
                "created_action_id": created_action.id,
            }
        finally:
            db.close()
    return state

def wait_for_approval(state):
    """Pauses the workflow for human intervention."""
    return {"requires_approval": True}

def log_memory(state):
    """Logs the completion of the workflow to the timeline."""
    db = SessionLocal()
    try:
        create_lead_activity(db, {
            "lead_id": state["lead_id"],
            "event_type": "workflow_completed",
            "title": "Agent Workflow Completed",
            "details": f"LangGraph automatically ran the workflow for event: {state['current_event']}",
            "metadata_json": {}
        })
    finally:
        db.close()
    return state
