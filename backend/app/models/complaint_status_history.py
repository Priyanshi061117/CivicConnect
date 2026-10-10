from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ComplaintStatusHistory(Base):
    __tablename__ = "complaint_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("complaints.id"), nullable=False
    )

    changed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    status: Mapped[str] = mapped_column(String(30), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    complaint = relationship("Complaint", back_populates="status_history")
    changed_by = relationship(
        "User",
        back_populates="status_updates",
        foreign_keys=[changed_by_user_id],
    )