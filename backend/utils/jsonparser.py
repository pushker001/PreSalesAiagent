"""
utils/jsonparser.py
Parses + validates LLM JSON output with schema enforcement and fallbacks.

Changes in v2:
  - Added SYNTHESIS_SCHEMA  (validates lead_intelligence_v2 synthesis output)
  - Added safe_parse_synthesis() with field-level fallback
  - Existing helpers kept intact
"""

from __future__ import annotations

import json
import re
from typing import Any


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

# Keys required in the synthesis block produced by lead_intelligence_v2
SYNTHESIS_SCHEMA: dict[str, type | tuple] = {
    "company_summary":       str,
    "pain_signals":          list,
    "buying_signals":        list,
    "personalization_hooks": list,
    "key_technologies":      list,
    "growth_stage":          str,
    "urgency_level":         str,
    "recommended_angle":     str,
    "risk_flags":            list,
}

SYNTHESIS_DEFAULTS: dict[str, Any] = {
    "company_summary":       "No summary available.",
    "pain_signals":          [],
    "buying_signals":        [],
    "personalization_hooks": [],
    "key_technologies":      [],
    "growth_stage":          "unknown",
    "urgency_level":         "medium",
    "recommended_angle":     "Value-led discovery call",
    "risk_flags":            [],
}

VALID_GROWTH_STAGES = {"seed", "early", "growth", "enterprise", "unknown"}
VALID_URGENCY_LEVELS = {"low", "medium", "high"}


# ---------------------------------------------------------------------------
# Core helpers (original)
# ---------------------------------------------------------------------------

def extract_json_block(text: str) -> str:
    """
    Strip markdown fences and extract the first JSON object or array
    from a raw LLM response string.
    """
    # Remove ```json ... ``` or ``` ... ``` fences
    text = re.sub(r"```(?:json)?", "", text).strip()

    # Find first { or [ and match to closing } or ]
    for start_char, end_char in (("{", "}"), ("[", "]")):
        idx = text.find(start_char)
        if idx == -1:
            continue
        depth, end_idx = 0, -1
        for i, ch in enumerate(text[idx:], start=idx):
            if ch == start_char:
                depth += 1
            elif ch == end_char:
                depth -= 1
                if depth == 0:
                    end_idx = i
                    break
        if end_idx != -1:
            return text[idx : end_idx + 1]

    return text  # return as-is; caller handles parse failure


def safe_parse(text: str, fallback: Any = None) -> Any:
    """
    Parse JSON from an LLM response string.
    Returns `fallback` on any failure.
    """
    try:
        cleaned = extract_json_block(text)
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return fallback


def ensure_list(value: Any) -> list:
    """Coerce a value to list — wraps scalars, passes lists through."""
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def ensure_str(value: Any, fallback: str = "") -> str:
    if isinstance(value, str):
        return value.strip()
    if value is None:
        return fallback
    return str(value).strip()


# ---------------------------------------------------------------------------
# Synthesis-specific parser (NEW)
# ---------------------------------------------------------------------------

def safe_parse_synthesis(raw: str | dict) -> dict[str, Any]:
    """
    Parse and validate a synthesis payload.

    Accepts either:
      - a raw JSON string (from LLM output)
      - an already-parsed dict

    Each field is validated against SYNTHESIS_SCHEMA.
    Missing or wrong-typed fields are replaced with SYNTHESIS_DEFAULTS.
    Enum fields (growth_stage, urgency_level) are normalised to their
    allowed value sets.

    Returns a fully-populated synthesis dict — never raises.
    """
    # --- 1. Parse if string
    if isinstance(raw, str):
        parsed = safe_parse(raw, fallback={})
    elif isinstance(raw, dict):
        parsed = raw
    else:
        parsed = {}

    if not isinstance(parsed, dict):
        parsed = {}

    # --- 2. Field-level validation + fallback
    result: dict[str, Any] = {}

    for field, expected_type in SYNTHESIS_SCHEMA.items():
        value   = parsed.get(field, SYNTHESIS_DEFAULTS[field])
        default = SYNTHESIS_DEFAULTS[field]

        # Type coercion
        if expected_type is list:
            value = ensure_list(value)
            # Ensure all list items are strings
            value = [ensure_str(item) for item in value if item is not None]
        elif expected_type is str:
            value = ensure_str(value, fallback=default)
        else:
            if not isinstance(value, expected_type):
                value = default

        result[field] = value

    # --- 3. Enum normalisation
    if result["growth_stage"] not in VALID_GROWTH_STAGES:
        result["growth_stage"] = "unknown"

    if result["urgency_level"] not in VALID_URGENCY_LEVELS:
        result["urgency_level"] = "medium"

    return result


# ---------------------------------------------------------------------------
# Generic schema validator (original, extended)
# ---------------------------------------------------------------------------

def validate_against_schema(
    data: dict[str, Any],
    schema: dict[str, type],
    defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Generic field-level validator.
    For each key in `schema`, ensures the value in `data` is of the right type.
    Replaces bad/missing values with defaults[key] if provided, else removes key.
    """
    defaults = defaults or {}
    out: dict[str, Any] = {}

    for key, expected in schema.items():
        val = data.get(key)
        if not isinstance(val, expected):
            if key in defaults:
                out[key] = defaults[key]
            # else: omit the key entirely
        else:
            out[key] = val

    return out


# ---------------------------------------------------------------------------
# Report-specific helpers (original)
# ---------------------------------------------------------------------------

def flatten_report(report: dict[str, Any]) -> dict[str, Any]:
    """
    Flatten a nested report dict one level deep for CSV/tabular export.
    Nested dicts become 'parent__child' keys.
    """
    flat: dict[str, Any] = {}
    for k, v in report.items():
        if isinstance(v, dict):
            for sub_k, sub_v in v.items():
                flat[f"{k}__{sub_k}"] = sub_v
        else:
            flat[k] = v
    return flat


# ---------------------------------------------------------------------------
# parse_llm_response — used by all agents
# ---------------------------------------------------------------------------

import logging as _logging
_logger = _logging.getLogger(__name__)

def parse_llm_response(response: str, agent_name: str) -> dict:
    """
    Parse LLM response with 3-layer fallback:
    1. Direct json.loads
    2. extract_json_block + json.loads
    3. Safe fallback dict
    """
    _FALLBACKS = {
        "psychology": {
            "pain_points": [], "motivations": [], "fears": [],
            "personality_type": "", "decision_making_style": "",
            "trust_level": "", "urgency_level": ""
        },
        "objections": {"likely_objections": []},
        "strategy": {
            "positioning": "", "recommended_close_type": "",
            "urgency_angle": "", "authority_lever": "",
            "timing_recommendation": "", "risk_mitigation": ""
        },
        "scripts": {
            "opening": "", "discovery_questions": [],
            "value_proposition": "", "closing_lines": "",
            "follow_up_sequence": []
        },
        "synthesis": {
            "company_summary": "", "pain_signals": [],
            "buying_signals": [], "personalization_hooks": [],
            "key_technologies": [], "growth_stage": "unknown",
            "urgency_level": "medium", "recommended_angle": "",
            "risk_flags": []
        }
    }

    # Layer 1 — direct parse
    try:
        return json.loads(response)
    except (json.JSONDecodeError, TypeError):
        pass

    # Layer 2 — extract JSON block then parse
    try:
        cleaned = extract_json_block(response)
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError) as e:
        _logger.error(f"{agent_name}: JSON parse failed: {e} | Raw: {str(response)[:300]}")

    # Layer 3 — safe fallback
    _logger.error(f"{agent_name}: Using safe fallback")
    return _FALLBACKS.get(agent_name, {})
