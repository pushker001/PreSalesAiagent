import logging
from utils.llm import call_groq
from utils.jsonparser import parse_llm_response

logger = logging.getLogger(__name__)

def predict_objections(psychology, data):
    # Pull past memory from intelligence if available
    past_memory      = getattr(data, "_intelligence", {}).get("past_memory", {})
    known_objections = past_memory.get("known_objections", [])

    prompt = f"""
You are an expert sales coach. Predict the EXACT objections this client will raise and give sharp word-for-word responses.

CLIENT PROFILE:
- Pain Points: {psychology.get("pain_points", [])}
- Fears: {psychology.get("fears", [])}
- Decision Style: {psychology.get("decision_making_style", "")}
- Trust Level: {psychology.get("trust_level", "")}
- Urgency: {psychology.get("urgency_level", "")}

- Offer: {data.offer_type} at {data.coach_offer_price_range}
- Revenue Stage: {data.revenue_stage}
- Lead Temperature: {data.lead_temperature}
- Problem Mentioned: {data.problem_mentioned}
- Known Past Objections: {known_objections}

INSTRUCTIONS:
- If known past objections exist, address them first with from_memory: true.
- A cold lead will object more than a hot referral.
- Higher price = more price objections.
- Give real word-for-word rebuttals, not generic advice.
- Return ONLY valid JSON, no extra text.

{{
  "likely_objections": [
    {{
      "objection": "exact words the client might say",
      "probability": "high/medium/low",
      "response_strategy": "specific 2-3 sentence response to say out loud",
      "reframe_technique": "the psychological reframe being used"
    }}
  ]
}}
"""
    response = call_groq(prompt)
    return parse_llm_response(response, "objections")
