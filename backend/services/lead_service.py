from models.lead import Lead


def get_or_create_lead(db, lead_data, org_id: str):
    website = lead_data.get("website_url")
    client_name = lead_data.get("client_name")
    lead = None

    if website:
        lead = db.query(Lead).filter(Lead.website_url == website, Lead.org_id == org_id).first()

    if not lead and client_name:
        lead = db.query(Lead).filter(Lead.client_name == client_name, Lead.org_id == org_id).first()

    if lead:
        for key, value in lead_data.items():
            if value is not None:
                setattr(lead, key, value)
    else:
        lead = Lead(**lead_data, org_id=org_id)
        db.add(lead)

    db.commit()
    db.refresh(lead)
    return lead


def get_all_leads(db, org_id: str):
    return db.query(Lead).filter(Lead.org_id == org_id).order_by(Lead.created_at.desc()).all()


def get_lead_by_id(db, lead_id: str, org_id: str):
    return db.query(Lead).filter(Lead.id == lead_id, Lead.org_id == org_id).first()


def update_lead(db, lead_id: str, update_data: dict, org_id: str):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.org_id == org_id).first()
    if not lead:
        return None
    for key, value in update_data.items():
        if value is not None:
            setattr(lead, key, value)

    db.commit()
    db.refresh(lead)
    return lead
