from models.report import Report


def create_report(db, report_data):
    report = Report(**report_data)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_reports_by_lead_id(db, lead_id):
    return (
        db.query(Report)
        .filter(Report.lead_id == lead_id)
        .order_by(Report.generated_at.desc())
        .all()
    )

    
