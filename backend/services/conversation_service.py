import json

from models.enums import RecommendedAction
from utils.llm import call_groq


def extract_conversation_signals(lead, qualification, report, activities):
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
        "has_proposal_sent": "proposal_sent" in event_types,
        "has_booking_reminder_sent": "booking_reminder_sent" in event_types,
    }


def decide_conversation_strategy(signals, current_message):
    message = (current_message or "").lower()

    objection_keywords = [
        "too expensive",
        "need to think",
        "not sure",
        "bad timing",
        "send details",
        "let me discuss",
        "not now",
        "maybe later",
        "no budget",
    ]

    if any(keyword in message for keyword in objection_keywords):
        return {
            "reply_type": "objection_response",
            "next_step": "Handle the hesitation and keep momentum alive.",
            "reasoning": "The current message contains hesitation or objection language, so the reply should address resistance directly.",
        }

    if (
        signals["recommended_action"] == RecommendedAction.BOOK_CALL
        and signals["booking_status"] not in {"confirmed", "completed"}
    ):
        return {
            "reply_type": "booking_push",
            "next_step": "Guide the lead toward booking the next conversation.",
            "reasoning": "Qualification indicates the lead is ready for a booking-oriented response.",
        }

    if signals["has_call_logged"]:
        return {
            "reply_type": "post_call_followup",
            "next_step": "Continue the conversation from the previous call and move the lead toward a concrete next step.",
            "reasoning": "A prior call is recorded in memory, so the response should build on that context.",
        }

    return {
        "reply_type": "nurture_reply",
        "next_step": "Respond helpfully without pushing too hard.",
        "reasoning": "No strong objection or booking trigger was found, so a softer nurture reply fits best.",
    }


def generate_conversation_reply(signals, strategy, current_message):
    objections = signals.get("objections", [])
    objections_summary = ", ".join(
        objection.get("objection", "")
        for objection in objections
        if isinstance(objection, dict) and objection.get("objection")
    ) or "No explicit objections recorded."

    prompt = f"""
You are writing a single reply suggestion for a business coach during a live sales conversation.

Lead context:
- Lead name: {signals["lead_name"]}
- Lead status: {signals["status"]}
- Booking status: {signals["booking_status"] or "not_set"}
- Qualification score: {signals["overall_score"]}
- Qualification reasoning: {signals["qualification_reasoning"]}
- Recommended action: {signals["recommended_action"]}
- Buying signals count: {signals["buying_signals_count"]}
- Pain signals count: {signals["pain_signals_count"]}
- Urgency level: {signals["urgency_level"]}
- Coach notes: {signals["coach_notes"] or "No notes yet"}
- Recent event types: {", ".join(signals["event_types"][:10]) or "No activity yet"}
- Known objections: {objections_summary}

Current lead message:
{current_message}

Reply strategy:
- Reply type: {strategy["reply_type"]}
- Next step: {strategy["next_step"]}
- Reasoning: {strategy["reasoning"]}

Write one strong, natural, concise reply the coach can send or say next.
Requirements:
- Keep it consultative and confident.
- Do not sound robotic.
- Do not mention internal scoring, memory, or systems.
- Align with the chosen reply type and next step.

Return JSON only with this shape:
{{
  "suggested_reply": "..."
}}
"""

    raw = call_groq(prompt)
    parsed = json.loads(raw)
    return parsed.get("suggested_reply", "").strip()


def build_conversation_suggestion(lead, qualification, report, activities, current_message):
    signals = extract_conversation_signals(lead, qualification, report, activities)
    strategy = decide_conversation_strategy(signals, current_message)
    suggested_reply = generate_conversation_reply(signals, strategy, current_message)

    return {
        "reply_type": strategy["reply_type"],
        "suggested_reply": suggested_reply,
        "next_step": strategy["next_step"],
        "reasoning": f"{strategy['reasoning']} {signals['qualification_reasoning']}".strip(),
        "context": {
            "status": signals["status"],
            "booking_status": signals["booking_status"],
            "overall_score": signals["overall_score"],
            "recommended_action": str(signals["recommended_action"]) if signals["recommended_action"] else None,
            "recent_event_types": signals["event_types"][:10],
        },
    }
