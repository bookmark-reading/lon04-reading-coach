"""Event entities for reading sessions."""

from dataclasses import dataclass


class InboundEvent:
    """Base class for inbound events."""
    
    pass


@dataclass
class InitSessionEvent(InboundEvent):
    """Event to initialize a session."""
    
    student_id: str
    book_id: str
    current_page: int
    sample_rate: int


@dataclass
class UpdateReaderStateEvent(InboundEvent):
    """Event to update reader state."""
    
    current_page: int
    visible_text: str


@dataclass
class IngestAudioEvent(InboundEvent):
    """Event to ingest audio data."""
    
    pcm_bytes: bytes
    timestamp: float


@dataclass
class AckEventEvent(InboundEvent):
    """Event to acknowledge a UI event."""
    
    event_id: str
    status: str


@dataclass
class CloseEvent(InboundEvent):
    """Event to close the session."""
    
    pass
