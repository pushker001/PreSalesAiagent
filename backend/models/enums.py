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
