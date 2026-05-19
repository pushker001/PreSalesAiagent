from datetime import datetime

from pydantic import BaseModel

from models.enums import AgentActionPriority, AgentActionStatus, AgentActionType, AgentName


class AgentActionCreate(BaseModel):
    lead_id: str
    org_id: str
    agent_name: AgentName
    action_type: AgentActionType
    priority: AgentActionPriority = AgentActionPriority.MEDIUM
    title: str
    message: str | None = None
    cta: str | None = None
    reasoning: str | None = None
    due_at: datetime | None = None
    metadata_json: dict | None = None


class AgentActionResponse(BaseModel):
    id: str
    org_id: str
    lead_id: str
    agent_name: AgentName
    action_type: AgentActionType
    status: AgentActionStatus
    priority: AgentActionPriority
    title: str
    message: str | None = None
    cta: str | None = None
    reasoning: str | None = None
    due_at: datetime | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    completed_at: datetime | None = None
    metadata_json: dict | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentActionStatusUpdate(BaseModel):
    metadata_json: dict | None = None
