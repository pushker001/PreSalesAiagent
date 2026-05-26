from sqlalchemy.orm import Session
from models.enums import SystemEventType
from services.lead_activity_service import create_lead_activity
# We will create this in Step 3!
from services.trigger_engine import evaluate_triggers

def publish_event(
    db: Session,
    event_type: SystemEventType,
    lead_id: str,
    org_id: str,
    title: str,
    details: str = None,
    metadata: dict = None
):
    """
    Central event bus. Logs the activity to the database and 
    proactively triggers the AI rules engine.
    """
    
    # 1. Save to the timeline (Lead Activity)
    activity_data = {
        "lead_id": lead_id,
        "event_type": event_type.value,
        "title": title,
        "details": details,
        "metadata_json": metadata or {}
    }
    
    activity = create_lead_activity(db, activity_data)
    
    # 2. Fire the Trigger Engine to evaluate rules
    # We pass org_id down because the Agent Actions need to know which org they belong to
    evaluate_triggers(db, event_type, lead_id, org_id, metadata)
    
    return activity
