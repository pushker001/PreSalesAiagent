from datetime import datetime

from pydantic import BaseModel, ConfigDict

from models.enums import RecommendedAction


class QualificationCreate(BaseModel):
    lead_id: str
    report_id: str | None = None
    fit_score: int
    urgency_score: int
    readiness_score: int
    overall_score: int
    recommended_action: RecommendedAction
    reasoning: str | None = None


class QualificationResponse(QualificationCreate):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
