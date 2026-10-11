import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="attorney")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    status: Mapped[str] = mapped_column(String(32), default="submitted", index=True)

    # Contact PII: stored for the attorney, NEVER sent to the LLM.
    claimant_name: Mapped[str] = mapped_column(String(255))
    claimant_email: Mapped[str] = mapped_column(String(255))
    claimant_phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    injury_type_reported: Mapped[str] = mapped_column(String(128))
    incident_description_redacted: Mapped[str] = mapped_column(Text)

    # Raw uploads are never persisted; only redacted text is stored.
    document_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    document_text_redacted: Mapped[str] = mapped_column(Text, default="")
    redaction_counts: Mapped[dict] = mapped_column(JSON, default=dict)

    extraction: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    funding_low: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    funding_high: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recommendation: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    score_factors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    memo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("cases.id"), nullable=True, index=True
    )
    # e.g. "attorney:jane@firm.test", "service:n8n", "public:portal", "anonymous"
    actor: Mapped[str] = mapped_column(String(255))
    # e.g. case.created, case.viewed, case.status_changed, case.extracted, auth.login_failed
    action: Mapped[str] = mapped_column(String(64), index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
