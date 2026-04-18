from datetime import datetime

from pydantic import BaseModel, ConfigDict

from models.enums import LeadStatus


class LeadBase(BaseModel):
    client_name: str
    website_url: str | None = None
    linkedin_url: str | None = None
    linkedin_summary: str | None = None
    client_type: str
    revenue_stage: str
    lead_source: str
    lead_temperature: str
    problem_mentioned: str
    coach_offer_price_range: str
    offer_type: str
    call_goal: str


class LeadCreate(LeadBase):
    pass


class LeadResponse(LeadBase):
    id: str
    status: LeadStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadStatusUpdate(BaseModel):
    status: LeadStatus
