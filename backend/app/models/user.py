from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    full_name: Mapped[str] = mapped_column(
        String(120), nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20), default="citizen", nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    complaints = relationship(
        "Complaint", back_populates="citizen"
    )

    department = relationship(
        "Department", back_populates="officials"
    )

    status_updates = relationship(
        "ComplaintStatusHistory",
        back_populates="changed_by",
        foreign_keys="ComplaintStatusHistory.changed_by_user_id",
    )