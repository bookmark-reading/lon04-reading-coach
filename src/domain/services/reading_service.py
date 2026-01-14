"""Reading service for managing reading session business logic."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from ..entities.audio import AudioFrame
from ..entities.book import Book
from ..entities.events import (
    AckEventEvent,
    CloseEvent,
    InboundEvent,
    IngestAudioEvent,
    InitSessionEvent,
    UpdateReaderStateEvent,
)
from ..entities.messages import (
    AudioOutMessage,
    ErrorOutMessage,
    FeedbackMessage,
    NoticeMessage,
    OutboundMessage,
    PageChangeMessage,
    SessionEndedMessage,
    SessionReadyMessage,
)
from ..entities.reading_session import ReadingSession, SessionStatus
from ..entities.websocket_messages import (
    ErrorCode,
    PageChange,
)
from ..interfaces.reading_agent import ReadingAgent

logger = logging.getLogger(__name__)


class ReadingService:
    """
    Per-session service that manages all reading session business logic.
    
    This service owns:
    - Session state (page, book_id, timing, last events)
    - Buffering + framing audio
    - Model streaming client integration (placeholder for now)
    - Decisioning/validation for UI actions (turn page rules)
    - Emitting events to the WebSocket layer via async queue
    
    The service is unit-testable without sockets.
    """
    
    def __init__(
        self,
        session: ReadingSession,
        book: Book,
        agent: ReadingAgent,
    ):
        self.session: ReadingSession = session
        self.book = book
        self.reading_agent = agent

        # Asyncio queues for communication
        self.inbound_queue: asyncio.Queue[InboundEvent] = asyncio.Queue()
        self.outbound_queue: asyncio.Queue[OutboundMessage] = asyncio.Queue()
        
        # Audio buffering
        self.audio_buffer: list[AudioFrame] = []
        self.audio_frame_size: int = 1024  # Configurable frame size
        
        # Event tracking (for page changes and feedback)
        self.pending_events: dict[str, PageChange] = {}
        self.last_events: list = []
        self.max_event_history: int = 100
        self._event_id_counter: int = 0
        
        # Service state
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        logger.info(f"ReadingService created for session {session.id}")
    
    async def start(self):
        """Start the reading service event loop and emit session ready message."""
        if self._running:
            logger.warning(f"Service {self.session.id} already running")
            return
        
        self._running = True
        
        # Update session status
        self.session.status = SessionStatus.ACTIVE
        self.session.last_activity_at = datetime.utcnow()
        
        # Start the event processing task
        self._task = asyncio.create_task(self._process_inbound_events())
        
        # Emit session ready message
        await self._emit_session_ready()
        
        logger.info(f"ReadingService {self.session.id} started")

    async def pause(self):
        """Pause the reading service event loop."""
        if not self._running:
            return

        self._running = False
        
        # Update session status
        self.session.status = SessionStatus.PAUSED
        self.session.last_activity_at = datetime.utcnow()

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info(f"ReadingService {self.session.id} paused")

    async def stop(self):
        """Stop the reading service event loop."""
        if not self._running:
            return
        
        self._running = False
        
        # Update session status
        self.session.status = SessionStatus.COMPLETED
        self.session.last_activity_at = datetime.utcnow()
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"ReadingService {self.session.id} stopped")
    
    async def _process_inbound_events(self):
        """Main event processing loop."""
        logger.info(f"Event processing started for session {self.session.id}")
        
        try:
            while self._running:
                try:
                    # Wait for inbound events with timeout to allow periodic checks
                    event = await asyncio.wait_for(
                        self.inbound_queue.get(),
                        timeout=1.0
                    )
                    await self._handle_event(event)
                except asyncio.TimeoutError:
                    # No event received, continue loop
                    continue
                except Exception as e:
                    logger.error(f"Error processing event: {e}", exc_info=True)
                    await self._emit_error(
                        ErrorCode.INTERNAL_ERROR,
                        f"Internal processing error: {str(e)}"
                    )
        finally:
            logger.info(f"Event processing ended for session {self.session.id}")
    
    async def _handle_event(self, event: InboundEvent):
        """Route event to appropriate handler based on type."""
        if isinstance(event, InitSessionEvent):
            await self._handle_init_session(event)
        elif isinstance(event, UpdateReaderStateEvent):
            await self._handle_update_reader_state(event)
        elif isinstance(event, IngestAudioEvent):
            await self._handle_ingest_audio(event)
        elif isinstance(event, AckEventEvent):
            await self._handle_ack_event(event)
        elif isinstance(event, CloseEvent):
            await self._handle_close()
        else:
            logger.warning(f"Unknown event type: {type(event)}")
    
    # ===== Event Handlers =====
    
    async def _handle_init_session(self, event: InitSessionEvent):
        """Handle session initialization."""
        logger.info(
            f"Initializing session {self.session.id} for student {event.student_id}, "
            f"book {event.book_id}, page {event.current_page}"
        )
        
        # Update session with initialization data
        self.session.student_id = event.student_id
        self.session.book_id = event.book_id
        self.session.current_page = event.current_page
        self.session.sample_rate = event.sample_rate
        self.session.status = SessionStatus.ACTIVE
        self.session.last_activity_at = datetime.utcnow()
        
        await self._emit_session_ready()
    
    async def _handle_update_reader_state(self, event: UpdateReaderStateEvent):
        """Handle reader state update."""
        logger.info(f"Updating reader state: page {event.current_page}")
        
        # Update session state
        old_page = self.session.current_page
        self.session.current_page = event.current_page
        self.session.last_activity_at = datetime.utcnow()
        
        # If page changed, log it
        if old_page != event.current_page:
            logger.info(f"Page changed from {old_page} to {event.current_page}")
    
    async def _handle_ingest_audio(self, event: IngestAudioEvent):
        """Handle incoming audio data."""
        # Create audio frame
        frame = AudioFrame(event.pcm_bytes, event.timestamp)
        self.audio_buffer.append(frame)
        
        # Log audio receipt for verification
        logger.debug(
            f"Session {self.session.id}: Received audio chunk "
            f"({len(event.pcm_bytes)} bytes, buffer size: {len(self.audio_buffer)} frames)"
        )
        
        # Process audio if buffer is large enough
        if len(self.audio_buffer) >= 10:  # Example threshold
            await self._process_audio_buffer()
    
    async def _process_audio_buffer(self):
        """
        Process buffered audio data.
        
        The reading agent analyzes the audio and decides on appropriate responses,
        including page changes. The agent has full control over which page to navigate to
        (next, previous, or jump to any specific page number).
        """
        # Keep buffer manageable (last 50 frames)
        if len(self.audio_buffer) > 50:
            self.audio_buffer = self.audio_buffer[-50:]
        
        # Get agent decision on what to do with the audio
        # Agent can return: PageChangeMessage, FeedbackMessage, AudioOutMessage, NoticeMessage, etc.
        agent_response = await self.reading_agent.coach(
            session=self.session,
            book=self.book,
            audio=self.audio_buffer
        )
        
        # If agent decided to change pages, update session state
        if isinstance(agent_response, PageChangeMessage):
            target_page = agent_response.page
            
            # Only validate that page is within book bounds
            if 1 <= target_page <= self.book.metadata.total_pages:
                old_page = self.session.current_page
                self.session.current_page = target_page
                self.session.last_activity_at = datetime.utcnow()
                
                logger.info(
                    f"Page change: {old_page} → {target_page} (agent decision)"
                )
                
                # Set event ID for acknowledgement tracking
                self._event_id_counter += 1
                event_id = f"{self.session.id}-evt-{self._event_id_counter}"
                agent_response.page_change.event_id = event_id
                self.pending_events[event_id] = agent_response.page_change
            else:
                logger.warning(
                    f"Agent requested invalid page {target_page}, "
                    f"valid range: 1-{self.book.metadata.total_pages}. Ignoring request."
                )
                # Don't send invalid page change
                return
        
        # Send the agent's response to the client
        await self.outbound_queue.put(agent_response)

    async def _handle_ack_event(self, event: AckEventEvent):
        """Handle client acknowledgement of a UI event."""
        logger.info(f"Received ack for event {event.event_id}: {event.status}")
        
        # Remove from pending events
        ui_event = self.pending_events.pop(event.event_id, None)
        
        if ui_event:
            # Add to history
            self.last_events.append(ui_event)
            if len(self.last_events) > self.max_event_history:
                self.last_events = self.last_events[-self.max_event_history:]
            
            if event.status == "error":
                logger.warning(f"Client reported error for event {event.event_id}")
        else:
            logger.warning(f"Received ack for unknown event {event.event_id}")
    
    async def _handle_close(self):
        """Handle session close."""
        logger.info(f"Closing session {self.session.id}")
        
        self.session.status = SessionStatus.COMPLETED
        
        await self._emit_notice("Session closed")
        await self.stop()
    
    # ===== Public API methods (called by WebSocket handler) =====
    
    async def init_session(
        self,
        student_id: str,
        book_id: str,
        current_page: int,
        sample_rate: int
    ):
        """
        Initialize a reading session.
        
        Args:
            student_id: Student identifier
            book_id: Book identifier
            current_page: Starting page number
            sample_rate: Audio sample rate in Hz
        """
        event = InitSessionEvent(student_id, book_id, current_page, sample_rate)
        await self.inbound_queue.put(event)
    
    async def update_reader_state(self, current_page: int, visible_text: str):
        """
        Update the current reader state.
        
        Args:
            current_page: Current page number
            visible_text: Currently visible text on the page
        """
        event = UpdateReaderStateEvent(current_page, visible_text)
        await self.inbound_queue.put(event)
    
    async def ingest_audio(self, pcm_bytes: bytes, timestamp: float):
        """
        Ingest audio data from the microphone.
        
        Args:
            pcm_bytes: PCM audio bytes
            timestamp: Timestamp of the audio data
        """
        event = IngestAudioEvent(pcm_bytes, timestamp)
        await self.inbound_queue.put(event)
    
    async def ack_event(self, event_id: str, status: str):
        """
        Acknowledge a UI event from the client.
        
        Args:
            event_id: Event identifier
            status: Acknowledgement status ("ok" or "error")
        """
        event = AckEventEvent(event_id, status)
        await self.inbound_queue.put(event)
    
    async def close(self):
        """Close the reading session."""
        event = CloseEvent()
        await self.inbound_queue.put(event)
    
    # ===== Outbound message helpers =====
    
    async def _emit_session_ready(self):
        """Emit session ready message to the client."""
        message = SessionReadyMessage(
            session_id=str(self.session.id),
            book_id=self.session.book_id,
            current_page=self.session.current_page
        )
        await self.outbound_queue.put(message)
        logger.info(f"Emitted session ready for session {self.session.id}")
    
    async def _emit_audio(self, pcm_bytes: bytes, timestamp: Optional[float] = None):
        """Emit audio output to the client."""
        message = AudioOutMessage(pcm_bytes, timestamp)
        await self.outbound_queue.put(message)
    
    async def _emit_page_change(self, page: int, direction: Optional[str] = None):
        """Emit a page change event to the client."""
        # Generate unique event ID
        self._event_id_counter += 1
        event_id = f"{self.session.id}-evt-{self._event_id_counter}"
        
        # Create page change with event ID
        message = PageChangeMessage(page=page, direction=direction)
        message.page_change.event_id = event_id
        
        # Store in pending events for acknowledgement tracking
        self.pending_events[event_id] = message.page_change
        
        await self.outbound_queue.put(message)
        logger.info(f"Emitted page change to page {page} with event_id {event_id}")
    
    async def _emit_feedback(
        self, 
        message: str, 
        feedback_type: str = "positive",
        highlight_text: Optional[str] = None
    ):
        """Emit feedback to the client."""
        feedback_msg = FeedbackMessage(
            message=message,
            feedback_type=feedback_type,
            highlight_text=highlight_text
        )
        await self.outbound_queue.put(feedback_msg)
        logger.info(f"Emitted feedback: {feedback_type}")
    
    async def _emit_notice(self, text: str):
        """Emit a notice message to the client."""
        message = NoticeMessage(text)
        await self.outbound_queue.put(message)
    
    async def _emit_error(self, code: ErrorCode, text: str):
        """Emit an error message to the client."""
        message = ErrorOutMessage(code, text)
        await self.outbound_queue.put(message)
    
    async def _emit_session_ended(self, reason: str, session_summary: Optional[str] = None):
        """Emit a session ended message to the client."""
        message = SessionEndedMessage(reason=reason, session_summary=session_summary)
        await self.outbound_queue.put(message)
        logger.info(f"Emitted session ended: {reason}")
    
    # ===== Business logic methods =====
    
    async def request_page_turn(self, direction: str = "next") -> bool:
        """
        Request a page turn (with validation).
        
        Args:
            direction: "next" or "prev"
        
        Returns:
            True if the request is valid and sent, False otherwise
        """
        # Validation: check if page turn is allowed
        if direction == "prev" and self.session.current_page <= 1:
            logger.warning("Cannot turn to previous page: already on first page")
            await self._emit_notice("Already on first page")
            return False
        
        if direction == "next" and self.session.current_page >= self.book.metadata.total_pages:
            logger.warning("Cannot turn to next page: already on last page")
            await self._emit_notice("Already on last page")
            return False
        
        # Calculate new page number
        new_page = self.session.current_page
        if direction == "next":
            new_page += 1
        elif direction == "prev":
            new_page -= 1
        
        # Update session state
        self.session.current_page = new_page
        self.session.last_activity_at = datetime.utcnow()
        
        # Emit page change event
        await self._emit_page_change(new_page, direction)
        
        return True
    
    def get_session_state(self) -> dict:
        """Get the current session state as a dictionary.
        
        Returns:
            Dictionary representation of session state
        """
        return {
            "session_id": str(self.session.id),
            "student_id": self.session.student_id,
            "book_id": self.session.book_id,
            "current_page": self.session.current_page,
            "status": self.session.status.value if hasattr(self.session.status, 'value') else str(self.session.status),
            "sample_rate": self.session.sample_rate,
            "audio_buffer_size": len(self.audio_buffer),
            "pending_events": len(self.pending_events),
            "last_activity": self.session.last_activity_at.isoformat() if self.session.last_activity_at else None,
        }
