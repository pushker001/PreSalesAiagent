from uuid import uuid4
from sqlalchemy import DateTime, String, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sender_settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    users = relationship("User", back_populates="organization")
    leads = relationship("Lead", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="owner", nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    organization = relationship("Organization", back_populates="users")
