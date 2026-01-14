"""Outbound message entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional

from .websocket_messages import (
    ErrorCode,
    ErrorMessage,
    PageChange,
    ResponseFeedback,
    ServerNotice,
    SessionEnded,
)


class OutboundMessage:
    """Base class for outbound messages."""
    
    pass


@dataclass
class AudioOutMessage(OutboundMessage):
    """Message containing audio output."""
    
    pcm_bytes: bytes
    timestamp: float = field(default_factory=lambda: datetime.utcnow().timestamp())


@dataclass
class NoticeMessage(OutboundMessage):
    """Message containing a notice."""
    
    message: str
    notice: ServerNotice = field(init=False)
    
    def __post_init__(self):
        self.notice = ServerNotice(message=self.message)


@dataclass
class ErrorOutMessage(OutboundMessage):
    """Message containing an error."""
    
    code: ErrorCode
    message: str
    error: ErrorMessage = field(init=False)
    
    def __post_init__(self):
        self.error = ErrorMessage(code=self.code, message=self.message)


@dataclass
class PageChangeMessage(OutboundMessage):
    """Message containing a page change instruction."""
    
    page: int
    direction: Optional[Literal["next", "prev"]] = None
    page_change: PageChange = field(init=False)
    
    def __post_init__(self):
        self.page_change = PageChange(page=self.page, direction=self.direction)


@dataclass
class FeedbackMessage(OutboundMessage):
    """Message containing feedback."""
    
    message: str
    feedback_type: Literal["positive", "corrective", "encouragement"] = "positive"
    highlight_text: Optional[str] = None
    feedback: ResponseFeedback = field(init=False)
    
    def __post_init__(self):
        self.feedback = ResponseFeedback(
            message=self.message,
            feedback_type=self.feedback_type,
            highlight_text=self.highlight_text,
        )


@dataclass
class SessionEndedMessage(OutboundMessage):
    """Message indicating session has ended."""
    
    reason: str
    session_summary: Optional[str] = None
    session_ended: SessionEnded = field(init=False)
    
    def __post_init__(self):
        self.session_ended = SessionEnded(
            reason=self.reason,
            session_summary=self.session_summary,
        )


@dataclass
class SessionReadyMessage(OutboundMessage):
    """Message indicating session is ready to accept events."""
    
    session_id: str
    book_id: str
    current_page: int
