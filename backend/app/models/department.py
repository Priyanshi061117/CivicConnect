from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False
    )

    complaints = relationship(
        "Complaint", back_populates="department"
    )

    officials = relationship(
        "User", back_populates="department"
    )