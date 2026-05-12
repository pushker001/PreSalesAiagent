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

