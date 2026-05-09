from models.enums import RecommendedAction


def extract_booking_signals(lead, qualification, report, activities):
    synthesis = report.get("synthesis", {}) if report else {}
    objections = report.get("objections", []) if report else []

    lead_name = getattr(lead, "client_name", "there")
    status = str(getattr(lead, "status", "") or "")
    booking_status = getattr(lead, "booking_status", None) or ""
    coach_notes = getattr(lead, "coach_notes", "") or ""

    recommended_action = getattr(qualification, "recommended_action", None)
    overall_score = getattr(qualification, "overall_score", 0) or 0
    qualification_reasoning = getattr(qualification, "reasoning", "") or ""

    buying_signals = synthesis.get("buying_signals", [])
    pain_signals = synthesis.get("pain_signals", [])
    urgency_level = (synthesis.get("urgency_level") or "medium").lower()

    high_objection_count = sum(
        1
        for objection in objections
        if isinstance(objection, dict) and (objection.get("probability") or "").lower() == "high"
    )

    event_types = [activity.event_type for activity in activities] if activities else []

    return {
        "lead_name": lead_name,
        "status": status,
        "booking_status": booking_status,
        "coach_notes": coach_notes,
        "recommended_action": recommended_action,
        "overall_score": overall_score,
        "qualification_reasoning": qualification_reasoning,
        "buying_signals_count": len(buying_signals),
        "pain_signals_count": len(pain_signals),
        "urgency_level": urgency_level,
        "objections": objections,
        "high_objection_count": high_objection_count,
        "event_types": event_types,
        "has_call_logged": "call_logged" in event_types,
        "has_follow_up_sent": "follow_up_sent" in event_types,
        "has_follow_up_replied": "follow_up_replied" in event_types,
        "has_proposal_sent": "proposal_sent" in event_types,
        "has_booking_reminder_sent": "booking_reminder_sent" in event_types,
    }

def decide_booking_strategy(signals):
    status = signals["status"]
    booking_status = signals["booking_status"]
    recommended_action = signals["recommended_action"]
    overall_score = signals["overall_score"]

    if status == "booked" or booking_status in {"confirmed", "completed"}:
        return {
            "should_push_booking": False,
            "booking_mode": "already_booked",
            "recommended_timing": "No booking push needed",
            "suggested_cta": "Booking is already in progress or complete.",
            "reasoning": "The lead is already booked or has completed the booking process.",
        }

    if booking_status == "link_sent":
        return {
            "should_push_booking": True,
            "booking_mode": "booking_reminder",
            "recommended_timing": "Within 24 hours",
            "suggested_cta": "Use the booking link to confirm a time.",
            "reasoning": "A booking link was already sent, so the correct next step is a reminder.",
        }

    if recommended_action == RecommendedAction.BOOK_CALL and overall_score >= 70:
        return {
            "should_push_booking": True,
            "booking_mode": "direct_booking_push",
            "recommended_timing": "Immediately",
            "suggested_cta": "Book a call now to move this forward.",
            "reasoning": "The qualification engine strongly indicates this lead is ready for a booking ask.",
        }

    if signals["has_proposal_sent"] and overall_score >= 60:
        return {
            "should_push_booking": True,
            "booking_mode": "proposal_to_booking",
            "recommended_timing": "Within 1-2 days",
            "suggested_cta": "Book a short call to review the proposal and align on next steps.",
            "reasoning": "A proposal was sent and the lead remains strong enough to move toward a booking conversation.",
        }

    if signals["has_call_logged"] and status in {"qualified", "analyzed"}:
        return {
            "should_push_booking": True,
            "booking_mode": "post_call_booking_push",
            "recommended_timing": "Within 24 hours of the call",
            "suggested_cta": "Choose a time so we can continue the conversation while momentum is high.",
            "reasoning": "A call has already happened and the lead is in a qualified stage, so booking is the logical next step.",
        }

    return {
        "should_push_booking": False,
        "booking_mode": "not_ready",
        "recommended_timing": "Not yet",
        "suggested_cta": "Continue nurturing before pushing for a booking.",
        "reasoning": "The current lead state and interaction history do not yet support a strong booking push.",
    }

def build_booking_suggestion(lead, qualification, report, activities):
    signals = extract_booking_signals(lead, qualification, report, activities)
    strategy = decide_booking_strategy(signals)

    lead_name = signals["lead_name"]
    booking_mode = strategy["booking_mode"]

    subject_line = f"Quick next step, {lead_name}"
    message = (
        f"Hi {lead_name}, I wanted to check in and see whether it makes sense to move this conversation forward. "
        "If you'd like, we can identify the best next step based on where things currently stand."
    )

    if booking_mode == "already_booked":
        subject_line = f"You’re all set, {lead_name}"
        message = (
            f"Hi {lead_name}, everything looks in motion on the booking side already. "
            "If anything changes before the meeting, I’m happy to help."
        )

    elif booking_mode == "booking_reminder":
        subject_line = f"Quick reminder to book your call, {lead_name}"
        message = (
            f"Hi {lead_name}, just a quick reminder to grab a time that works for you using the booking link already shared. "
            "If it helps, we can use that session to review your goals and map the best next step together."
        )

    elif booking_mode == "direct_booking_push":
        subject_line = f"Let’s get a time locked in, {lead_name}"
        message = (
            f"Hi {lead_name}, based on everything we’ve discussed, I think the best next step is to get a call on the calendar. "
            "That way we can move from ideas into a concrete plan and make sure the next move is aligned with your priorities."
        )

    elif booking_mode == "proposal_to_booking":
        subject_line = f"Let’s review the proposal together, {lead_name}"
        message = (
            f"Hi {lead_name}, now that you’ve had a chance to review the proposal, the best next step is to book a short call "
            "so we can walk through questions, align on fit, and decide how to move forward."
        )

    elif booking_mode == "post_call_booking_push":
        subject_line = f"Let’s continue the conversation, {lead_name}"
        message = (
            f"Hi {lead_name}, I’d recommend booking the next conversation while the context is still fresh. "
            "That will give us the best chance to keep momentum and turn the discussion into a concrete action plan."
        )

    return {
        "should_push_booking": strategy["should_push_booking"],
        "booking_mode": strategy["booking_mode"],
        "recommended_timing": strategy["recommended_timing"],
        "subject_line": subject_line,
        "message": message,
        "suggested_cta": strategy["suggested_cta"],
        "reasoning": f"{strategy['reasoning']} {signals['qualification_reasoning']}".strip(),
        "context": {
            "status": signals["status"],
            "booking_status": signals["booking_status"],
            "overall_score": signals["overall_score"],
            "recommended_action": str(signals["recommended_action"]) if signals["recommended_action"] else None,
            "recent_event_types": signals["event_types"][:10],
        },
    }



