from models.enums import RecommendedAction


def build_follow_up_suggestion(lead, qualification, report, activities):
    synthesis = report.get("synthesis", {}) if report else {}
    objections = report.get("objections", []) if report else []
    lead_name = getattr(lead, "client_name", "there")
    booking_status = getattr(lead, "booking_status", None) or ""
    status = str(getattr(lead, "status", "") or "")
    recommended_action = getattr(qualification, "recommended_action", None)
    qualification_reasoning = getattr(qualification, "reasoning", "") or ""

    event_types = [activity.event_type for activity in activities] if activities else []
    has_call_logged = "call_logged" in event_types
    has_follow_up_sent = "follow_up_sent" in event_types
    has_proposal_sent = "proposal_sent" in event_types
    has_follow_up_reply = "follow_up_replied" in event_types
    has_high_objection = any(
        (objection.get("probability") or "").lower() == "high"
        for objection in objections
        if isinstance(objection, dict)
    )

    follow_up_type = "no_response_nudge"
    recommended_timing = "Within 48 hours"
    subject_line = f"Quick follow-up for {lead_name}"
    message = (
        f"Hi {lead_name}, just checking in on our last conversation. "
        "Wanted to see where things stand and whether moving forward still feels relevant for you."
    )
    reasoning = "Defaulted to a gentle re-engagement nudge because no stronger follow-up trigger was found."

    if booking_status == "link_sent":
        follow_up_type = "booking_reminder"
        recommended_timing = "Within 24 hours"
        subject_line = f"Quick reminder to book your call, {lead_name}"
        message = (
            f"Hi {lead_name}, just a quick reminder to grab a time that works for you using the booking link I sent. "
            "Happy to answer anything first if that would help."
        )
        reasoning = "Booking status is link_sent, so the best next move is a booking reminder."

    elif has_proposal_sent:
        follow_up_type = "proposal_follow_up"
        recommended_timing = "2-3 days after proposal"
        subject_line = f"Checking in on the proposal, {lead_name}"
        message = (
            f"Hi {lead_name}, wanted to follow up on the proposal I sent over. "
            "Curious what stood out, what questions came up, and whether you'd like to talk through the next step together."
        )
        reasoning = "A proposal was already sent, so the next step is a proposal follow-up."

    elif has_call_logged:
        follow_up_type = "post_call_follow_up"
        recommended_timing = "Within 24 hours of the call"
        subject_line = f"Great speaking with you, {lead_name}"
        message = (
            f"Hi {lead_name}, great speaking with you today. "
            "Based on our conversation, it sounds like improving conversion consistency is a priority. "
            "Happy to help you map the next step whenever you're ready."
        )
        reasoning = "A call was logged, so the agent generated a post-call follow-up."

    elif recommended_action == RecommendedAction.FOLLOW_UP and has_high_objection:
        follow_up_type = "objection_follow_up"
        recommended_timing = "Within 24-48 hours"
        subject_line = f"Following up on your questions, {lead_name}"
        message = (
            f"Hi {lead_name}, I wanted to follow up on the concerns we surfaced. "
            "A lot of people hesitate at this stage because they want more clarity before deciding, "
            "so if helpful I can walk you through the specific parts that matter most for your situation."
        )
        reasoning = "Qualification recommends follow-up and the report includes high-probability objections."

    elif has_follow_up_sent and not has_follow_up_reply:
        follow_up_type = "no_response_nudge"
        recommended_timing = "3-5 days after the last follow-up"
        subject_line = f"Still open to this, {lead_name}?"
        message = (
            f"Hi {lead_name}, wanted to send a quick nudge in case this slipped through. "
            "If this is still something you want to solve, I’m happy to help you think through the best next move."
        )
        reasoning = "A follow-up was already sent and no reply has been recorded, so a no-response nudge fits best."

    return {
        "follow_up_type": follow_up_type,
        "recommended_timing": recommended_timing,
        "subject_line": subject_line,
        "message": message,
        "reasoning": f"{reasoning} {qualification_reasoning}".strip(),
        "context": {
            "status": status,
            "booking_status": booking_status,
            "recommended_action": str(recommended_action) if recommended_action else None,
            "recent_event_types": event_types[:10],
        },
    }
