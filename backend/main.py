from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import json
import logging
from dotenv import load_dotenv
from orchestrator import ClosureAgentOrchestrator

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# ---------- Request Schema ----------
class ClosureRequest(BaseModel):
    client_name: str
    linkedin_url: str | None = None
    website_url: str | None = None
    client_type: str
    revenue_stage: str
    lead_source: str
    lead_temperature: str
    problem_mentioned: str
    coach_offer_price_range: str
    offer_type: str
    call_goal: str
    linkedin_summary: str | None = ""


def error_stream(message: str):
    """Helper — yields a single error event as a stream"""
    yield json.dumps({"event": "error", "message": message}) + "\n"


# ---------- Streaming Endpoint ----------
@app.post("/analyze-closure")
def analyze_closure(data: ClosureRequest):
    if not GROQ_API_KEY:
        return StreamingResponse(
            error_stream("GROQ_API_KEY not configured"),
            media_type="application/x-ndjson"
        )

    if not data.client_name or not data.client_name.strip():
        return StreamingResponse(
            error_stream("client_name is required"),
            media_type="application/x-ndjson"
        )

    try:
        orchestrator = ClosureAgentOrchestrator()
        return StreamingResponse(
            orchestrator.stream(data),
            media_type="application/x-ndjson",
            headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"}
        )
    except Exception as e:
        logger.error(f"Failed to start orchestrator: {e}")
        return StreamingResponse(
            error_stream(f"Failed to start analysis: {str(e)}"),
            media_type="application/x-ndjson"
        )
