from models.lead import Lead


def get_or_create_lead(db, lead_data):
    website = lead_data.get("website_url")
    client_name = lead_data.get("client_name")
    lead = None

    if website:
        lead = db.query(Lead).filter(Lead.website_url == website).first()

    if not lead and client_name:
        lead = db.query(Lead).filter(Lead.client_name == client_name).first()

    if lead:
        for key, value in lead_data.items():
            if value is not None:
                setattr(lead, key, value)
    else:
        lead = Lead(**lead_data)
        db.add(lead)

    db.commit()
    db.refresh(lead)

    return lead


def get_all_leads(db):
    return db.query(Lead).order_by(Lead.created_at.desc()).all()


def get_lead_by_id(db, lead_id: str):
    return db.query(Lead).filter(Lead.id == lead_id).first()

def update_lead(db, lead_id: str, update_data: dict):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return None
    for key, value in update_data.items():
        if value is not None:
            setattr(lead, key, value)

    db.commit()
    db.refresh(lead)
    return lead