from pydantic import BaseModel


class BookingSuggestionResponse(BaseModel):
    should_push_booking: bool
    booking_mode: str
    recommended_timing: str
    subject_line: str
    message: str
    suggested_cta: str
    booking_url: str | None = None
    reasoning: str
    context: dict | None = None
