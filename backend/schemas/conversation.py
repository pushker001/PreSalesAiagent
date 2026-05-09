from pydantic import BaseModel

class ConversationRequest(BaseModel):
    current_message: str

class ConversationSuggestionResponse(BaseModel):
    reply_type: str
    suggested_reply: str
    next_step: str
    reasoning: str
    context: dict | None = None
