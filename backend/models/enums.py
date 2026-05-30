from enum import Enum


class LeadStatus(str, Enum):
    NEW = "new"
    ANALYZED = "analyzed"
    QUALIFIED = "qualified"
    NURTURE = "nurture"
    BOOKED = "booked"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class RecommendedAction(str, Enum):
    BOOK_CALL = "book_call"
    FOLLOW_UP = "follow_up"
    NURTURE = "nurture"
    DISQUALIFY = "disqualify"

class BookingStatus(str, Enum):
    NOT_STARTED = "not_started"
    LINK_SENT = "link_sent"
    REMINDER_SENT = "reminder_sent"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    ABANDONED = "abandoned"

class AgentName(str, Enum):
    BOOKING = "booking_agent"
    Qualification = "qualification_agent"
    FOLLOW_UP = "follow_up_agent"
    CONVERSATION = "conversation_agent"

class AgentActionType(str, Enum):
    SEND_FOLLOW_UP = "send_follow_up"
    SEND_BOOKING_LINK = "send_booking_link"
    SEND_BOOKING_REMINDER = "send_booking_reminder"
    SEND_RECOVERY_MESSAGE = "send_recovery_message"
    HANDLE_OBJECTION = "handle_objection"
    ESCALATE_TO_COACH = "escalate_to_coach"


class AgentActionStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SENT = "sent"
    COMPLETED = "completed"
    DISMISSED = "dismissed"
    FAILED = "failed"


class AgentActionPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class SystemEventType(str, Enum):
    LEAD_CREATED = "lead_created"
    ANALYSIS_COMPLETED = "analysis_completed"
    QUALIFICATION_CREATED = "qualification_created"
    BOOKING_LINK_SENT = "booking_link_sent"
    BOOKING_CONFIRMED = "booking_confirmed"
    FOLLOW_UP_SENT = "follow_up_sent"
    CONVERSATION_REPLY_GENERATED = "conversation_reply_generated"
    PROPOSAL_SENT = "proposal_sent"
    BOOKING_REMINDER_SENT = "booking_reminder_sent"
    BOOKING_RECOVERY_SENT = "booking_recovery_sent"
