import logging
from utils.llm import call_groq
from utils.jsonparser import parse_llm_response

logger = logging.getLogger(__name__)

def analyze_psychology(intelligence, data):
    synthesis      = intelligence.get("synthesis", {})
    pain_signals   = synthesis.get("pain_signals", [])
    buying_signals = synthesis.get("buying_signals", [])

    prompt = f"""
You are an expert business coach and sales psychologist. Deeply analyze this potential client.

CLIENT INTEL:
- Name: {data.client_name}
- Type: {data.client_type}
- Revenue Stage: {data.revenue_stage}
- Lead Source: {data.lead_source}
- Lead Temperature: {data.lead_temperature}
- Problem Mentioned: {data.problem_mentioned}
- Offer: {data.offer_type} at {data.coach_offer_price_range}
- Call Goal: {data.call_goal}

REAL INTELLIGENCE FROM WEB DATA:
- Pain Signals: {pain_signals}
- Buying Signals: {buying_signals}
- Business Stage: {synthesis.get("growth_stage", "unknown")}
- Urgency Level: {synthesis.get("urgency_level", "medium")}
- Company Summary: {synthesis.get("company_summary", "N/A")}

INSTRUCTIONS:
- Ground your analysis in the real pain and buying signals above.
- Be specific, not generic.
- Return ONLY valid JSON, no extra text.

{{
  "pain_points": ["3-5 specific pain points grounded in real signals"],
  "motivations": ["3-5 specific motivations driving them to seek help now"],
  "fears": ["3-5 specific fears that could stop them from buying"],
  "personality_type": "one sentence sharp personality read",
  "decision_making_style": "how they make decisions — fast/slow, data/emotion, solo/committee",
  "trust_level": "how much they trust you right now based on lead source and temperature",
  "urgency_level": "low/medium/high — and why"
}}
"""
    response = call_groq(prompt)
    return parse_llm_response(response, "psychology")
