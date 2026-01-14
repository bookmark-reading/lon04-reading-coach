"""WebSocket message models for the reading coach application."""

from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


# ===== Client → Server Messages =====


class SessionCreate(BaseModel):
    """Session initialization message from client."""
    
    type: Literal["session.create"] = "session.create"
    student_id: str
    book_id: str
    current_page: int = Field(ge=1)
    sample_rate: int = Field(default=16000)


class InputAudio(BaseModel):
    """Audio data from client (binary audio will be sent separately)."""
    
    type: Literal["input_audio"] = "input_audio"
    # Audio chunk sent as binary WebSocket frame


# Union type for all client messages
ClientMessage = Union[SessionCreate, InputAudio]


# ===== Server → Client Messages =====


class SessionCreated(BaseModel):
    """Session created confirmation from server."""
    
    type: Literal["session.created"] = "session.created"
    session_id: str


class ResponseAudio(BaseModel):
    """Audio response from server (binary audio will be sent separately)."""
    
    type: Literal["response.audio"] = "response.audio"
    # Audio will be sent as binary WebSocket frame


class PageChange(BaseModel):
    """Page change instruction from server."""
    
    type: Literal["page.change"] = "page.change"
    page: int = Field(ge=1)
    direction: Optional[Literal["next", "prev"]] = None
    event_id: Optional[str] = Field(default=None, description="Unique event identifier for acknowledgement tracking")


class ResponseFeedback(BaseModel):
    """Feedback message from server."""
    
    type: Literal["response.feedback"] = "response.feedback"
    message: str
    feedback_type: Literal["positive", "corrective", "encouragement"] = "positive"
    highlight_text: Optional[str] = None


class SessionEnded(BaseModel):
    """Session ended message from server."""
    
    type: Literal["session.ended"] = "session.ended"
    reason: str
    session_summary: Optional[str] = None


class ServerNotice(BaseModel):
    """Server notice message."""
    
    type: Literal["server_notice"] = "server_notice"
    message: str


class ErrorCode(str, Enum):
    """Error codes for WebSocket errors."""
    
    INVALID_MESSAGE = "INVALID_MESSAGE"
    INVALID_PAGE = "INVALID_PAGE"
    AUTH_FAILED = "AUTH_FAILED"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorMessage(BaseModel):
    """Error message from server."""
    
    type: Literal["error"] = "error"
    code: ErrorCode
    message: str


# Union type for all server messages
ServerMessage = Union[SessionCreated, ResponseAudio, PageChange, ResponseFeedback, SessionEnded, ServerNotice, ErrorMessage]
