import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from src.domain.entities import ReadingSession, Book, AudioFrame, OutboundMessage, \
    AudioOutMessage, TextMessage, NoticeMessage, ErrorOutMessage, ErrorCode

logger = logging.getLogger(__name__)

# Check if Nova Sonic SDK is available
try:
    from src.infrastructure.nova_sonic import NovaSonic
    NOVA_SDK_AVAILABLE = True
    logger.info("✅ Real Nova Sonic SDK loaded")
except ImportError:
    # Use mock implementation
    from src.infrastructure.nova_sonic_mock import NovaSonic
    NOVA_SDK_AVAILABLE = True
    logger.info("🎭 Using MOCK Nova Sonic implementation")


@dataclass
class NovaSonicConfig:
    """Configuration for Nova Sonic reading agent."""
    region: str = 'us-east-1'
    model_id: str = 'amazon.nova-sonic-v1:0'
    max_tokens: int = 1024
    temperature: float = 0.7
    top_p: float = 0.9
    sample_rate_hz: int = 16000
    channels: int = 1
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None


class NovaSonicReadingAgent:
    """Adapter that implements ReadingAgent protocol using NovaSonic."""

    def __init__(self, config: Optional[NovaSonicConfig] = None, 
                 region: str = 'us-east-1', 
                 model_id: str = 'amazon.nova-sonic-v1:0'):
        """Initialize Nova Sonic reading agent.
        
        Args:
            config: Optional configuration object. If provided, overrides other parameters.
            region: AWS region (used if config is None)
            model_id: Nova Sonic model ID (used if config is None)
        """
        if config:
            self.region = config.region
            self.model_id = config.model_id
            self.config = config
        else:
            self.region = region
            self.model_id = model_id
            self.config = NovaSonicConfig(region=region, model_id=model_id)
        
        self._sessions: Dict[UUID, NovaSonic] = {}
        self._initialization_locks: Dict[UUID, asyncio.Lock] = {}
        self._initialization_tasks: Dict[UUID, asyncio.Task] = {}

    async def coach(
        self,
        session: ReadingSession,
        book: Book,
        audio_frame: AudioFrame
    ) -> OutboundMessage:
        """Process audio frame and return response."""
        logging.info(f"NovaSonicReadingAgent.coach called for session {session.id}")
        try:
            # Get or create Nova Sonic instance for this session
            nova = await self._get_or_create_session(session, book)

            # Send the audio frame
            logging.info(f"Sending {len(audio_frame.pcm_bytes)} bytes to Nova Sonic")
            await nova.send_audio_chunk(audio_frame.pcm_bytes)

            # Yield control to allow other tasks to run
            await asyncio.sleep(0)

            # Try to get text response first (faster)
            try:
                text = await asyncio.wait_for(
                    nova.get_text_output(),
                    timeout=0.1  # 100ms timeout for text
                )
                logging.info(f"Got text response: {text}")
                return TextMessage(
                    text=text,
                    timestamp=datetime.now().timestamp()
                )
            except asyncio.TimeoutError:
                logging.debug(f"No text response yet")
                pass  # No text yet, try audio

            # Try to get audio response with timeout
            try:
                audio_bytes = await asyncio.wait_for(
                    nova.get_audio_output(),
                    timeout=0.5  # 500ms timeout
                )
                logging.info(f"Got audio response: {len(audio_bytes)} bytes")
                return AudioOutMessage(
                    pcm_bytes=audio_bytes,
                    timestamp=datetime.now().timestamp()
                )
            except asyncio.TimeoutError:
                logging.debug(f"No audio response yet")
                # No response yet - return None to avoid flooding with messages
                return None

        except Exception as e:
            logging.error(f"Error in coach method: {e}")
            return ErrorOutMessage(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Error processing audio: {str(e)}"
            )

    async def close(self):
        """Close all active sessions and cleanup resources."""
        for session_id, nova in list(self._sessions.items()):
            try:
                await nova.close_session()
            except Exception as e:
                logging.error(f"Error closing session {session_id}: {e}")
        
        self._sessions.clear()
        self._initialization_locks.clear()

    async def _get_or_create_session(self, session: ReadingSession, book: Book) -> NovaSonic:
        """Get existing NovaSonic instance or create new one for session."""
        session_id = session.id

        # Return existing session if available and initialized
        if session_id in self._sessions:
            return self._sessions[session_id]

        # Create lock for this session if it doesn't exist
        if session_id not in self._initialization_locks:
            self._initialization_locks[session_id] = asyncio.Lock()

        # Use lock to prevent multiple initializations
        async with self._initialization_locks[session_id]:
            # Check again in case another task initialized while we waited
            if session_id in self._sessions:
                return self._sessions[session_id]

            # Create new NovaSonic instance
            nova = NovaSonic(model_id=self.model_id, region=self.region)

            # Generate system prompt with book context
            system_prompt = self._generate_system_prompt(session, book)

            # Initialize the session (this starts the stream and response processor)
            await nova.start_session(system_prompt=system_prompt)

            # Start audio input stream
            await nova.start_audio_input()

            # Store the session
            self._sessions[session_id] = nova

            return nova

    def _generate_system_prompt(self, session: ReadingSession, book: Book) -> str:
        """Generate reading coach system prompt with book context."""
        current_page = session.current_page
        page_text = ""

        # Get current page text if available
        if book.pages and 0 < current_page <= len(book.pages):
            page_text = book.pages[current_page - 1].text

        prompt = (
            f"You are an encouraging reading coach helping a student read '{book.metadata.title}'. "
            f"The student is on page {current_page} of {book.metadata.total_pages}. "
            f"Listen to them read and provide brief, supportive feedback. "
            f"Keep responses very short - one sentence. "
            f"Encourage them when they're doing well and gently help when they struggle. "
        )

        if page_text:
            prompt += f"The current page text is: '{page_text[:200]}...' "

        return prompt

    async def close_session(self, session_id: UUID):
        """Close and cleanup a session."""
        if session_id in self._sessions:
            nova = self._sessions[session_id]
            try:
                await nova.end_audio_input()
                await nova.end_session()
                nova.is_active = False

                # Cancel response task
                if nova.response_task and not nova.response_task.done():
                    nova.response_task.cancel()
                    try:
                        await nova.response_task
                    except asyncio.CancelledError:
                        pass
            except Exception as e:
                logging.error(f"Error closing session {session_id}: {e}")
            finally:
                del self._sessions[session_id]
                if session_id in self._initialization_locks:
                    del self._initialization_locks[session_id]
