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


def get_pipeline_breakdown(db):
    rows = db.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all()
    return {str(status): count for status, count in rows}


def get_qualification_to_booking_rate(db):
    book_call_count = (
        db.query(Qualification)
        .filter(Qualification.recommended_action == RecommendedAction.BOOK_CALL)
        .count()
    )
    booked_count = db.query(Lead).filter(Lead.status == LeadStatus.BOOKED).count()
    rate = round((booked_count / book_call_count) * 100) if book_call_count else 0
    return {"booked": booked_count, "book_call_qualified": book_call_count, "rate_percent": rate}


def get_stagnant_leads(db):
    cutoff = datetime.now(timezone.utc) - timedelta(days=STAGNATION_DAYS)
    leads = (
        db.query(Lead)
        .filter(Lead.last_activity_at < cutoff, Lead.status.notin_(CLOSED_STATUSES))
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


def get_ai_actions_count(db):
    return (
        db.query(LeadActivity)
        .filter(LeadActivity.event_type.in_(AI_EVENT_TYPES))
        .count()
    )


def get_average_qualification_score(db):
    result = db.query(func.avg(Qualification.overall_score)).scalar()
    return round(result) if result else 0


def get_dashboard_metrics(db):
    return {
        "pipeline_breakdown": get_pipeline_breakdown(db),
        "qualification_to_booking": get_qualification_to_booking_rate(db),
        "stagnant_leads": get_stagnant_leads(db),
        "ai_actions_count": get_ai_actions_count(db),
        "average_qualification_score": get_average_qualification_score(db),
    }
