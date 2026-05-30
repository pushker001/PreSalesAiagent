from typing import TypedDict, Optional
from datetime import datetime

class LeadLifecycleState(TypedDict):
    lead_id: str
    org_id: str
    current_event: str
    
    # Context pulled from DB
    lead_context: dict
    
    # Agent Output
    latest_action: Optional[dict]
    
    # Workflow control
    requires_approval: bool
    next_wait_until: Optional[datetime]
    outcome: str
    metadata: dict