import json
import os

from models.enums import BookingStatus, RecommendedAction
from utils.llm import call_groq

BOOKING_URL = (os.getenv("BOOKING_URL") or "").strip()


def extract_booking_signals(lead, qualification, report, activities):
    synthesis = report.get("synthesis", {}) if report else {}
    objections = report.get("objections", []) if report else []

    lead_name = getattr(lead, "client_name", "there")
    status = str(getattr(lead, "status", "") or "")
    booking_status = str(getattr(lead, "booking_status", "") or "")
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

    if status == "booked" or booking_status in {
        BookingStatus.CONFIRMED.value,
        BookingStatus.COMPLETED.value,
    }:
        return {
            "should_push_booking": False,
            "booking_mode": "already_booked",
            "recommended_timing": "No booking push needed",
            "suggested_cta": "Booking is already in progress or complete.",
            "reasoning": "The lead is already booked or has completed the booking process.",
        }

    if booking_status == BookingStatus.REMINDER_SENT.value:
        return {
            "should_push_booking": True,
            "booking_mode": "booking_abandonment_recovery",
            "recommended_timing": "Within 24-48 hours",
            "suggested_cta": "Re-open the conversation and remove friction before asking for the booking again.",
            "reasoning": "A reminder has already been sent and the lead still has not booked, so recovery is the right next move.",
        }

    if booking_status == BookingStatus.LINK_SENT.value:
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

    if (
        overall_score >= 55
        and signals["buying_signals_count"] >= 3
        and signals["pain_signals_count"] >= 2
        and signals["urgency_level"] in {"medium", "high"}
    ):
        return {
            "should_push_booking": True,
            "booking_mode": "soft_booking_push",
            "recommended_timing": "Within 24-48 hours",
            "suggested_cta": "Offer a short, low-pressure call to clarify the best next step.",
            "reasoning": "The lead shows enough buying and pain signals to justify a soft booking prompt.",
        }

    return {
        "should_push_booking": False,
        "booking_mode": "not_ready",
        "recommended_timing": "Not yet",
        "suggested_cta": "Continue nurturing before pushing for a booking.",
        "reasoning": "The current lead state and interaction history do not yet support a strong booking push.",
    }


def generate_booking_message(signals, strategy):
    objections = signals.get("objections", [])
    objections_summary = ", ".join(
        objection.get("objection", "")
        for objection in objections
        if isinstance(objection, dict) and objection.get("objection")
    ) or "No explicit objections recorded."

    booking_url = BOOKING_URL or ""

    prompt = f"""
You are writing one booking message for a business coach who wants to move a lead toward a scheduled call.

Lead context:
- Lead name: {signals["lead_name"]}
- Lead status: {signals["status"]}
- Booking status: {signals["booking_status"] or BookingStatus.NOT_STARTED.value}
- Qualification score: {signals["overall_score"]}
- Qualification reasoning: {signals["qualification_reasoning"]}
- Recommended action: {signals["recommended_action"]}
- Buying signals count: {signals["buying_signals_count"]}
- Pain signals count: {signals["pain_signals_count"]}
- Urgency level: {signals["urgency_level"]}
- Coach notes: {signals["coach_notes"] or "No notes yet"}
- Recent event types: {", ".join(signals["event_types"][:10]) or "No activity yet"}
- Known objections: {objections_summary}

Booking strategy:
- Booking mode: {strategy["booking_mode"]}
- Should push booking: {strategy["should_push_booking"]}
- Recommended timing: {strategy["recommended_timing"]}
- Strategy reasoning: {strategy["reasoning"]}
- Default CTA direction: {strategy["suggested_cta"]}
- Booking URL: {booking_url or "No booking URL configured"}

Write one strong, natural, concise booking message the coach can send manually.

Requirements:
- Keep it consultative and confident.
- Do not sound robotic or overly salesy.
- Do not mention internal scoring, memory, or systems.
- Match the booking mode exactly.
- If a booking URL exists, include it naturally in the message.
- Return a short subject line and a clear CTA.

Return JSON only with this shape:
{{
  "subject_line": "...",
  "message": "...",
  "suggested_cta": "..."
}}
"""

    raw = call_groq(prompt)
    parsed = json.loads(raw)
    return {
        "subject_line": parsed.get("subject_line", "").strip(),
        "message": parsed.get("message", "").strip(),
        "suggested_cta": parsed.get("suggested_cta", "").strip(),
    }


def build_booking_fallback(signals, strategy):
    lead_name = signals["lead_name"]
    booking_mode = strategy["booking_mode"]
    booking_link_line = f" You can book a time here: {BOOKING_URL}" if BOOKING_URL else ""

    subject_line = f"Quick next step, {lead_name}"
    message = (
        f"Hi {lead_name}, I wanted to check in and see whether it makes sense to move this conversation forward. "
        "If you'd like, we can identify the best next step based on where things currently stand."
    )
    suggested_cta = strategy["suggested_cta"]

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
            f"{booking_link_line}"
        )
        if BOOKING_URL:
            suggested_cta = "Use the booking link to choose a time that works for you."

    elif booking_mode == "booking_abandonment_recovery":
        subject_line = f"Still open to this, {lead_name}?"
        message = (
            f"Hi {lead_name}, just checking in in case booking a time slipped down the list. "
            "If it would help, we can keep the next step simple and just use a short call to answer the main questions first."
            f"{booking_link_line}"
        )
        if BOOKING_URL:
            suggested_cta = "Use the booking link if you want to restart the conversation with a short call."

    elif booking_mode == "direct_booking_push":
        subject_line = f"Let’s get a time locked in, {lead_name}"
        message = (
            f"Hi {lead_name}, based on everything we’ve discussed, I think the best next step is to get a call on the calendar. "
            "That way we can move from ideas into a concrete plan and make sure the next move is aligned with your priorities."
            f"{booking_link_line}"
        )
        if BOOKING_URL:
            suggested_cta = "Use the booking link to choose a time that works for you."

    elif booking_mode == "proposal_to_booking":
        subject_line = f"Let’s review the proposal together, {lead_name}"
        message = (
            f"Hi {lead_name}, now that you’ve had a chance to review the proposal, the best next step is to book a short call "
            "so we can walk through questions, align on fit, and decide how to move forward."
            f"{booking_link_line}"
        )
        if BOOKING_URL:
            suggested_cta = "Use the booking link to choose a time for a short proposal review call."

    elif booking_mode == "post_call_booking_push":
        subject_line = f"Let’s continue the conversation, {lead_name}"
        message = (
            f"Hi {lead_name}, I’d recommend booking the next conversation while the context is still fresh. "
            "That will give us the best chance to keep momentum and turn the discussion into a concrete action plan."
            f"{booking_link_line}"
        )
        if BOOKING_URL:
            suggested_cta = "Use the booking link to lock in the next conversation while momentum is high."

    elif booking_mode == "soft_booking_push":
        subject_line = f"Worth a quick conversation, {lead_name}?"
        message = (
            f"Hi {lead_name}, based on where things stand, it may be useful to have a short, low-pressure conversation "
            "to clarify what matters most and see whether there is a practical next step."
            f"{booking_link_line}"
        )
        if BOOKING_URL:
            suggested_cta = "Use the booking link to choose a time for a short clarity call."

    return {
        "subject_line": subject_line,
        "message": message,
        "suggested_cta": suggested_cta,
    }


def build_booking_suggestion(lead, qualification, report, activities):
    signals = extract_booking_signals(lead, qualification, report, activities)
    strategy = decide_booking_strategy(signals)

    try:
        message_payload = generate_booking_message(signals, strategy)
    except Exception:
        message_payload = build_booking_fallback(signals, strategy)

    return {
        "should_push_booking": strategy["should_push_booking"],
        "booking_mode": strategy["booking_mode"],
        "recommended_timing": strategy["recommended_timing"],
        "subject_line": message_payload["subject_line"],
        "message": message_payload["message"],
        "suggested_cta": message_payload["suggested_cta"] or strategy["suggested_cta"],
        "booking_url": BOOKING_URL or None,
        "reasoning": f"{strategy['reasoning']} {signals['qualification_reasoning']}".strip(),
        "context": {
            "status": signals["status"],
            "booking_status": signals["booking_status"],
            "overall_score": signals["overall_score"],
            "recommended_action": str(signals["recommended_action"]) if signals["recommended_action"] else None,
            "recent_event_types": signals["event_types"][:10],
        },
    }
