from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    lead_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("leads.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    intelligence_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    full_report_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    lead = relationship("Lead", back_populates="reports")
    qualifications = relationship(
        "Qualification",
        back_populates="report",
        cascade="all, delete-orphan",
    )
