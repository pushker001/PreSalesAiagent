from uuid import uuid4

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from models.enums import LeadStatus


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    client_name: Mapped[str] = mapped_column(String(255), index=True)
    website_url: Mapped[str | None] = mapped_column(String(500), index=True, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    linkedin_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_type: Mapped[str] = mapped_column(String(120))
    revenue_stage: Mapped[str] = mapped_column(String(120))
    lead_source: Mapped[str] = mapped_column(String(120))
    lead_temperature: Mapped[str] = mapped_column(String(50))
    problem_mentioned: Mapped[str] = mapped_column(Text)
    coach_offer_price_range: Mapped[str] = mapped_column(String(120))
    offer_type: Mapped[str] = mapped_column(String(120))
    call_goal: Mapped[str] = mapped_column(String(120))
    coach_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    booking_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, name="lead_status"),
        default=LeadStatus.NEW,
        nullable=False,
    )
    last_activity_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    reports = relationship("Report", back_populates="lead", cascade="all, delete-orphan")
    qualifications = relationship(
        "Qualification",
        back_populates="lead",
        cascade="all, delete-orphan",
    )
