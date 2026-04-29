from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LeadActivityBase(BaseModel):
    lead_id: str
    event_type: str
    title: str
    details: str | None = None
    metadata_json: dict | None = None


class LeadActivityCreate(LeadActivityBase):
    pass


class LeadActivityResponse(LeadActivityBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
