
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    citizen_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )

    description: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    # Citizen-provided area or locality
    locality: Mapped[str | None] = mapped_column(
        String(150), nullable=True
    )

    # Explainable rule-based priority
    priority: Mapped[str] = mapped_column(
        String(20), default="MEDIUM", nullable=False
    )

    priority_reason: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # Raw classifier decision score, not a probability
    model_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    # Reference to a possible original/related complaint
    duplicate_of_complaint_id: Mapped[int | None] = mapped_column(
        ForeignKey("complaints.id"), nullable=True
    )

    duplicate_similarity: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30), default="SUBMITTED", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    citizen = relationship(
        "User", back_populates="complaints"
    )

    department = relationship(
        "Department", back_populates="complaints"
    )

    status_history = relationship(
        "ComplaintStatusHistory",
        back_populates="complaint",
        cascade="all, delete-orphan",
    )
