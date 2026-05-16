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
from services.lead_activity_service import create_lead_activity, get_lead_activities
from schemas.lead_activity import LeadActivityInput, LeadActivityResponse
from schemas.follow_up import FollowUpSuggestionResponse
from services.follow_up_service import build_follow_up_suggestion
from schemas.booking import BookingSuggestionResponse
from services.booking_service import build_booking_suggestion
from schemas.conversation import ConversationSuggestionResponse, ConversationRequest
from services.conversation_service import build_conversation_suggestion
from services.dashboard_service import get_dashboard_metrics as fetch_dashboard_metrics
from schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse
from services.auth_service import signup_user, login_user, create_access_token
from middleware.auth import get_current_user

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
    return {"ready": True, **status}


# ---------- Auth Endpoints ----------
@app.post("/auth/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    from services.auth_service import get_user_by_email
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = signup_user(db, payload.email, payload.password, payload.org_name)
    token = create_access_token(user.id, user.org_id)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = login_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user.id, user.org_id)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    return current_user


# ---------- Lead Endpoints ----------
@app.get("/leads", response_model=list[LeadResponse])
def list_leads(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_all_leads(db, current_user.org_id)


@app.get("/leads/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    lead = get_lead_by_id(db, lead_id, current_user.org_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@app.get("/leads/{lead_id}/reports", response_model=list[ReportResponse])
def get_lead_reports(lead_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    lead = get_lead_by_id(db, lead_id, current_user.org_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return get_reports_by_lead_id(db, lead_id)


@app.get("/leads/{lead_id}/qualification", response_model=QualificationResponse)
def get_lead_qualification(lead_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    lead = get_lead_by_id(db, lead_id, current_user.org_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    qualification = get_latest_qualification_by_lead_id(db, lead_id)
    if not qualification:
        raise HTTPException(status_code=404, detail="Qualification not found")
    return qualification


@app.patch("/leads/{lead_id}", response_model=LeadResponse)
def patch_lead(lead_id: str, lead_update: LeadUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    update_data = lead_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No lead fields provided for update")

    existing_lead = get_lead_by_id(db, lead_id, current_user.org_id)
    if not existing_lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    previous_status = str(existing_lead.status)
    previous_booking_status = existing_lead.booking_status

    lead = update_lead(db, lead_id, update_data, current_user.org_id)

    if "status" in update_data:
        create_lead_activity(db, {
            "lead_id": lead.id,
            "event_type": "lead_status_updated",
            "title": "Lead status updated",
            "details": f"Lead status changed from {previous_status} to {lead.status}.",
            "metadata_json": {"from_status": previous_status, "to_status": str(lead.status)},
        })

    if "booking_status" in update_data:
        create_lead_activity(db, {
            "lead_id": lead.id,
            "event_type": "booking_status_updated",
            "title": "Booking status updated",
            "details": f"Booking status changed from {previous_booking_status or 'not_set'} to {lead.booking_status or 'not_set'}.",
            "metadata_json": {"from_booking_status": previous_booking_status, "to_booking_status": lead.booking_status},
        })

    if "coach_notes" in update_data:
        create_lead_activity(db, {
            "lead_id": lead.id,
            "event_type": "coach_note_added",
            "title": "Coach notes updated",
            "details": "Coach notes were added or updated for this lead.",
            "metadata_json": {"has_notes": bool(lead.coach_notes)},
        })

    return lead


@app.get("/leads/{lead_id}/activities", response_model=list[LeadActivityResponse])
def list_lead_activities(lead_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    lead = get_lead_by_id(db, lead_id, current_user.org_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return get_lead_activities(db, lead_id)


@app.post("/leads/{lead_id}/activities", response_model=LeadActivityResponse)
def create_manual_lead_activity(lead_id: str, activity_input: LeadActivityInput, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    lead = get_lead_by_id(db, lead_id, current_user.org_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return create_lead_activity(db, {
        "lead_id": lead_id,
        "event_type": activity_input.event_type,
        "title": activity_input.title,
        "details": activity_input.details,
        "metadata_json": activity_input.metadata_json,
    })


@app.post("/leads/{lead_id}/follow-up/generate", response_model=FollowUpSuggestionResponse)
def generate_follow_up(lead_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    lead = get_lead_by_id(db, lead_id, current_user.org_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    qualification = get_latest_qualification_by_lead_id(db, lead_id)
    if not qualification:
        raise HTTPException(status_code=404, detail="Qualification not found")
    reports = get_reports_by_lead_id(db, lead_id)
    if not reports:
        raise HTTPException(status_code=404, detail="Reports not found")
    activities = get_lead_activities(db, lead_id)
    return build_follow_up_suggestion(lead, qualification, reports[0].full_report_json, activities)


@app.post("/leads/{lead_id}/booking/generate", response_model=BookingSuggestionResponse)
def generate_booking_suggestion(lead_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    lead = get_lead_by_id(db, lead_id, current_user.org_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    qualification = get_latest_qualification_by_lead_id(db, lead_id)
    if not qualification:
        raise HTTPException(status_code=404, detail="Qualification not found")
    reports = get_reports_by_lead_id(db, lead_id)
    if not reports:
        raise HTTPException(status_code=404, detail="Report not found")
    activities = get_lead_activities(db, lead_id)
    suggestion = build_booking_suggestion(lead, qualification, reports[0].full_report_json, activities)
    create_lead_activity(db, {
        "lead_id": lead.id,
        "event_type": "booking_suggestion_generated",
        "title": "Booking suggestion generated",
        "details": f"Booking agent recommended mode {suggestion['booking_mode']} with timing {suggestion['recommended_timing']}.",
        "metadata_json": {
            "booking_mode": suggestion["booking_mode"],
            "should_push_booking": suggestion["should_push_booking"],
            "recommended_timing": suggestion["recommended_timing"],
            "suggested_cta": suggestion["suggested_cta"],
        },
    })
    return suggestion


@app.post("/leads/{lead_id}/conversation/generate", response_model=ConversationSuggestionResponse)
def generate_conversation_suggestion(lead_id: str, payload: ConversationRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    lead = get_lead_by_id(db, lead_id, current_user.org_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    qualification = get_latest_qualification_by_lead_id(db, lead_id)
    if not qualification:
        raise HTTPException(status_code=404, detail="Qualification not found")
    reports = get_reports_by_lead_id(db, lead_id)
    if not reports:
        raise HTTPException(status_code=404, detail="Report not found")
    activities = get_lead_activities(db, lead_id)
    suggestion = build_conversation_suggestion(lead, qualification, reports[0].full_report_json, activities, payload.current_message)
    create_lead_activity(db, {
        "lead_id": lead.id,
        "event_type": "conversation_suggestion_generated",
        "title": "Conversation suggestion generated",
        "details": f"Conversation agent generated a {suggestion['reply_type']} reply for the latest lead message.",
        "metadata_json": {"reply_type": suggestion["reply_type"], "next_step": suggestion["next_step"]},
    })
    return suggestion


@app.post("/leads/{lead_id}/booking/mark-link-sent", response_model=LeadResponse)
def mark_booking_link_sent(lead_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    lead = get_lead_by_id(db, lead_id, current_user.org_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead = update_lead(db, lead_id, {"booking_status": "link_sent"}, current_user.org_id)
    create_lead_activity(db, {
        "lead_id": lead_id,
        "event_type": "booking_link_sent",
        "title": "Booking link sent",
        "details": "Coach marked the booking link as sent to this lead.",
        "metadata_json": {"booking_status": "link_sent"},
    })
    return lead


@app.get("/dashboard/metrics")
def dashboard_metrics(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return fetch_dashboard_metrics(db, current_user.org_id)


# ---------- Streaming Endpoint ----------
@app.post("/analyze-closure")
def analyze_closure(data: ClosureRequest, current_user=Depends(get_current_user)):
    if not GROQ_API_KEY:
        return StreamingResponse(error_stream("GROQ_API_KEY not configured"), media_type="application/x-ndjson")

    if not data.client_name or not data.client_name.strip():
        return StreamingResponse(error_stream("client_name is required"), media_type="application/x-ndjson")

    try:
        orchestrator = ClosureAgentOrchestrator()
        return StreamingResponse(
            orchestrator.stream(data, org_id=current_user.org_id),
            media_type="application/x-ndjson",
            headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"}
        )
    except Exception as e:
        logger.error(f"Failed to start orchestrator: {e}")
        return StreamingResponse(error_stream(f"Failed to start analysis: {str(e)}"), media_type="application/x-ndjson")
