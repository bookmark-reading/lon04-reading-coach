"""Tests for LocalSessionRepository."""

import pytest
import uuid
from datetime import datetime

from src.domain.entities.reading_session import ReadingSession, SessionStatus
from src.infrastructure.local_session_repository import LocalSessionRepository


@pytest.fixture
def repository():
    """Create a fresh LocalSessionRepository for each test."""
    return LocalSessionRepository()


@pytest.fixture
def sample_session():
    """Create a sample session for testing."""
    test_uuid = uuid.UUID('12345678-1234-5678-1234-567812345678')
    return ReadingSession(
        id=test_uuid,
        student_id="student-456",
        book_id="book-789",
        current_page=1,
        sample_rate=16000,
        status=SessionStatus.ACTIVE,
        started_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow()
    )


@pytest.mark.asyncio
async def test_save_and_get_session(repository, sample_session):
    """Test saving and retrieving a session."""
    await repository.save_session(sample_session)
    retrieved = await repository.get_session(str(sample_session.id))
    
    assert retrieved.id == sample_session.id
    assert retrieved.student_id == sample_session.student_id
    assert retrieved.book_id == sample_session.book_id
    assert retrieved.current_page == sample_session.current_page
    assert retrieved.status == sample_session.status


@pytest.mark.asyncio
async def test_get_nonexistent_session(repository):
    """Test retrieving a session that doesn't exist."""
    with pytest.raises(ValueError, match="Session with id nonexistent not found"):
        await repository.get_session("nonexistent")


@pytest.mark.asyncio
async def test_update_session(repository, sample_session):
    """Test updating an existing session."""
    await repository.save_session(sample_session)
    
    # Modify the session
    updated_session = sample_session.model_copy(update={"current_page": 5})
    await repository.update_session(updated_session)
    
    retrieved = await repository.get_session(str(sample_session.id))
    assert retrieved.current_page == 5


@pytest.mark.asyncio
async def test_update_nonexistent_session(repository, sample_session):
    """Test updating a session that doesn't exist."""
    with pytest.raises(ValueError, match="Session with id .* not found"):
        await repository.update_session(sample_session)


@pytest.mark.asyncio
async def test_delete_session(repository, sample_session):
    """Test deleting a session."""
    await repository.save_session(sample_session)
    await repository.delete_session(str(sample_session.id))
    
    with pytest.raises(ValueError, match="Session with id .* not found"):
        await repository.get_session(str(sample_session.id))


@pytest.mark.asyncio
async def test_delete_nonexistent_session(repository):
    """Test deleting a session that doesn't exist."""
    with pytest.raises(ValueError, match="Session with id nonexistent not found"):
        await repository.delete_session("nonexistent")


def test_clear_sessions(repository):
    """Test clearing all sessions."""
    uuid1 = uuid.UUID('12345678-1234-5678-1234-567812345671')
    uuid2 = uuid.UUID('12345678-1234-5678-1234-567812345672')
    repository._sessions = {
        str(uuid1): ReadingSession(
            id=uuid1, 
            student_id="s1", 
            book_id="b1"
        ),
        str(uuid2): ReadingSession(
            id=uuid2, 
            student_id="s2", 
            book_id="b2"
        ),
    }
    
    repository.clear()
    assert len(repository._sessions) == 0


@pytest.mark.asyncio
async def test_get_all_sessions(repository):
    """Test retrieving all sessions."""
    uuid1 = uuid.UUID('12345678-1234-5678-1234-567812345673')
    uuid2 = uuid.UUID('12345678-1234-5678-1234-567812345674')
    session1 = ReadingSession(
        id=uuid1, 
        student_id="s1", 
        book_id="b1"
    )
    session2 = ReadingSession(
        id=uuid2, 
        student_id="s2", 
        book_id="b2"
    )
    
    await repository.save_session(session1)
    await repository.save_session(session2)
    
    all_sessions = repository.get_all_sessions()
    assert len(all_sessions) == 2
    assert str(uuid1) in all_sessions
    assert str(uuid2) in all_sessions
