from datetime import datetime

from sqlalchemy import (
    DateTime, ForeignKey, Integer, String, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class DuplicateReview(Base):
    __tablename__ = "duplicate_reviews"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("complaints.id"), unique=True, nullable=False
    )

    reviewed_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    decision: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    comment: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    complaint = relationship("Complaint")
    reviewed_by = relationship("User")