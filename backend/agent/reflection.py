import logging
from utils.llm import call_groq
from utils.jsonparser import parse_llm_response
 
logger = logging.getLogger(__name__)
 
 
# ─────────────────────────────────────────────────────────────
# Reflection Point 1 — Psychology
# Auto-retry if score < 7/10
# Feeds 3 downstream agents so highest ROI
# ─────────────────────────────────────────────────────────────
 
def critique_psychology(psychology: dict, lead_info: dict, data) -> dict:
    synthesis    = lead_info.get("synthesis", {})
    pain_signals = synthesis.get("pain_signals", [])
 
    critique_prompt = f"""
You are a senior sales intelligence reviewer. Score this psychology analysis strictly.
 
PSYCHOLOGY OUTPUT:
- Pain Points: {psychology.get("pain_points", [])}
- Motivations: {psychology.get("motivations", [])}
- Fears: {psychology.get("fears", [])}
- Personality Type: {psychology.get("personality_type", "")}
- Decision Style: {psychology.get("decision_making_style", "")}
- Urgency Level: {psychology.get("urgency_level", "")}
 
REAL WEB INTELLIGENCE (pain points MUST be grounded in these):
- Pain Signals: {pain_signals}
- Company Summary: {synthesis.get("company_summary", "")}
- Growth Stage: {synthesis.get("growth_stage", "")}
 
SCORING CRITERIA:
1. Are pain points specific to this company or generic?
2. Are motivations grounded in real buying signals?
3. Is urgency level justified by real data?
 
Return ONLY valid JSON:
{{
  "specificity_score": 8,
  "grounded_in_intel": true,
  "generic_fields": ["pain_points"],
  "pass": true,
  "improvement_notes": "specific instructions to improve"
}}
"""
    response = call_groq(critique_prompt)
    critique  = parse_llm_response(response, "psychology")
    score     = critique.get("specificity_score", 10)
    critique["pass"] = score >= 7
 
    if not critique["pass"]:
        logger.warning(f"Psychology score {score}/10 — retrying with stricter prompt")
 
        # Import here to avoid circular import at module level
        from agent.psychology import analyze_psychology
 
        improved = analyze_psychology(
            lead_info,
            data,
            retry_note=critique.get("improvement_notes", "")
        )
 
        # Guard: only accept the retry if it returned a non-empty valid dict
        if improved and improved.get("pain_points"):
            improved["_reflection"] = {"retried": True, "original_score": score}
            return improved
 
        logger.warning("Psychology retry returned empty result — keeping original")
 
    psychology["_reflection"] = {"retried": False, "score": score}
    return psychology
 
 
# ─────────────────────────────────────────────────────────────
# Reflection Point 2 — Scripts
# Rewrites only failing sections, not the full script
# ─────────────────────────────────────────────────────────────
 
def critique_scripts(scripts: dict, intelligence: dict, psychology: dict, strategy: dict, objections: dict, data) -> dict:
    hooks       = intelligence.get("synthesis", {}).get("personalization_hooks", [])
    pain_points = psychology.get("pain_points", [])
 
    critique_prompt = f"""
You are a senior sales coach reviewing a call script. Score strictly.
 
SCRIPT TO REVIEW:
- Opening: {scripts.get("opening", "")}
- First Discovery Question: {scripts.get("discovery_questions", [""])[0]}
- Value Proposition: {scripts.get("value_proposition", "")}
- Closing Lines: {scripts.get("closing_lines", "")}
 
PERSONALIZATION HOOKS AVAILABLE (opening MUST use one):
{hooks}
 
CLIENT PAIN POINTS (value prop MUST reference these):
{pain_points}
 
SCORING CRITERIA:
1. Does opening use a real personalization hook — not generic?
2. Are discovery questions specific — not "what are your goals?"
3. Is value proposition connected to exact pain points?
4. Are closing lines natural — not pushy?
 
Return ONLY valid JSON:
{{
  "opening_uses_hook": true,
  "questions_are_specific": true,
  "value_prop_is_specific": true,
  "closing_is_natural": true,
  "overall_score": 8,
  "pass": true,
  "rewrite_fields": [],
  "notes": "specific fix instructions per field"
}}
"""
    response = call_groq(critique_prompt)
    critique  = parse_llm_response(response, "synthesis")
    score     = critique.get("overall_score", 10)
    critique["pass"] = score >= 7
 
    fields_to_fix = critique.get("rewrite_fields", [])
 
    if not critique["pass"] or fields_to_fix:
        logger.info(f"Scripts score {score}/10 — rewriting fields: {fields_to_fix}")
 
        # Call generate_scripts with a retry note so it uses the full context
        # (strategy, objections, offer type) — not a stripped-down rewrite prompt
        from agent.scripts import generate_scripts
        improved = generate_scripts(
            psychology,
            objections,
            strategy,
            data,
            retry_note=critique.get("notes", ""),
            rewrite_fields=fields_to_fix
        )
 
        if improved:
            # Only replace the fields that were flagged — keep the rest from original
            for field in fields_to_fix:
                if field in improved and improved[field]:
                    scripts[field] = improved[field]
 
    scripts["_reflection"] = {"score": score, "fields_rewritten": fields_to_fix}
    return scripts
 
 
# ─────────────────────────────────────────────────────────────
# Reflection Point 3 — Final Report
# No retry — cross-section consistency check only
# Returns consistency_check dict, does NOT mutate report
# ─────────────────────────────────────────────────────────────
 
def critique_report(report: dict) -> dict:
    psychology = report.get("psychology", {})
    objections = report.get("objections", [])
    strategy   = report.get("strategy", {})
    scripts    = report.get("scripts", {})
    synthesis  = report.get("synthesis", {})
 
    prompt = f"""
You are a senior sales strategist doing a final consistency check across a sales report.
 
PSYCHOLOGY:
- Pain Points: {psychology.get("pain_points", [])}
- Urgency: {psychology.get("urgency_level", "")}
- Decision Style: {psychology.get("decision_making_style", "")}
 
TOP OBJECTIONS: {[o.get("objection") for o in objections[:3]]}
 
STRATEGY:
- Close Type: {strategy.get("recommended_close_type", "")}
- Urgency Angle: {strategy.get("urgency_angle", "")}
- Positioning: {strategy.get("positioning", "")}
 
SCRIPTS:
- Opening: {scripts.get("opening", "")}
- Value Proposition: {scripts.get("value_proposition", "")}
- Closing Lines: {scripts.get("closing_lines", "")}
 
INTELLIGENCE:
- Growth Stage: {synthesis.get("growth_stage", "")}
- Recommended Angle: {synthesis.get("recommended_angle", "")}
 
CHECK FOR:
1. Does close type match the lead urgency and decision style?
2. Does the script opening match the strategy positioning?
3. Are the top objections addressed anywhere in the scripts?
4. Is the urgency angle in strategy reflected in closing lines?
 
Return ONLY valid JSON:
{{
  "consistency_score": 8,
  "flags": [
    {{
      "section": "scripts.closing_lines",
      "issue": "closing does not match consultative close type",
      "severity": "medium"
    }}
  ],
  "overall_coherent": true,
  "summary": "one sentence overall assessment"
}}
"""
    response = call_groq(prompt)
    result   = parse_llm_response(response, "synthesis")
 
    # Return a clean dict — caller decides where to attach it
    return {
        "score":            result.get("consistency_score", 10),
        "flags":            result.get("flags", []),
        "overall_coherent": result.get("overall_coherent", True),
        "summary":          result.get("summary", "")
    }