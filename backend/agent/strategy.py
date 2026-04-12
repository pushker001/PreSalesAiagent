import logging
from utils.llm import call_groq
from utils.jsonparser import parse_llm_response

logger = logging.getLogger(__name__)

def build_closing_strategy(psychology, objections, data):
    synthesis             = getattr(data, "_intelligence", {}).get("synthesis", {})
    buying_signals        = synthesis.get("buying_signals", [])
    personalization_hooks = synthesis.get("personalization_hooks", [])
    recommended_angle     = synthesis.get("recommended_angle", "")

    prompt = f"""
You are a master sales strategist for high-ticket business coaches. Build a precise closing strategy.

CLIENT PROFILE:
- Pain Points: {psychology.get("pain_points", [])}
- Motivations: {psychology.get("motivations", [])}
- Decision Style: {psychology.get("decision_making_style", "")}
- Urgency: {psychology.get("urgency_level", "")}
- Top Objections: {[o.get("objection") for o in objections.get("likely_objections", [])]}
- Offer: {data.offer_type} at {data.coach_offer_price_range}
- Call Goal: {data.call_goal}
- Lead Temperature: {data.lead_temperature}
- Revenue Stage: {data.revenue_stage}

REAL INTELLIGENCE:
- Buying Signals: {buying_signals}
- Personalization Hooks: {personalization_hooks}
- Recommended Angle: {recommended_angle}

INSTRUCTIONS:
- Warm/hot leads need a direct close. Cold leads need consultative approach first.
- Use buying signals to build urgency angle.
- Use personalization hooks in authority lever.
- Return ONLY valid JSON, no extra text.

{{
  "positioning": "how to position yourself and your offer on this specific call",
  "recommended_close_type": "Consultative Close / Assumptive Close / Direct Close / Trial Close",
  "urgency_angle": "specific reason why they should decide today — reference buying signals",
  "authority_lever": "what to say to establish credibility — reference personalization hooks",
  "timing_recommendation": "exactly when in the call to transition to the close",
  "risk_mitigation": "what to offer to reduce their fear of committing"
}}
"""
    response = call_groq(prompt)
    return parse_llm_response(response, "strategy")
