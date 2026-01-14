"""Unit tests for session entities."""

import pytest
import uuid
from datetime import datetime

from src.domain.entities import ReadingSession, SessionStatus


class TestSessionStatus:
    """Tests for SessionStatus enum."""
    
    def test_session_status_values(self):
        """Test that session statuses have correct string values."""
        assert SessionStatus.READY.value == "ready"
        assert SessionStatus.INITIALIZING.value == "initializing"
        assert SessionStatus.ACTIVE.value == "active"
        assert SessionStatus.PAUSED.value == "paused"
        assert SessionStatus.COMPLETED.value == "completed"
        assert SessionStatus.ERROR.value == "error"
    
    def test_session_status_count(self):
        """Test that there are exactly 6 session statuses."""
        assert len(SessionStatus) == 6


class TestSession:
    """Tests for Session entity."""
    
    def test_session_creation_minimal(self):
        """Test creating a session with minimal required fields."""
        session = ReadingSession(
            student_id="student-123",
            book_id="book-456"
        )
        
        assert session.id is not None
        assert session.student_id == "student-123"
        assert session.book_id == "book-456"
        assert session.current_page == 1
        assert session.sample_rate == 16000
        assert session.status == SessionStatus.INITIALIZING
        assert isinstance(session.started_at, datetime)
        assert isinstance(session.last_activity_at, datetime)
    
    def test_session_creation_with_all_fields(self):
        """Test creating a session with all fields."""
        start_time = datetime(2026, 1, 13, 10, 0, 0)
        last_activity = datetime(2026, 1, 13, 10, 30, 0)
        test_uuid = uuid.UUID('12345678-1234-5678-1234-567812345678')
        
        session = ReadingSession(
            id=test_uuid,
            student_id="student-456",
            book_id="book-789",
            current_page=5,
            sample_rate=44100,
            status=SessionStatus.ACTIVE,
            started_at=start_time,
            last_activity_at=last_activity
        )
        
        assert session.id == test_uuid
        assert session.student_id == "student-456"
        assert session.book_id == "book-789"
        assert session.current_page == 5
        assert session.sample_rate == 44100
        assert session.status == SessionStatus.ACTIVE
        assert session.started_at == start_time
        assert session.last_activity_at == last_activity
    
    def test_session_validation_current_page_minimum(self):
        """Test that current_page must be at least 1."""
        with pytest.raises(Exception):  # Pydantic validation error
            ReadingSession(
                student_id="student-789",
                book_id="book-012",
                current_page=0
            )
    
    def test_session_validation_current_page_negative(self):
        """Test that current_page cannot be negative."""
        with pytest.raises(Exception):  # Pydantic validation error
            ReadingSession(
                student_id="student-789",
                book_id="book-012",
                current_page=-1
            )
    
    def test_session_status_transitions(self):
        """Test updating session status."""
        session = ReadingSession(
            student_id="student-100",
            book_id="book-200"
        )
        
        assert session.status == SessionStatus.INITIALIZING
        
        session.status = SessionStatus.ACTIVE
        assert session.status == SessionStatus.ACTIVE
        
        session.status = SessionStatus.PAUSED
        assert session.status == SessionStatus.PAUSED
        
        session.status = SessionStatus.COMPLETED
        assert session.status == SessionStatus.COMPLETED
    
    def test_session_page_progression(self):
        """Test updating current page."""
        session = ReadingSession(
            student_id="student-300",
            book_id="book-400"
        )
        
        assert session.current_page == 1
        
        session.current_page = 10
        assert session.current_page == 10
        
        session.current_page = 50
        assert session.current_page == 50
    
    def test_session_serialization(self):
        """Test that session can be serialized to dict."""
        test_uuid = uuid.UUID('12345678-1234-5678-1234-567812345679')
        session = ReadingSession(
            id=test_uuid,
            student_id="student-500",
            book_id="book-600",
            current_page=3,
            status=SessionStatus.ACTIVE
        )
        
        session_dict = session.model_dump()
        
        assert isinstance(session_dict, dict)
        assert session_dict["id"] == test_uuid
        assert session_dict["student_id"] == "student-500"
        assert session_dict["book_id"] == "book-600"
        assert session_dict["current_page"] == 3
        assert session_dict["status"] == "active"
    
    def test_session_json_serialization(self):
        """Test that session can be serialized to JSON."""
        session = ReadingSession(
            student_id="student-700",
            book_id="book-800"
        )
        
        json_str = session.model_dump_json()
        
        assert isinstance(json_str, str)
        assert "student-700" in json_str
        assert "book-800" in json_str
    
    def test_session_sample_rate_custom(self):
        """Test setting custom sample rate."""
        session = ReadingSession(
            student_id="student-900",
            book_id="book-1000",
            sample_rate=48000
        )
        
        assert session.sample_rate == 48000
