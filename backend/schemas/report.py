from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportCreate(BaseModel):
    lead_id: str
    intelligence_score: int
    full_report_json: dict


class ReportResponse(ReportCreate):
    id: str
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)
