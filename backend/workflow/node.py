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

        from models.users import Organization
        org = db.query(Organization).filter(Organization.id == state["org_id"]).first()
        brand_voice = org.brand_voice if org else ""
        
        # Call Groq LLM with Brand Voice
        suggestion = build_booking_suggestion(lead, qualification, report_json, activities, brand_voice)

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
    """Calls the follow-up logic to generate a tracked follow-up action."""
    from services.follow_up_service import build_follow_up_suggestion

    db = SessionLocal()
    try:
        lead = get_lead_by_id(db, state["lead_id"], state["org_id"])
        qualification = get_latest_qualification_by_lead_id(db, state["lead_id"])
        reports = get_reports_by_lead_id(db, state["lead_id"])
        activities = get_lead_activities(db, state["lead_id"])

        if not lead or not qualification or not reports:
            return {
                "latest_action": None,
                "outcome": "follow_up_context_missing",
            }

        suggestion = build_follow_up_suggestion(
            lead,
            qualification,
            reports[0].full_report_json,
            activities,
        )

        if not suggestion.get("should_create_follow_up", True):
            return {
                "latest_action": None,
                "outcome": suggestion.get("follow_up_type", "follow_up_not_needed"),
            }

        due_at = datetime.now(timezone.utc) + timedelta(hours=48)

        if suggestion.get("follow_up_type") in {
            "post_call_follow_up",
            "objection_follow_up",
            "booking_reminder",
        }:
            due_at = datetime.now(timezone.utc) + timedelta(hours=24)

        latest_action = {
            "org_id": state["org_id"],
            "lead_id": state["lead_id"],
            "agent_name": AgentName.FOLLOW_UP,
            "action_type": AgentActionType.SEND_FOLLOW_UP,
            "priority": AgentActionPriority.MEDIUM,
            "title": suggestion.get("subject_line", "Follow-up required"),
            "message": suggestion.get("message", ""),
            "cta": None,
            "reasoning": suggestion.get("reasoning"),
            "due_at": due_at,
            "metadata_json": {
                "follow_up_type": suggestion.get("follow_up_type"),
                "recommended_timing": suggestion.get("recommended_timing"),
                "follow_up_sent_count": suggestion.get("context", {}).get("follow_up_sent_count"),
                "source": "langgraph_workflow",
            },
        }

        return {"latest_action": latest_action}
    finally:
        db.close()


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
    """Evaluates granular automation rules before pausing or sending."""
    db = SessionLocal()
    try:
        from models.users import Organization
        from services.lead_service import get_lead_by_id
        from services.email_service import send_action_email
        from services.agent_action_service import approve_agent_action, mark_agent_action_sent, fail_agent_action
        from services.lead_activity_service import create_lead_activity
        from models.agent_action import AgentAction
        from datetime import datetime, timezone
        from sqlalchemy import func

        org = db.query(Organization).filter(Organization.id == state["org_id"]).first()
        sender_settings = org.sender_settings or {}
        
        # 1. Load the new Rules Engine settings
        execution_mode = sender_settings.get("execution_mode", "rules_based")
        
        default_rules = {
            "SEND_BOOKING_LINK": "low_risk_auto",
            "SEND_BOOKING_REMINDER": "low_risk_auto",
            "SEND_FOLLOW_UP": "approval_required",
            "SEND_RECOVERY_MESSAGE": "approval_required",
        }
        action_rules = sender_settings.get("action_rules", default_rules)
        send_limits = sender_settings.get("send_limits", {"max_per_lead_per_day": 2})

        action_data = state.get("latest_action")
        action_id = state.get("created_action_id")
        
        # Bail out early if it's strictly manual
        if not action_id or execution_mode == "manual":
            return {"requires_approval": True}

        # 2. Risk Level Evaluation
        if execution_mode == "automatic":
            risk_level = "low_risk_auto"
        else:
            risk_level = action_rules.get(action_data["action_type"], "approval_required")

        if risk_level in ["never_auto", "approval_required"]:
            create_lead_activity(db, {
                "lead_id": state["lead_id"],
                "event_type": "automation_escalated",
                "title": "Action Escalated to Inbox",
                "details": f"Action '{action_data['action_type']}' requires human approval (Rule: {risk_level}).",
                "metadata_json": {}
            })
            return {"requires_approval": True}

        # 3. Limit Check (if low_risk_auto)
        if risk_level == "low_risk_auto":
            today = datetime.now(timezone.utc).date()
            
            # Count actions sent today to this lead
            sent_count = db.query(func.count(AgentAction.id)).filter(
                AgentAction.lead_id == state["lead_id"],
                AgentAction.status == "SENT",
                func.date(AgentAction.completed_at) == today
            ).scalar()

            if sent_count >= send_limits.get("max_per_lead_per_day", 2):
                create_lead_activity(db, {
                    "lead_id": state["lead_id"],
                    "event_type": "automation_limit_reached",
                    "title": "Daily Send Limit Reached",
                    "details": f"Lead has already received {sent_count} automated emails today. Escalating to inbox for safety.",
                    "metadata_json": {}
                })
                return {"requires_approval": True}

            # 4. Future Date Safety Check
            due_at = action_data.get("due_at")
            if due_at and due_at > datetime.now(timezone.utc):
                create_lead_activity(db, {
                    "lead_id": state["lead_id"],
                    "event_type": "automation_delayed",
                    "title": "Action Scheduled for Future",
                    "details": f"Action was drafted but is scheduled for the future. Waiting for delayed worker.",
                    "metadata_json": {}
                })
                return {"requires_approval": True}

            # 5. Final Execution (Passed all safety checks!)
            approve_agent_action(db, action_id, state["org_id"], "system_auto_rules")
            lead = get_lead_by_id(db, state["lead_id"], state["org_id"])
            from_email = sender_settings.get("from_email", "ai-agent@yourcompany.com")
            
            success = send_action_email(
                to_email=lead.email,
                subject=action_data["title"],
                body=action_data["message"],
                from_email=from_email,
                lead_id=lead.id
            )
            
            if success:
                mark_agent_action_sent(db, action_id, state["org_id"])
                create_lead_activity(db, {
                    "lead_id": state["lead_id"],
                    "event_type": "automation_executed",
                    "title": "Action Automatically Sent",
                    "details": f"'{action_data['action_type']}' was sent safely under the {risk_level} rule.",
                    "metadata_json": {}
                })
            else:
                fail_agent_action(db, action_id, state["org_id"])

            return {"requires_approval": False}

        return {"requires_approval": True}
    finally:
        db.close()

def log_memory(state):
    """Logs the completion of the workflow to the timeline."""
    db = SessionLocal()
    try:
        from services.lead_activity_service import create_lead_activity
        create_lead_activity(db, {
            "lead_id": state["lead_id"],
            "event_type": "workflow_completed",
            "title": "Agent Workflow Completed",
            "details": f"LangGraph automatically ran the workflow for event: {state.get('current_event', 'unknown')}",
            "metadata_json": {}
        })
    finally:
        db.close()
    return state