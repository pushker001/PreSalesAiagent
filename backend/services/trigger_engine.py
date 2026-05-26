import logging
from sqlalchemy.orm import Session
from models.enums import SystemEventType, AgentName, AgentActionType, AgentActionPriority
from services.agent_action_service import create_agent_action, find_open_agent_action

logger = logging.getLogger(__name__)

def evaluate_triggers(
    db: Session,
    event_type: SystemEventType,
    lead_id: str,
    org_id: str,
    metadata: dict = None
):
    if not metadata:
        metadata = {}

    # RULE 1: Qualification Rules
    if event_type == SystemEventType.QUALIFICATION_CREATED:
        score = metadata.get("score", 0)
        recommended_action = metadata.get("recommended_action")

        # 1A: If score is high -> Automatically queue a Booking Action
        if score >= 70:
            logger.info(f"Trigger Engine: High score ({score}) detected. Queueing Booking Action.")
            existing = find_open_agent_action(db, org_id, lead_id, AgentActionType.SEND_BOOKING_LINK)
            
            if not existing:
                create_agent_action(db, {
                    "org_id": org_id,
                    "lead_id": lead_id,
                    "agent_name": AgentName.BOOKING,
                    "action_type": AgentActionType.SEND_BOOKING_LINK,
                    "priority": AgentActionPriority.HIGH,
                    "title": "Proactive Booking Suggestion Required",
                    "message": "Trigger Engine queued this action because the lead scored >= 70. Click generate to write the message.",
                    "metadata_json": {"source": "trigger_engine"}
                })
                
        # 1B: If score is lower but follow-up recommended -> Queue Follow-up Action
        elif recommended_action == "follow_up":
            logger.info("Trigger Engine: Follow-up recommended. Queueing Follow-up Action.")
            existing = find_open_agent_action(db, org_id, lead_id, AgentActionType.SEND_FOLLOW_UP)
            
            if not existing:
                create_agent_action(db, {
                    "org_id": org_id,
                    "lead_id": lead_id,
                    "agent_name": AgentName.FOLLOW_UP,
                    "action_type": AgentActionType.SEND_FOLLOW_UP,
                    "priority": AgentActionPriority.MEDIUM,
                    "title": "Proactive Follow-Up Required",
                    "message": "Trigger Engine queued this action based on qualification results.",
                    "metadata_json": {"source": "trigger_engine"}
                })

    # RULE 2: If a booking link was just sent -> Queue a Reminder Action
    elif event_type == SystemEventType.BOOKING_LINK_SENT:
        logger.info("Trigger Engine: Booking link sent. Queueing Reminder Action.")
        existing = find_open_agent_action(db, org_id, lead_id, AgentActionType.SEND_BOOKING_REMINDER)
        
        if not existing:
             create_agent_action(db, {
                 "org_id": org_id,
                 "lead_id": lead_id,
                 "agent_name": AgentName.BOOKING,
                 "action_type": AgentActionType.SEND_BOOKING_REMINDER,
                 "priority": AgentActionPriority.MEDIUM,
                 "title": "Follow up on Booking Link",
                 "message": "The booking link was sent. Remind them to book if they haven't yet.",
                 "metadata_json": {"source": "trigger_engine"}
             })
