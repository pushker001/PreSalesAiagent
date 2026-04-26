from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import json
import logging
from dotenv import load_dotenv
from orchestrator import ClosureAgentOrchestrator
from sqlalchemy.orm import Session

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

DATABASE_LAYER_READY = False
database_import_error = None

try:
    from db.session import check_database_connection, get_db
    from schemas.lead import LeadResponse, LeadUpdate
    from schemas.report import ReportResponse
    from schemas.qualification import QualificationResponse
    from services.lead_service import get_all_leads, get_lead_by_id, update_lead
    from services.reports_service import get_reports_by_lead_id
    from services.qualification_service import get_latest_qualification_by_lead_id

    DATABASE_LAYER_READY = True
except Exception as exc:  # noqa: BLE001
    database_import_error = str(exc)
    logger.warning("Database layer not ready: %s", exc)

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


@app.get("/health/database")
def database_health():
    if not DATABASE_LAYER_READY:
        return {
            "ready": False,
            "connected": False,
            "message": "Database layer unavailable until SQLAlchemy dependencies and DATABASE_URL are configured.",
            "details": database_import_error,
        }

    status = check_database_connection()
    return {
        "ready": True,
        **status,
    }
# get all leads

@app.get("/leads", response_model=list[LeadResponse])
def list_leads(db: Session = Depends(get_db)):
    return get_all_leads(db)

# get lead by id

@app.get("/leads/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: str, db: Session = Depends(get_db)):
    lead = get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@app.get("/leads/{lead_id}/reports", response_model=list[ReportResponse])
def get_lead_reports(lead_id: str, db: Session = Depends(get_db)):
    lead = get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return get_reports_by_lead_id(db, lead_id)


@app.get("/leads/{lead_id}/qualification", response_model=QualificationResponse)
def get_lead_qualification(lead_id: str, db: Session = Depends(get_db)):
    lead = get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    qualification = get_latest_qualification_by_lead_id(db, lead_id)
    if not qualification:
        raise HTTPException(status_code=404, detail="Qualification not found")

    return qualification


@app.patch("/leads/{lead_id}", response_model=LeadResponse)
def patch_lead(lead_id: str, lead_update: LeadUpdate, db: Session = Depends(get_db)):
    update_data = lead_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No lead fields provided for update")

    lead = update_lead(db, lead_id, update_data)

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return lead



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
