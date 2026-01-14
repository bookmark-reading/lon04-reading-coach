"""Tests for pending events tracking in ReadingService."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from src.domain.entities import ReadingSession, Book, BookMetadata
from src.domain.entities.messages import PageChangeMessage
from src.domain.entities.websocket_messages import PageChange
from src.domain.services.reading_service import ReadingService


@pytest.fixture
def mock_agent():
    """Create a mock reading agent."""
    agent = AsyncMock()
    return agent


@pytest.fixture
def test_session():
    """Create a test session."""
    return ReadingSession(
        student_id="test-student-123",
        book_id="test-book-456",
        current_page=1,
        sample_rate=16000
    )


@pytest.fixture
def test_book():
    """Create a test book."""
    metadata = BookMetadata(
        book_id="test-book-456",
        book_name="Test Book",
        reading_level=3,
        total_pages=50,
        path="/test/path"
    )
    return Book(
        book_id="test-book-456",
        file_content=b"test content",
        metadata=metadata
    )


@pytest.fixture
def reading_service(test_session, test_book, mock_agent):
    """Create a reading service for testing."""
    return ReadingService(test_session, test_book, mock_agent)


@pytest.mark.asyncio
async def test_page_change_generates_event_id(reading_service):
    """Test that emitting a page change generates and stores an event ID."""
    await reading_service.start()
    
    try:
        # Clear any existing messages
        while not reading_service.outbound_queue.empty():
            await reading_service.outbound_queue.get()
        
        # Emit a page change
        await reading_service._emit_page_change(page=2, direction="next")
        
        # Should have one pending event
        assert len(reading_service.pending_events) == 1
        
        # Get the event ID
        event_id = list(reading_service.pending_events.keys())[0]
        assert event_id.startswith(f"{reading_service.session.id}-evt-")
        
        # Check the stored PageChange
        page_change = reading_service.pending_events[event_id]
        assert isinstance(page_change, PageChange)
        assert page_change.page == 2
        assert page_change.direction == "next"
        assert page_change.event_id == event_id
        
        # Check the outbound message
        message = await reading_service.outbound_queue.get()
        assert isinstance(message, PageChangeMessage)
        assert message.page_change.page == 2
        assert message.page_change.event_id == event_id
        
    finally:
        await reading_service.stop()


@pytest.mark.asyncio
async def test_event_id_counter_increments(reading_service):
    """Test that event IDs increment for each page change."""
    await reading_service.start()
    
    try:
        # Clear queue
        while not reading_service.outbound_queue.empty():
            await reading_service.outbound_queue.get()
        
        # Emit multiple page changes
        await reading_service._emit_page_change(page=2, direction="next")
        await reading_service._emit_page_change(page=3, direction="next")
        await reading_service._emit_page_change(page=4, direction="next")
        
        # Should have three pending events
        assert len(reading_service.pending_events) == 3
        
        # Check event IDs are sequential
        event_ids = sorted(reading_service.pending_events.keys())
        assert event_ids[0].endswith("-evt-1")
        assert event_ids[1].endswith("-evt-2")
        assert event_ids[2].endswith("-evt-3")
        
    finally:
        await reading_service.stop()


@pytest.mark.asyncio
async def test_ack_event_removes_from_pending(reading_service):
    """Test that acknowledging an event removes it from pending and adds to history."""
    await reading_service.start()
    
    try:
        # Clear queue
        while not reading_service.outbound_queue.empty():
            await reading_service.outbound_queue.get()
        
        # Emit a page change
        await reading_service._emit_page_change(page=2, direction="next")
        
        # Get the event ID
        event_id = list(reading_service.pending_events.keys())[0]
        page_change = reading_service.pending_events[event_id]
        
        # Acknowledge the event
        await reading_service.ack_event(event_id, "ok")
        await asyncio.sleep(0.1)  # Let it process
        
        # Should be removed from pending
        assert event_id not in reading_service.pending_events
        
        # Should be in history
        assert len(reading_service.last_events) == 1
        assert reading_service.last_events[0] == page_change
        
    finally:
        await reading_service.stop()


@pytest.mark.asyncio
async def test_ack_event_with_error_status(reading_service):
    """Test that acknowledging an event with error status is logged."""
    await reading_service.start()
    
    try:
        # Clear queue
        while not reading_service.outbound_queue.empty():
            await reading_service.outbound_queue.get()
        
        # Emit a page change
        await reading_service._emit_page_change(page=2, direction="next")
        
        # Get the event ID
        event_id = list(reading_service.pending_events.keys())[0]
        
        # Acknowledge with error
        await reading_service.ack_event(event_id, "error")
        await asyncio.sleep(0.1)
        
        # Should still be removed from pending
        assert event_id not in reading_service.pending_events
        
        # Should be in history
        assert len(reading_service.last_events) == 1
        
    finally:
        await reading_service.stop()


@pytest.mark.asyncio
async def test_ack_unknown_event_id(reading_service):
    """Test that acknowledging an unknown event ID is handled gracefully."""
    await reading_service.start()
    
    try:
        # Try to ack a non-existent event
        await reading_service.ack_event("unknown-event-id", "ok")
        await asyncio.sleep(0.1)
        
        # Should not crash
        assert len(reading_service.pending_events) == 0
        assert len(reading_service.last_events) == 0
        
    finally:
        await reading_service.stop()


@pytest.mark.asyncio
async def test_multiple_pending_events(reading_service):
    """Test handling multiple pending events at once."""
    await reading_service.start()
    
    try:
        # Clear queue
        while not reading_service.outbound_queue.empty():
            await reading_service.outbound_queue.get()
        
        # Emit multiple page changes without acknowledging
        await reading_service._emit_page_change(page=2, direction="next")
        await reading_service._emit_page_change(page=3, direction="next")
        await reading_service._emit_page_change(page=4, direction="next")
        
        # Should have three pending events
        assert len(reading_service.pending_events) == 3
        
        # Acknowledge them in order
        event_ids = list(reading_service.pending_events.keys())
        for event_id in event_ids:
            await reading_service.ack_event(event_id, "ok")
            await asyncio.sleep(0.05)
        
        # All should be removed from pending
        assert len(reading_service.pending_events) == 0
        
        # All should be in history
        assert len(reading_service.last_events) == 3
        
    finally:
        await reading_service.stop()


@pytest.mark.asyncio
async def test_event_history_limit_with_pending_events(reading_service):
    """Test that event history is limited even with many pending events."""
    reading_service.max_event_history = 5
    await reading_service.start()
    
    try:
        # Clear queue
        while not reading_service.outbound_queue.empty():
            await reading_service.outbound_queue.get()
        
        # Emit and acknowledge many events
        for i in range(10):
            await reading_service._emit_page_change(page=i+2, direction="next")
            event_id = list(reading_service.pending_events.keys())[-1]
            await reading_service.ack_event(event_id, "ok")
            await asyncio.sleep(0.05)
        
        # History should be limited to max
        assert len(reading_service.last_events) == 5
        
        # Check the last 5 are kept
        for i, page_change in enumerate(reading_service.last_events):
            # Should be pages 7-11 (last 5 of 10)
            assert page_change.page == i + 7
        
    finally:
        await reading_service.stop()


@pytest.mark.asyncio
async def test_request_page_turn_creates_pending_event(reading_service):
    """Test that request_page_turn creates a pending event."""
    await reading_service.start()
    
    try:
        # Clear queue
        while not reading_service.outbound_queue.empty():
            await reading_service.outbound_queue.get()
        
        # Request page turn
        result = await reading_service.request_page_turn("next")
        assert result is True
        
        # Should have one pending event
        assert len(reading_service.pending_events) == 1
        
        # Get the event
        event_id = list(reading_service.pending_events.keys())[0]
        page_change = reading_service.pending_events[event_id]
        assert page_change.page == 2  # From page 1 to 2
        assert page_change.direction == "next"
        
    finally:
        await reading_service.stop()


@pytest.mark.asyncio
async def test_get_session_state_includes_pending_events_count(reading_service):
    """Test that session state includes pending events count."""
    await reading_service.start()
    
    try:
        # Clear queue
        while not reading_service.outbound_queue.empty():
            await reading_service.outbound_queue.get()
        
        # Emit some page changes
        await reading_service._emit_page_change(page=2, direction="next")
        await reading_service._emit_page_change(page=3, direction="next")
        
        # Get session state
        state = reading_service.get_session_state()
        
        assert "pending_events" in state
        assert state["pending_events"] == 2
        
    finally:
        await reading_service.stop()


@pytest.mark.asyncio
async def test_pending_events_cleared_on_service_restart(test_session, test_book, mock_agent):
    """Test that pending events are cleared when service is stopped and restarted."""
    service = ReadingService(test_session, test_book, mock_agent)
    
    await service.start()
    
    try:
        # Clear queue
        while not service.outbound_queue.empty():
            await service.outbound_queue.get()
        
        # Emit page changes
        await service._emit_page_change(page=2, direction="next")
        await service._emit_page_change(page=3, direction="next")
        
        assert len(service.pending_events) == 2
        
    finally:
        await service.stop()
    
    # Pending events persist after stop (they're just in memory)
    assert len(service.pending_events) == 2
    
    # But counter should still work after restart
    await service.start()
    try:
        await service._emit_page_change(page=4, direction="next")
        
        # Counter continues from where it left off
        event_ids = list(service.pending_events.keys())
        assert any("evt-3" in eid for eid in event_ids)
        
    finally:
        await service.stop()
