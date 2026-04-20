from models.report import Report


def create_report(db, report_data):
    report = Report(**report_data)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
