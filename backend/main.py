from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
from dotenv import load_dotenv
from orchestrator import ClosureAgentOrchestrator

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)

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


# ---------- Main Endpoint ----------
@app.post("/analyze-closure")
def analyze_closure(data: ClosureRequest):
    try:
        if not GROQ_API_KEY:
            return {"status": "error", "message": "GROQ_API_KEY not configured"}

        orchestrator = ClosureAgentOrchestrator()
        closure_report = orchestrator.run(data)

        return {
            "status": "success",
            "closure_report": closure_report
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
