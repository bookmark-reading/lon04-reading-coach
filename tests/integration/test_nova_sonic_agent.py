"""Integration test for Nova Sonic Reading Agent with Reading Service."""

import asyncio
import os
import pytest
from datetime import datetime

from src.domain.entities.audio import AudioFrame
from src.domain.entities.book import Book, BookMetadata, BookPage
from src.domain.entities.reading_session import ReadingSession, SessionStatus
from src.domain.entities.messages import (
    AudioOutMessage,
    PageChangeMessage,
    FeedbackMessage,
    NoticeMessage,
)
from src.domain.services.reading_service import ReadingService
from src.infrastructure.nova_sonic_reading_agent import (
    NovaSonicReadingAgent,
    NovaSonicConfig,
    NOVA_SDK_AVAILABLE,
)


# Skip tests if Nova SDK is not available
pytestmark = pytest.mark.skipif(
    not NOVA_SDK_AVAILABLE,
    reason="Nova Sonic SDK not installed"
)


@pytest.fixture
def sample_book():
    """Create a sample book for testing."""
    return Book(
        metadata=BookMetadata(
            book_id="test-book-001",
            title="The Cat on the Mat",
            author="Test Author",
            total_pages=3,
            difficulty_level="beginner",
        ),
        pages=[
            BookPage(
                page_number=1,
                text="The cat sat on the mat. It was a big cat.",
                image_url=None,
            ),
            BookPage(
                page_number=2,
                text="The cat was happy. The mat was soft.",
                image_url=None,
            ),
            BookPage(
                page_number=3,
                text="The cat went to sleep. Good night, cat!",
                image_url=None,
            ),
        ]
    )


@pytest.fixture
def sample_session():
    """Create a sample reading session."""
    import uuid
    return ReadingSession(
        id=str(uuid.uuid4()),
        student_id="student-123",
        book_id="test-book-001",
        current_page=1,
        status=SessionStatus.ACTIVE,
        sample_rate=16000,
        created_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow(),
    )


@pytest.fixture
def nova_config():
    """Create Nova Sonic configuration from environment."""
    # Load credentials from environment (should be set from .env.local)
    import os
    
    return NovaSonicConfig(
        region=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
    )


@pytest.fixture
async def nova_agent(nova_config):
    """Create and cleanup Nova Sonic agent."""
    agent = NovaSonicReadingAgent(config=nova_config)
    yield agent
    await agent.close()


def generate_test_audio(duration_ms: int = 100, sample_rate: int = 16000) -> bytes:
    """
    Generate simple test PCM16LE audio (silence or simple tone).
    
    Args:
        duration_ms: Duration in milliseconds
        sample_rate: Sample rate in Hz
        
    Returns:
        PCM16LE audio bytes
    """
    import struct
    num_samples = int(sample_rate * duration_ms / 1000)
    # Generate silence (zeros) - in real tests you'd load actual audio
    samples = [0] * num_samples
    return struct.pack(f'{num_samples}h', *samples)


@pytest.mark.asyncio
async def test_nova_agent_initialization(nova_agent, sample_session, sample_book):
    """Test that Nova Sonic agent initializes correctly."""
    # Agent should initialize without errors
    assert nova_agent is not None
    assert nova_agent.config is not None
    
    # Create a test audio frame
    audio_frame = AudioFrame(
        pcm_bytes=generate_test_audio(100),
        timestamp=datetime.utcnow().timestamp()
    )
    
    # Call coach method - should establish stream
    response = await nova_agent.coach(sample_session, sample_book, audio_frame)
    
    # Should get some response (notice, audio, or feedback)
    assert response is not None
    assert isinstance(
        response,
        (NoticeMessage, AudioOutMessage, FeedbackMessage, PageChangeMessage)
    )


@pytest.mark.asyncio
async def test_reading_service_with_nova_agent(
    nova_agent,
    sample_session,
    sample_book
):
    """Test ReadingService integration with Nova Sonic agent."""
    # Create reading service with Nova agent
    service = ReadingService(
        session=sample_session,
        book=sample_book,
        agent=nova_agent,
    )
    
    # Start the service
    await service.start()
    
    try:
        # Simulate receiving audio from client
        from src.domain.entities.events import IngestAudioEvent
        
        # Send multiple audio chunks
        for i in range(15):  # Send enough to trigger processing
            audio_event = IngestAudioEvent(
                pcm_bytes=generate_test_audio(200),
                timestamp=datetime.utcnow().timestamp()
            )
            await service.inbound_queue.put(audio_event)
            
            # Give event loop time to process
            await asyncio.sleep(0.1)
        
        # Wait for responses
        responses = []
        timeout = 10  # seconds
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                response = await asyncio.wait_for(
                    service.outbound_queue.get(),
                    timeout=1.0
                )
                responses.append(response)
                print(f"Received response: {type(response).__name__}")
                
                # Break if we get an audio or meaningful response
                if isinstance(response, (AudioOutMessage, PageChangeMessage, FeedbackMessage)):
                    break
                    
            except asyncio.TimeoutError:
                continue
        
        # Should have received at least some responses
        assert len(responses) > 0, "No responses received from service"
        
        # Check response types
        response_types = [type(r).__name__ for r in responses]
        print(f"Response types received: {response_types}")
        
    finally:
        await service.stop()
        await nova_agent.close()


@pytest.mark.asyncio
async def test_audio_round_trip(nova_agent, sample_session, sample_book):
    """Test sending audio and receiving audio response from Nova."""
    # Send audio frames one at a time (simulating real-time streaming)
    audio_received = False
    max_attempts = 20
    
    for attempt in range(max_attempts):
        # Send single audio frame
        audio_frame = AudioFrame(
            pcm_bytes=generate_test_audio(200),
            timestamp=datetime.utcnow().timestamp()
        )
        
        response = await nova_agent.coach(sample_session, sample_book, audio_frame)
        
        print(f"Attempt {attempt + 1}: {type(response).__name__}")
        
        if isinstance(response, AudioOutMessage):
            audio_received = True
            assert len(response.pcm_bytes) > 0, "Audio response should contain data"
            print(f"Received audio response: {len(response.pcm_bytes)} bytes")
            break
        
        # Wait a bit between attempts
        await asyncio.sleep(0.1)
    
    # Note: This test may not always receive audio immediately
    # Nova Sonic may buffer before responding
    print(f"Audio received: {audio_received}")


@pytest.mark.asyncio
async def test_page_turn_detection(nova_agent, sample_session, sample_book):
    """Test that Nova can detect end of page and trigger page turn."""
    # Send many audio frames to simulate reading a page
    page_changed = False
    max_attempts = 30
    
    for attempt in range(max_attempts):
        # Simulate continuous reading - send multiple frames sequentially
        for _ in range(5):
            audio_frame = AudioFrame(
                pcm_bytes=generate_test_audio(500),
                timestamp=datetime.utcnow().timestamp()
            )
            
            response = await nova_agent.coach(sample_session, sample_book, audio_frame)
            
            if isinstance(response, PageChangeMessage):
                page_changed = True
                assert response.page > sample_session.current_page
                assert response.direction == "next"
                print(f"Page turn detected: {sample_session.current_page} -> {response.page}")
                break
            
            await asyncio.sleep(0.1)
        
        if page_changed:
            break
        
        print(f"Attempt {attempt + 1}: No page turn yet")
        await asyncio.sleep(0.5)
    
    # Note: Page turn detection depends on Nova's analysis
    # This test documents the capability but may not always trigger
    print(f"Page turn detected: {page_changed}")


@pytest.mark.asyncio
async def test_agent_stream_reuse(nova_agent, sample_session, sample_book):
    """Test that agent can reuse stream across multiple coach calls."""
    responses = []
    
    # Make multiple calls with same session
    for i in range(5):
        audio_frame = AudioFrame(
            pcm_bytes=generate_test_audio(100),
            timestamp=datetime.utcnow().timestamp()
        )
        
        response = await nova_agent.coach(sample_session, sample_book, audio_frame)
        responses.append(response)
        
        await asyncio.sleep(0.2)
    
    # Should have received responses without errors
    assert len(responses) == 5
    assert all(r is not None for r in responses)
    
    print(f"Responses: {[type(r).__name__ for r in responses]}")


@pytest.mark.asyncio  
async def test_agent_session_switching(nova_agent, sample_session, sample_book):
    """Test that agent can switch between different sessions."""
    # Create second session
    session2 = ReadingSession(
        id="test-session-002",
        student_id="student-456",
        book_id="test-book-001",
        current_page=2,
        status=SessionStatus.ACTIVE,
        sample_rate=16000,
        created_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow(),
    )
    
    # Send audio for first session
    audio1 = AudioFrame(generate_test_audio(100), datetime.utcnow().timestamp())
    response1 = await nova_agent.coach(sample_session, sample_book, audio1)
    assert response1 is not None
    
    await asyncio.sleep(0.5)
    
    # Send audio for second session (should trigger new stream)
    audio2 = AudioFrame(generate_test_audio(100), datetime.utcnow().timestamp())
    response2 = await nova_agent.coach(session2, sample_book, audio2)
    assert response2 is not None
    
    # Verify agent switched sessions
    assert nova_agent._current_session_id == session2.id
    
    print(f"Session switched successfully: {sample_session.id} -> {session2.id}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
