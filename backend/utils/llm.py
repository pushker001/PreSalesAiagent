import requests
import os
import logging
import re
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

logger = logging.getLogger(__name__)


def extract_json(text: str):
    """Strip markdown code blocks and extract clean JSON"""
    # Remove ```json ... ``` or ``` ... ``` wrappers
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    text = re.sub(r"```\s*$", "", text).strip()
    return text

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
def call_groq(prompt: str):
    """Make API call to Groq LLM"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a professional sales strategist and closure expert for coaches. Always respond with valid JSON only. No markdown, no code blocks, no extra text. Just raw JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"}
    }

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.warning(f"Groq request timeout after {REQUEST_TIMEOUT}s - retrying...")
        raise
    except requests.exceptions.RequestException as e:
        logger.warning(f"Groq request failed: {e} — retrying...")
        raise

    data = response.json()

    if "error" in data:
        raise Exception(f"Groq API Error: {data['error']}")

    raw = data["choices"][0]["message"]["content"]
    return extract_json(raw)

