from models.qualification import Qualification
from models.enums import RecommendedAction


def _clamp_score(value: int) -> int:
    return max(0, min(100, value))


def _infer_recommended_action(overall_score: int) -> RecommendedAction:
    if overall_score >= 75:
        return RecommendedAction.BOOK_CALL
    if overall_score >= 55:
        return RecommendedAction.FOLLOW_UP
    if overall_score >= 35:
        return RecommendedAction.NURTURE
    return RecommendedAction.DISQUALIFY


def build_qualification_data(report, lead, saved_report):
    synthesis = report.get("synthesis", {})
    psychology = report.get("psychology", {})
    objections = report.get("objections", [])
    lead_info = report.get("lead_info", {})

    buying_signals = synthesis.get("buying_signals", [])
    pain_signals = synthesis.get("pain_signals", [])
    urgency_level = (synthesis.get("urgency_level") or "medium").lower()
    trust_level = (psychology.get("trust_level") or "").lower()
    lead_temperature = (lead_info.get("lead_temperature") or "").lower()
    revenue_stage = (lead_info.get("revenue_stage") or "").lower()
    client_type = (lead_info.get("client_type") or "").lower()
    problem_mentioned = lead_info.get("problem_mentioned") or ""
    intelligence_score = report.get("intelligence_score", 0)

    high_probability_objections = [
        objection
        for objection in objections
        if (objection.get("probability") or "").lower() == "high"
    ]

    fit_score = 0
    if intelligence_score >= 70:
        fit_score += 25
    if len(buying_signals) >= 2:
        fit_score += 20
    if problem_mentioned.strip():
        fit_score += 15
    if revenue_stage and "idea" not in revenue_stage:
        fit_score += 15
    if client_type in {"solo founder", "agency owner", "startup founder", "enterprise executive"}:
        fit_score += 15
    if pain_signals:
        fit_score += 10
    fit_score = _clamp_score(fit_score)

    urgency_score = {"high": 70, "medium": 45, "low": 20}.get(urgency_level, 45)
    if len(pain_signals) >= 3:
        urgency_score += 10
    if lead_temperature == "hot":
        urgency_score += 10
    elif lead_temperature == "warm":
        urgency_score += 5
    urgency_score = _clamp_score(urgency_score)

    readiness_score = {"hot": 60, "warm": 40, "cold": 20}.get(lead_temperature, 20)
    if "high" in trust_level or "strong" in trust_level:
        readiness_score += 15
    elif "medium" in trust_level or "moderate" in trust_level:
        readiness_score += 8
    if len(buying_signals) >= 2:
        readiness_score += 10
    if len(objections) >= 3:
        readiness_score -= 10
    if len(high_probability_objections) >= 2:
        readiness_score -= 15
    readiness_score = _clamp_score(readiness_score)

    overall_score = int(fit_score * 0.4 + urgency_score * 0.3 + readiness_score * 0.3)
    recommended_action = _infer_recommended_action(overall_score)

    reasoning_parts = [
        f"{len(buying_signals)} buying signal(s) detected",
        f"{len(pain_signals)} pain signal(s) detected",
        f"urgency assessed as {urgency_level}",
        f"lead temperature is {lead_temperature or 'unknown'}",
        f"{len(high_probability_objections)} high-probability objection(s)",
    ]

    return {
        "lead_id": lead.id,
        "report_id": saved_report.id,
        "fit_score": fit_score,
        "urgency_score": urgency_score,
        "readiness_score": readiness_score,
        "overall_score": overall_score,
        "recommended_action": recommended_action,
        "reasoning": ", ".join(reasoning_parts) + ".",
    }


def create_qualification(db, qualification_data):
    qualification = Qualification(**qualification_data)
    db.add(qualification)
    db.commit()
    db.refresh(qualification)
    return qualification


def get_latest_qualification_by_lead_id(db, lead_id):
    return (
        db.query(Qualification)
        .filter(Qualification.lead_id == lead_id)
        .order_by(Qualification.created_at.desc())
        .first()
    )
