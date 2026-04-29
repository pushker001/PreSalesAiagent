from models.lead_activity import LeadActivity


def create_lead_activity(db, activity_data):
    activity = LeadActivity(**activity_data)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def get_lead_activities(db, lead_id: str):
    return (
        db.query(LeadActivity)
        .filter(LeadActivity.lead_id == lead_id)
        .order_by(LeadActivity.created_at.desc())
        .all()
    )
