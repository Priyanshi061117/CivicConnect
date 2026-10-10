
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ComplaintCreate(BaseModel):
    description: str = Field(min_length=10, max_length=5000)
    locality: Optional[str] = Field(default=None, max_length=150)


class ComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    locality: Optional[str] = None
    status: str
    created_at: datetime

