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