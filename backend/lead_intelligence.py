"""
lead_intelligence_v2.py
6-layer lead intelligence engine with LLM synthesis + intelligence score.

Layer 1: Playwright  — website copy, blog RSS, podcast RSS
Layer 2: Google News RSS — via feedparser
Layer 3: YouTube       — public search scrape
Layer 4: Hunter.io + Clearbit + linkedin_summary (from form)
Layer 5: Trustpilot    — review scraping
Layer 6: JSON memory   — past interactions / known objections
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, quote_plus

import feedparser
import httpx
from playwright.async_api import async_playwright

# ---------------------------------------------------------------------------
# Config / constants
# ---------------------------------------------------------------------------

HUNTER_API_KEY   = os.getenv("HUNTER_API_KEY", "")
CLEARBIT_API_KEY = os.getenv("CLEARBIT_API_KEY", "")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY", "")   # used only for synthesis LLM
MEMORY_DIR       = Path(os.getenv("MEMORY_DIR", "memory"))

GOOGLE_NEWS_RSS  = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
YOUTUBE_SEARCH   = "https://www.youtube.com/results?search_query={query}"
TRUSTPILOT_URL   = "https://www.trustpilot.com/review/{domain}"

TIMEOUT          = 15          # seconds for HTTP calls
PLAYWRIGHT_WAIT  = 8_000       # ms


# ---------------------------------------------------------------------------
# Layer 1 — Playwright: website + blog RSS + podcast RSS
# ---------------------------------------------------------------------------

async def _playwright_scrape(domain: str) -> dict[str, Any]:
    """Visit homepage, extract text, meta, and look for feed URLs."""
    results: dict[str, Any] = {
        "homepage_text": "",
        "meta_description": "",
        "blog_posts": [],
        "podcast_episodes": [],
    }

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page    = await browser.new_page()

        try:
            await page.goto(f"https://{domain}", timeout=PLAYWRIGHT_WAIT * 2, wait_until="domcontentloaded")
            await page.wait_for_timeout(PLAYWRIGHT_WAIT)

            # Homepage copy
            results["homepage_text"] = (await page.inner_text("body"))[:4_000]

            # Meta description
            meta = await page.query_selector('meta[name="description"]')
            if meta:
                results["meta_description"] = (await meta.get_attribute("content")) or ""

            # Discover RSS/Atom feed links
            feed_links = await page.eval_on_selector_all(
                'link[type="application/rss+xml"], link[type="application/atom+xml"]',
                "els => els.map(e => e.href)"
            )

            for href in feed_links[:4]:
                feed = feedparser.parse(href)
                entries = [
                    {"title": e.get("title", ""), "summary": e.get("summary", "")[:300]}
                    for e in feed.entries[:5]
                ]
                # Crude heuristic — call it podcast if "episode" or "podcast" in feed title
                title_lower = (feed.feed.get("title") or "").lower()
                if any(kw in title_lower for kw in ("podcast", "episode", "show")):
                    results["podcast_episodes"] = entries
                else:
                    results["blog_posts"] = entries

        except Exception as exc:  # noqa: BLE001
            results["error"] = str(exc)
        finally:
            await browser.close()

    return results


# ---------------------------------------------------------------------------
# Layer 2 — Google News RSS
# ---------------------------------------------------------------------------

def _google_news(company_name: str) -> list[dict[str, str]]:
    url  = GOOGLE_NEWS_RSS.format(query=quote(company_name))
    feed = feedparser.parse(url)
    return [
        {"title": e.get("title", ""), "published": e.get("published", ""), "link": e.get("link", "")}
        for e in feed.entries[:10]
    ]


# ---------------------------------------------------------------------------
# Layer 3 — YouTube public search
# ---------------------------------------------------------------------------

async def _youtube_search(query: str) -> list[dict[str, str]]:
    """Scrape public YouTube search results (no API key required)."""
    url  = YOUTUBE_SEARCH.format(query=quote_plus(query))
    headers = {"User-Agent": "Mozilla/5.0 (compatible; LeadBot/1.0)"}

    async with httpx.AsyncClient(timeout=TIMEOUT, headers=headers) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except Exception:  # noqa: BLE001
            return []

    # Pull video IDs + titles from the raw HTML
    ids    = re.findall(r'"videoId":"([^"]{11})"', resp.text)
    titles = re.findall(r'"title":\{"runs":\[\{"text":"([^"]+)"', resp.text)

    seen, videos = set(), []
    for vid_id, title in zip(ids, titles):
        if vid_id not in seen:
            seen.add(vid_id)
            videos.append({"id": vid_id, "title": title, "url": f"https://youtu.be/{vid_id}"})
        if len(videos) >= 6:
            break

    return videos


# ---------------------------------------------------------------------------
# Layer 4 — Hunter.io + Clearbit + linkedin_summary
# ---------------------------------------------------------------------------

async def _hunter_domain(domain: str) -> dict[str, Any]:
    if not HUNTER_API_KEY:
        return {}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            r = await client.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "api_key": HUNTER_API_KEY, "limit": 5},
            )
            data = r.json().get("data", {})
            return {
                "organization": data.get("organization"),
                "emails": [e.get("value") for e in data.get("emails", [])[:5]],
                "employee_count": data.get("meta", {}).get("results"),
            }
        except Exception:  # noqa: BLE001
            return {}


async def _clearbit_company(domain: str) -> dict[str, Any]:
    if not CLEARBIT_API_KEY:
        return {}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            r = await client.get(
                f"https://company.clearbit.com/v2/companies/find?domain={domain}",
                headers={"Authorization": f"Bearer {CLEARBIT_API_KEY}"},
            )
            d = r.json()
            return {
                "name": d.get("name"),
                "description": d.get("description"),
                "industry": d.get("category", {}).get("industry"),
                "employees": d.get("metrics", {}).get("employees"),
                "raised": d.get("metrics", {}).get("raised"),
                "tech_stack": d.get("tech", [])[:10],
                "location": d.get("location"),
                "linkedin_handle": d.get("linkedin", {}).get("handle"),
                "twitter_handle": d.get("twitter", {}).get("handle"),
                "funding_stage": d.get("metrics", {}).get("latestFundingStage"),
            }
        except Exception:  # noqa: BLE001
            return {}


def _parse_linkedin_summary(text: str) -> dict[str, Any]:
    """Light parsing of raw LinkedIn copy pasted by the user."""
    if not text:
        return {}
    return {
        "raw": text[:2_000],
        "word_count": len(text.split()),
        "mentions_hiring": bool(re.search(r"\bhi(ring|red)\b", text, re.I)),
        "mentions_funding": bool(re.search(r"\b(series [a-e]|seed|funding|raise[sd]?)\b", text, re.I)),
        "mentions_award": bool(re.search(r"\b(award|recogni[sz]ed|ranked|best|top \d+)\b", text, re.I)),
    }


# ---------------------------------------------------------------------------
# Layer 5 — Trustpilot
# ---------------------------------------------------------------------------

async def _trustpilot(domain: str) -> dict[str, Any]:
    url     = TRUSTPILOT_URL.format(domain=domain)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; LeadBot/1.0)"}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page    = await browser.new_page()
        try:
            await page.goto(url, timeout=PLAYWRIGHT_WAIT * 2, wait_until="domcontentloaded")
            await page.wait_for_timeout(3_000)

            # Rating
            rating_el = await page.query_selector('[data-rating-typography]')
            rating    = (await rating_el.inner_text()).strip() if rating_el else "N/A"

            # Recent reviews
            review_els = await page.query_selector_all("article[data-service-review]")
            reviews    = []
            for el in review_els[:5]:
                body_el = await el.query_selector("[data-service-review-text-typography]")
                body    = (await body_el.inner_text()).strip()[:300] if body_el else ""
                reviews.append(body)

            return {"rating": rating, "recent_reviews": reviews}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}
        finally:
            await browser.close()


# ---------------------------------------------------------------------------
# Layer 6 — JSON memory store
# ---------------------------------------------------------------------------

def _load_memory(domain: str) -> dict[str, Any]:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    path = MEMORY_DIR / f"{domain.replace('.', '_')}.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _save_memory(domain: str, data: dict[str, Any]) -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    path = MEMORY_DIR / f"{domain.replace('.', '_')}.json"
    path.write_text(json.dumps(data, indent=2, default=str))


# ---------------------------------------------------------------------------
# LLM synthesis
# ---------------------------------------------------------------------------

_SYNTHESIS_SYSTEM = """
You are a senior sales intelligence analyst. Given raw data about a company, output ONLY valid JSON
matching this exact schema — no markdown fences, no extra keys:

{
  "company_summary":       "<2–3 sentence summary>",
  "pain_signals":          ["<signal>", ...],
  "buying_signals":        ["<signal>", ...],
  "personalization_hooks": ["<hook>", ...],
  "key_technologies":      ["<tech>", ...],
  "growth_stage":          "<seed|early|growth|enterprise|unknown>",
  "urgency_level":         "<low|medium|high>",
  "recommended_angle":     "<one-line pitch angle>",
  "risk_flags":            ["<flag>", ...]
}
"""


async def _llm_synthesize(raw: dict[str, Any]) -> dict[str, Any]:
    from utils.llm import call_groq
    from utils.jsonparser import parse_llm_response
    try:
        prompt = f"""
You are a senior sales intelligence analyst. Synthesize this company data into actionable sales intelligence.
Return ONLY valid JSON with these exact keys — no markdown, no extra text:

{{
  "company_summary":       "2-3 sentence summary of the business",
  "pain_signals":          ["specific pain point from data"],
  "buying_signals":        ["specific signal they are ready to buy"],
  "personalization_hooks": ["specific thing to reference in opening"],
  "key_technologies":      ["tech they use"],
  "growth_stage":          "seed|early|growth|enterprise|unknown",
  "urgency_level":         "low|medium|high",
  "recommended_angle":     "one-line pitch angle",
  "risk_flags":            ["potential risk or objection"]
}}

DATA: {json.dumps(raw, default=str)[:8000]}
"""
        response = call_groq(prompt)
        return parse_llm_response(response, "synthesis")
    except Exception:
        return _fallback_synthesis(raw)


def _fallback_synthesis(raw: dict[str, Any]) -> dict[str, Any]:
    """Rule-based fallback when LLM is unavailable."""
    cb   = raw.get("clearbit", {})
    news = raw.get("google_news", [])
    li   = raw.get("linkedin_parsed", {})

    pain_signals: list[str] = []
    buying_signals: list[str] = []

    if li.get("mentions_hiring"):
        buying_signals.append("Actively hiring — growth mode")
    if li.get("mentions_funding"):
        buying_signals.append("Recent funding round mentioned")
    if any("layoff" in (n.get("title") or "").lower() for n in news):
        pain_signals.append("Layoffs in recent news")
    if any("lawsuit" in (n.get("title") or "").lower() for n in news):
        pain_signals.append("Legal issues surfaced in news")

    tech_stack = cb.get("tech_stack") or []

    return {
        "company_summary":       cb.get("description") or "No description available.",
        "pain_signals":          pain_signals or ["No explicit pain signals detected"],
        "buying_signals":        buying_signals or ["No explicit buying signals detected"],
        "personalization_hooks": [
            f"Industry: {cb.get('industry')}" if cb.get("industry") else "No industry data",
            f"Location: {cb.get('location')}" if cb.get("location") else "No location data",
        ],
        "key_technologies":      tech_stack[:8],
        "growth_stage":          _infer_stage(cb),
        "urgency_level":         "medium",
        "recommended_angle":     "Value-led discovery call",
        "risk_flags":            [],
    }


def _infer_stage(cb: dict[str, Any]) -> str:
    emp = cb.get("employees") or 0
    stage_map = {
        "Seed":     "seed",
        "Series A": "early",
        "Series B": "early",
        "Series C": "growth",
        "Series D": "growth",
        "Series E": "enterprise",
    }
    fs = cb.get("funding_stage") or ""
    if fs in stage_map:
        return stage_map[fs]
    if emp < 20:
        return "seed"
    if emp < 100:
        return "early"
    if emp < 500:
        return "growth"
    return "enterprise"


# ---------------------------------------------------------------------------
# Intelligence score (0–100)
# ---------------------------------------------------------------------------

def _compute_intelligence_score(raw: dict[str, Any], synthesis: dict[str, Any]) -> int:
    """
    Weighted scoring across six dimensions.
    Max 100 points.
    """
    score = 0

    # 1. Data completeness (20 pts)
    completeness_checks = [
        bool(raw.get("website", {}).get("homepage_text")),
        bool(raw.get("google_news")),
        bool(raw.get("youtube_videos")),
        bool(raw.get("clearbit")),
        bool(raw.get("hunter")),
        bool(raw.get("trustpilot", {}).get("rating")),
    ]
    score += int(sum(completeness_checks) / len(completeness_checks) * 20)

    # 2. Signal richness (20 pts)
    pain_count    = len([s for s in synthesis.get("pain_signals", [])    if "no explicit" not in s.lower()])
    buying_count  = len([s for s in synthesis.get("buying_signals", [])  if "no explicit" not in s.lower()])
    hook_count    = len([h for h in synthesis.get("personalization_hooks", []) if "no " not in h.lower()])
    score += min(20, (pain_count + buying_count + hook_count) * 3)

    # 3. News recency (15 pts)
    news = raw.get("google_news", [])
    score += min(15, len(news) * 2)

    # 4. LinkedIn richness (15 pts)
    li = raw.get("linkedin_parsed", {})
    if li.get("mentions_hiring"):  score += 5
    if li.get("mentions_funding"): score += 5
    if li.get("mentions_award"):   score += 5

    # 5. Trustpilot data (15 pts)
    tp     = raw.get("trustpilot", {})
    rating = tp.get("rating", "N/A")
    try:
        r_val  = float(rating)
        score += min(15, int(r_val * 2))
    except (ValueError, TypeError):
        pass

    # 6. Urgency bonus (15 pts)
    urgency_map = {"high": 15, "medium": 8, "low": 2}
    score += urgency_map.get(synthesis.get("urgency_level", "medium"), 0)

    return min(100, max(0, score))


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def gather_lead_intelligence(
    domain: str,
    company_name: str,
    linkedin_summary: str = "",
) -> dict[str, Any]:
    """
    Run all 6 layers concurrently where possible, synthesize with LLM,
    compute intelligence score, update memory, and return full payload.
    """
    start = time.monotonic()

    # Load existing memory first (sync — fast)
    past_memory = _load_memory(domain)

    # Run IO-bound layers concurrently
    (
        website_data,
        hunter_data,
        clearbit_data,
        youtube_data,
        trustpilot_data,
    ) = await asyncio.gather(
        _playwright_scrape(domain),
        _hunter_domain(domain),
        _clearbit_company(domain),
        _youtube_search(company_name),
        _trustpilot(domain),
    )

    # Layer 2 is sync (feedparser is blocking) — run in executor
    loop = asyncio.get_event_loop()
    google_news = await loop.run_in_executor(None, _google_news, company_name)

    # Layer 4 partial — LinkedIn summary
    linkedin_parsed = _parse_linkedin_summary(linkedin_summary)

    # Assemble raw intelligence bundle
    raw = {
        "domain":          domain,
        "company_name":    company_name,
        "fetched_at":      datetime.now(timezone.utc).isoformat(),
        "website":         website_data,
        "google_news":     google_news,
        "youtube_videos":  youtube_data,
        "hunter":          hunter_data,
        "clearbit":        clearbit_data,
        "linkedin_parsed": linkedin_parsed,
        "trustpilot":      trustpilot_data,
        "past_memory":     past_memory,
    }

    # LLM synthesis
    synthesis = await _llm_synthesize(raw)

    # Intelligence score
    intelligence_score = _compute_intelligence_score(raw, synthesis)

    # Update memory
    updated_memory = {
        **past_memory,
        "last_enriched": datetime.now(timezone.utc).isoformat(),
        "intelligence_score": intelligence_score,
        "synthesis": synthesis,
        "known_objections": past_memory.get("known_objections", []),
        "interaction_history": past_memory.get("interaction_history", []),
    }
    _save_memory(domain, updated_memory)

    elapsed = round(time.monotonic() - start, 2)

    return {
        "domain":             domain,
        "company_name":       company_name,
        "intelligence_score": intelligence_score,
        "synthesis":          synthesis,
        "raw":                raw,
        "past_memory":        past_memory,
        "elapsed_seconds":    elapsed,
    }


# ---------------------------------------------------------------------------
# Sync wrapper — called by orchestrator
# ---------------------------------------------------------------------------

def collect_lead_intelligence(data):
    """Sync entry point for orchestrator compatibility"""
    from urllib.parse import urlparse

    domain = ""
    if data.website_url:
        domain = urlparse(data.website_url).netloc.replace("www.", "")

    linkedin_summary = getattr(data, "linkedin_summary", "") or ""

    result = asyncio.run(gather_lead_intelligence(
        domain=domain,
        company_name=data.client_name,
        linkedin_summary=linkedin_summary
    ))

    # Attach form fields for downstream agents
    result["client_type"]             = data.client_type
    result["revenue_stage"]           = data.revenue_stage
    result["lead_source"]             = data.lead_source
    result["lead_temperature"]        = data.lead_temperature
    result["problem_mentioned"]       = data.problem_mentioned
    result["coach_offer_price_range"] = data.coach_offer_price_range
    result["website_data"]            = result.get("raw", {}).get("website", {})

    return result
