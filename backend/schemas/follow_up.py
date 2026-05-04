from pydantic import BaseModel


class FollowUpSuggestionResponse(BaseModel):
    follow_up_type: str
    recommended_timing: str
    subject_line: str
    message: str
    reasoning: str
    context: dict | None = None
