from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from models.enums import RecommendedAction


class Qualification(Base):
    __tablename__ = "qualifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    lead_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("leads.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    report_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("reports.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    fit_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    urgency_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    readiness_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overall_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recommended_action: Mapped[RecommendedAction] = mapped_column(
        Enum(RecommendedAction, name="recommended_action"),
        nullable=False,
    )
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    lead = relationship("Lead", back_populates="qualifications")
    report = relationship("Report", back_populates="qualifications")
