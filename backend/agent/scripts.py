import logging
from utils.llm import call_groq
from utils.jsonparser import parse_llm_response

logger = logging.getLogger(__name__)

def generate_scripts(psychology, objections, strategy, data):
    intelligence          = getattr(data, "_intelligence", {})
    synthesis             = intelligence.get("synthesis", {})
    personalization_hooks = synthesis.get("personalization_hooks", [])
    pain_signals          = synthesis.get("pain_signals", [])

    prompt = f"""
You are a world-class sales script writer for business coaches. Write a complete, word-for-word call script that feels natural and human — not robotic or salesy.

CLIENT INTEL:
- Client Name: {data.client_name}
- Problem They Mentioned: {data.problem_mentioned}
- Revenue Stage: {data.revenue_stage}
- Lead Temperature: {data.lead_temperature}
- Offer: {data.offer_type} at {data.coach_offer_price_range}
- Call Goal: {data.call_goal}
- Psychology Profile: {psychology}
- Closing Strategy: {strategy}

REAL INTELLIGENCE:
- Personalization Hooks: {personalization_hooks}
- Pain Signals: {pain_signals}

INSTRUCTIONS:
- Opening MUST use at least one personalization hook — not generic.
- Discovery questions must dig into pain, cost of inaction, and desired outcome.
- Value proposition must connect their exact problem to your offer outcome.
- Closing lines must feel natural, not pushy.
- Follow-up messages must be short, human, and non-desperate.
- Return ONLY valid JSON, no extra text.

{{
  "opening": "exact word-for-word opening line using a personalization hook",
  "discovery_questions": [
    "5 specific questions that uncover pain, urgency and buying intent"
  ],
  "value_proposition": "2-3 sentences connecting their exact problem to your offer outcome",
  "closing_lines": "exact word-for-word closing statement to use at the end of the call",
  "follow_up_sequence": [
    "Day 1 follow-up message",
    "Day 3 follow-up message",
    "Day 7 final follow-up message"
  ]
}}
"""
    response = call_groq(prompt)
    return parse_llm_response(response, "scripts")
