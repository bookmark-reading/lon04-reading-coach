"""Domain entities for the reading coach application."""

from .audio import AudioFrame
from .book import Book, BookMetadata
from .events import (
    AckEventEvent,
    CloseEvent,
    InboundEvent,
    IngestAudioEvent,
    InitSessionEvent,
    UpdateReaderStateEvent,
)
from .messages import (
    AudioOutMessage,
    ErrorOutMessage,
    NoticeMessage,
    OutboundMessage,
)
from .reading_session import ReadingSession, SessionStatus
from .user_profile import ReadingLevel, UserProfile
from .websocket_messages import (
    ClientMessage,
    ErrorCode,
    ErrorMessage,
    InputAudio,
    PageChange,
    ResponseAudio,
    ResponseFeedback,
    ServerMessage,
    ServerNotice,
    SessionCreate,
    SessionCreated,
    SessionEnded,
)

__all__ = [
    # Session entities
    "ReadingSession",
    "SessionStatus",
    # User profile entities
    "UserProfile",
    "ReadingLevel",
    # Book entities
    "Book",
    "BookMetadata",
    # Audio entities
    "AudioFrame",
    # Event entities
    "InboundEvent",
    "InitSessionEvent",
    "UpdateReaderStateEvent",
    "IngestAudioEvent",
    "AckEventEvent",
    "CloseEvent",
    # Message entities
    "OutboundMessage",
    "AudioOutMessage",
    "NoticeMessage",
    "ErrorOutMessage",
    # WebSocket message entities
    "ClientMessage",
    "ServerMessage",
    "SessionCreate",
    "InputAudio",
    "SessionCreated",
    "ResponseAudio",
    "PageChange",
    "ResponseFeedback",
    "SessionEnded",
    "ServerNotice",
    "ErrorMessage",
    "ErrorCode",
]
