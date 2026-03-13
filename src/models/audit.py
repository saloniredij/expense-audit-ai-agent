import uuid
from typing import Dict, Any, List
from enum import Enum

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import String, ForeignKey

from .base import Base, TimestampMixin, UUIDMixin

class AuditStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AuditReport(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "audit_reports"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[AuditStatus] = mapped_column(String, default=AuditStatus.PENDING, index=True)
    raw_result: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="reports")
