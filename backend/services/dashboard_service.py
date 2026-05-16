from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from models.lead import Lead
from models.lead_activity import LeadActivity
from models.qualification import Qualification
from models.enums import LeadStatus, RecommendedAction

AI_EVENT_TYPES = {
    "booking_suggestion_generated",
    "follow_up_sent",
    "conversation_reply_generated",
}

CLOSED_STATUSES = {LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST}

STAGNATION_DAYS = 7


def get_pipeline_breakdown(db, org_id: str):
    rows = db.query(Lead.status, func.count(Lead.id)).filter(Lead.org_id == org_id).group_by(Lead.status).all()
    return {str(status): count for status, count in rows}


def get_qualification_to_booking_rate(db, org_id: str):
    lead_ids = [r.id for r in db.query(Lead.id).filter(Lead.org_id == org_id).all()]
    book_call_count = (
        db.query(Qualification)
        .filter(Qualification.lead_id.in_(lead_ids), Qualification.recommended_action == RecommendedAction.BOOK_CALL)
        .count()
    )
    booked_count = db.query(Lead).filter(Lead.org_id == org_id, Lead.status == LeadStatus.BOOKED).count()
    rate = round((booked_count / book_call_count) * 100) if book_call_count else 0
    return {"booked": booked_count, "book_call_qualified": book_call_count, "rate_percent": rate}


def get_stagnant_leads(db, org_id: str):
    cutoff = datetime.now(timezone.utc) - timedelta(days=STAGNATION_DAYS)
    leads = (
        db.query(Lead)
        .filter(Lead.org_id == org_id, Lead.last_activity_at < cutoff, Lead.status.notin_(CLOSED_STATUSES))
        .order_by(Lead.last_activity_at.asc())
        .all()
    )
    return [
        {
            "id": lead.id,
            "client_name": lead.client_name,
            "status": str(lead.status),
            "last_activity_at": lead.last_activity_at.isoformat() if lead.last_activity_at else None,
        }
        for lead in leads
    ]


def get_ai_actions_count(db, org_id: str):
    lead_ids = [r.id for r in db.query(Lead.id).filter(Lead.org_id == org_id).all()]
    return (
        db.query(LeadActivity)
        .filter(LeadActivity.lead_id.in_(lead_ids), LeadActivity.event_type.in_(AI_EVENT_TYPES))
        .count()
    )


def get_average_qualification_score(db, org_id: str):
    lead_ids = [r.id for r in db.query(Lead.id).filter(Lead.org_id == org_id).all()]
    result = db.query(func.avg(Qualification.overall_score)).filter(Qualification.lead_id.in_(lead_ids)).scalar()
    return round(result) if result else 0


def get_dashboard_metrics(db, org_id: str):
    return {
        "pipeline_breakdown": get_pipeline_breakdown(db, org_id),
        "qualification_to_booking": get_qualification_to_booking_rate(db, org_id),
        "stagnant_leads": get_stagnant_leads(db, org_id),
        "ai_actions_count": get_ai_actions_count(db, org_id),
        "average_qualification_score": get_average_qualification_score(db, org_id),
    }
