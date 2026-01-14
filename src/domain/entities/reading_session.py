"""Session entities for the reading coach application."""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Session status enum."""
    READY = "ready"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class ReadingSession(BaseModel):
    """Session entity representing a reading session."""
    
    id: UUID = Field(default_factory=uuid.uuid4)
    student_id: str
    book_id: str
    current_page: int = Field(default=1, ge=1)
    sample_rate: int = Field(default=16000)
    status: SessionStatus = SessionStatus.INITIALIZING
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic model configuration."""
        
        json_schema_extra = {
            "example": {
                "id": "sess-001",
                "student_id": "abc123",
                "book_id": "book-42",
                "current_page": 1,
                "sample_rate": 16000,
                "status": "active"
            }
        }
