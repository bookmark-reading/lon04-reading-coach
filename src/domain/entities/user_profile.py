"""User profile entities for the reading coach application."""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ReadingLevel(int, Enum):
    """Reading proficiency levels."""
    
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5
    LEVEL_6 = 6
    LEVEL_7 = 7


class UserProfile(BaseModel):
    """User profile entity containing user information and reading preferences."""
    
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    current_reading_level: int = Field(ge=1, le=7, description="Current reading level (1-7)")
    sessions: list[UUID] = Field(default_factory=list, description="List of session IDs from previous sessions")
    
    class Config:
        """Pydantic model configuration."""
        
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "current_reading_level": 5,
                "sessions": ["123e4567-e89b-12d3-a456-426614174000"]
            }
        }
