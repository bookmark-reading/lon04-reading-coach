"""Tests for DynamoDB session repository."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest

from src.domain.entities.reading_session import ReadingSession, SessionStatus
from src.infrastructure.dynamodb_session_repository import DynamoDBSessionRepository


@pytest.fixture
def mock_dynamodb_table():
    """Create a mock DynamoDB table."""
    mock_table = AsyncMock()
    return mock_table


@pytest.fixture
def mock_dynamodb_resource(mock_dynamodb_table):
    """Create a mock DynamoDB resource."""
    mock_resource = MagicMock()
    mock_resource.Table = AsyncMock(return_value=mock_dynamodb_table)
    return mock_resource


@pytest.fixture
def mock_aioboto3_session(mock_dynamodb_resource):
    """Create a mock aioboto3 session."""
    with patch("src.infrastructure.dynamodb_session_repository.aioboto3.Session") as mock_session_class:
        mock_session_instance = MagicMock()
        mock_session_class.return_value = mock_session_instance
        
        # Setup async context manager for resource
        mock_session_instance.resource.return_value.__aenter__ = AsyncMock(return_value=mock_dynamodb_resource)
        mock_session_instance.resource.return_value.__aexit__ = AsyncMock(return_value=None)
        
        yield mock_session_instance


@pytest.fixture
def repository(mock_aioboto3_session):
    """Create a DynamoDB session repository instance."""
    return DynamoDBSessionRepository(table_name="test-sessions", region_name="us-east-1")


@pytest.fixture
def sample_session():
    """Create a sample session entity."""
    test_uuid = uuid.UUID('12345678-1234-5678-1234-567812345678')
    return ReadingSession(
        id=test_uuid,
        student_id="student-abc",
        book_id="book-xyz",
        current_page=5,
        sample_rate=16000,
        status=SessionStatus.ACTIVE,
        started_at=datetime(2026, 1, 13, 10, 0, 0),
        last_activity_at=datetime(2026, 1, 13, 10, 30, 0),
    )


@pytest.fixture
def sample_dynamodb_item():
    """Create a sample DynamoDB item."""
    return {
        "id": "12345678-1234-5678-1234-567812345678",
        "student_id": "student-abc",
        "book_id": "book-xyz",
        "current_page": 5,
        "sample_rate": 16000,
        "status": "active",
        "started_at": "2026-01-13T10:00:00",
        "last_activity_at": "2026-01-13T10:30:00",
    }


class TestDynamoDBSessionRepository:
    """Test cases for DynamoDBSessionRepository."""
    
    def test_init(self, repository):
        """Test repository initialization."""
        assert repository.table_name == "test-sessions"
        assert repository.region_name == "us-east-1"
    
    @pytest.mark.asyncio
    async def test_save_session(self, repository, mock_dynamodb_table, sample_session):
        """Test saving a session to DynamoDB."""
        await repository.save_session(sample_session)
        
        mock_dynamodb_table.put_item.assert_called_once()
        call_args = mock_dynamodb_table.put_item.call_args
        item = call_args.kwargs["Item"]
        
        assert item["id"] == "12345678-1234-5678-1234-567812345678"
        assert item["student_id"] == "student-abc"
        assert item["book_id"] == "book-xyz"
        assert item["current_page"] == 5
        assert item["sample_rate"] == 16000
        assert item["status"] == "active"
        assert item["started_at"] == "2026-01-13T10:00:00"
        assert item["last_activity_at"] == "2026-01-13T10:30:00"
    
    @pytest.mark.asyncio
    async def test_get_session_success(self, repository, mock_dynamodb_table, sample_dynamodb_item):
        """Test successful session retrieval."""
        mock_dynamodb_table.get_item.return_value = {"Item": sample_dynamodb_item}
        
        result = await repository.get_session("12345678-1234-5678-1234-567812345678")
        
        assert isinstance(result, ReadingSession)
        assert str(result.id) == "12345678-1234-5678-1234-567812345678"
        assert result.student_id == "student-abc"
        assert result.book_id == "book-xyz"
        assert result.current_page == 5
        assert result.sample_rate == 16000
        assert result.status == SessionStatus.ACTIVE
        assert result.started_at == datetime(2026, 1, 13, 10, 0, 0)
        assert result.last_activity_at == datetime(2026, 1, 13, 10, 30, 0)
        
        mock_dynamodb_table.get_item.assert_called_once_with(Key={"id": "12345678-1234-5678-1234-567812345678"})
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, repository, mock_dynamodb_table):
        """Test session not found scenario."""
        mock_dynamodb_table.get_item.return_value = {}
        
        with pytest.raises(ValueError, match="Session with id 12345678-1234-5678-1234-567812345678 not found"):
            await repository.get_session("12345678-1234-5678-1234-567812345678")
    
    @pytest.mark.asyncio
    async def test_update_session(self, repository, mock_dynamodb_table, sample_session):
        """Test updating an existing session."""
        # Update some fields
        sample_session.current_page = 10
        sample_session.status = SessionStatus.PAUSED
        
        await repository.update_session(sample_session)
        
        mock_dynamodb_table.put_item.assert_called_once()
        call_args = mock_dynamodb_table.put_item.call_args
        item = call_args.kwargs["Item"]
        
        assert item["id"] == "12345678-1234-5678-1234-567812345678"
        assert item["current_page"] == 10
        assert item["status"] == "paused"
    
    @pytest.mark.asyncio
    async def test_delete_session(self, repository, mock_dynamodb_table):
        """Test deleting a session."""
        await repository.delete_session("12345678-1234-5678-1234-567812345678")
        
        mock_dynamodb_table.delete_item.assert_called_once_with(Key={"id": "12345678-1234-5678-1234-567812345678"})
    
    def test_session_to_item(self, repository, sample_session):
        """Test conversion of Session entity to DynamoDB item."""
        result = repository._session_to_item(sample_session)
        
        assert result["id"] == "12345678-1234-5678-1234-567812345678"
        assert result["student_id"] == "student-abc"
        assert result["book_id"] == "book-xyz"
        assert result["current_page"] == 5
        assert result["sample_rate"] == 16000
        assert result["status"] == "active"
        assert result["started_at"] == "2026-01-13T10:00:00"
        assert result["last_activity_at"] == "2026-01-13T10:30:00"
    
    def test_item_to_session(self, repository, sample_dynamodb_item):
        """Test conversion of DynamoDB item to Session entity."""
        result = repository._item_to_session(sample_dynamodb_item)
        
        assert isinstance(result, ReadingSession)
        assert str(result.id) == "12345678-1234-5678-1234-567812345678"
        assert result.student_id == "student-abc"
        assert result.book_id == "book-xyz"
        assert result.current_page == 5
        assert result.sample_rate == 16000
        assert result.status == SessionStatus.ACTIVE
        assert result.started_at == datetime(2026, 1, 13, 10, 0, 0)
        assert result.last_activity_at == datetime(2026, 1, 13, 10, 30, 0)
    
    @pytest.mark.asyncio
    async def test_save_session_with_different_statuses(self, repository, mock_dynamodb_table, sample_session):
        """Test saving sessions with different status values."""
        statuses = [
            SessionStatus.INITIALIZING,
            SessionStatus.ACTIVE,
            SessionStatus.PAUSED,
            SessionStatus.COMPLETED,
            SessionStatus.ERROR,
        ]
        
        for status in statuses:
            sample_session.status = status
            await repository.save_session(sample_session)
        
        # Should have been called for each status
        assert mock_dynamodb_table.put_item.call_count == len(statuses)
    
    @pytest.mark.asyncio
    async def test_get_session_with_initializing_status(self, repository, mock_dynamodb_table):
        """Test retrieving a session with INITIALIZING status."""
        item = {
            "id": "12345678-1234-5678-1234-567812345679",
            "student_id": "student-123",
            "book_id": "book-456",
            "current_page": 1,
            "sample_rate": 16000,
            "status": "initializing",
            "started_at": "2026-01-13T09:00:00",
            "last_activity_at": "2026-01-13T09:00:00",
        }
        mock_dynamodb_table.get_item.return_value = {"Item": item}
        
        result = await repository.get_session("12345678-1234-5678-1234-567812345679")
        
        assert result.status == SessionStatus.INITIALIZING
        assert result.current_page == 1
    
    @pytest.mark.asyncio
    async def test_get_session_with_completed_status(self, repository, mock_dynamodb_table):
        """Test retrieving a session with COMPLETED status."""
        item = {
            "id": "12345678-1234-5678-1234-567812345680",
            "student_id": "student-789",
            "book_id": "book-101",
            "current_page": 100,
            "sample_rate": 16000,
            "status": "completed",
            "started_at": "2026-01-12T10:00:00",
            "last_activity_at": "2026-01-13T10:00:00",
        }
        mock_dynamodb_table.get_item.return_value = {"Item": item}
        
        result = await repository.get_session("12345678-1234-5678-1234-567812345680")
        
        assert result.status == SessionStatus.COMPLETED
        assert result.current_page == 100
