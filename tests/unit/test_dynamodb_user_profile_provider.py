"""Tests for DynamoDB user profile provider."""

from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.domain.entities.user_profile import UserProfile
from src.infrastructure.dynamodb_user_profile_provider import DynamoDBUserProfileProvider


@pytest.fixture
def mock_dynamodb_table():
    """Create a mock DynamoDB table."""
    with patch("src.infrastructure.dynamodb_user_profile_provider.boto3") as mock_boto3:
        mock_resource = MagicMock()
        mock_table = MagicMock()
        mock_boto3.resource.return_value = mock_resource
        mock_resource.Table.return_value = mock_table
        yield mock_table


@pytest.fixture
def provider(mock_dynamodb_table):
    """Create a DynamoDB user profile provider instance."""
    return DynamoDBUserProfileProvider(table_name="test-users", region_name="us-east-1")


@pytest.fixture
def sample_user_id():
    """Create a sample user ID."""
    return UUID("123e4567-e89b-12d3-a456-426614174000")


@pytest.fixture
def sample_dynamodb_item(sample_user_id):
    """Create a sample DynamoDB item."""
    session_id = "223e4567-e89b-12d3-a456-426614174000"
    return {
        "id": str(sample_user_id),
        "first_name": "John",
        "last_name": "Doe",
        "sessions": [session_id],
    }


class TestDynamoDBUserProfileProvider:
    """Test cases for DynamoDBUserProfileProvider."""
    
    def test_init(self, provider, mock_dynamodb_table):
        """Test provider initialization."""
        assert provider.table_name == "test-users"
        assert provider.table == mock_dynamodb_table
    
    def test_get_user_success(self, provider, mock_dynamodb_table, sample_user_id, sample_dynamodb_item):
        """Test successful user retrieval."""
        mock_dynamodb_table.get_item.return_value = {"Item": sample_dynamodb_item}
        
        result = provider.get_user(sample_user_id)
        
        assert isinstance(result, UserProfile)
        assert result.first_name == "John"
        assert result.last_name == "Doe"
        assert len(result.sessions) == 1
        assert result.sessions[0] == UUID("223e4567-e89b-12d3-a456-426614174000")
        
        mock_dynamodb_table.get_item.assert_called_once_with(Key={"id": str(sample_user_id)})
    
    def test_get_user_not_found(self, provider, mock_dynamodb_table, sample_user_id):
        """Test user not found scenario."""
        mock_dynamodb_table.get_item.return_value = {}
        
        with pytest.raises(ValueError, match=f"User with id {sample_user_id} not found"):
            provider.get_user(sample_user_id)
    
    def test_get_user_with_minimal_data(self, provider, mock_dynamodb_table, sample_user_id):
        """Test user retrieval with minimal required data."""
        minimal_item = {
            "id": str(sample_user_id),
            "first_name": "Jane",
            "last_name": "Doe",
        }
        mock_dynamodb_table.get_item.return_value = {"Item": minimal_item}
        
        result = provider.get_user(sample_user_id)
        
        assert isinstance(result, UserProfile)
        assert result.first_name == "Jane"
        assert result.last_name == "Doe"
        assert result.sessions == []  # default empty list
    
    def test_item_to_user_profile_complete(self, provider, sample_user_id, sample_dynamodb_item):
        """Test conversion of complete DynamoDB item to UserProfile."""
        result = provider._item_to_user_profile(sample_dynamodb_item)
        
        assert isinstance(result, UserProfile)
        assert result.first_name == "John"
        assert result.last_name == "Doe"
        assert len(result.sessions) == 1
        assert result.sessions[0] == UUID("223e4567-e89b-12d3-a456-426614174000")
    
    def test_item_to_user_profile_without_sessions(self, provider, sample_user_id):
        """Test conversion without sessions field."""
        item = {
            "id": str(sample_user_id),
            "first_name": "Test",
            "last_name": "User",
        }
        
        result = provider._item_to_user_profile(item)
        
        assert isinstance(result, UserProfile)
        assert result.first_name == "Test"
        assert result.last_name == "User"
        assert result.sessions == []
    
    def test_get_user_with_multiple_sessions(self, provider, mock_dynamodb_table, sample_user_id):
        """Test user retrieval with multiple sessions."""
        session_ids = [
            "323e4567-e89b-12d3-a456-426614174000",
            "423e4567-e89b-12d3-a456-426614174000",
            "523e4567-e89b-12d3-a456-426614174000",
        ]
        item = {
            "id": str(sample_user_id),
            "first_name": "Multi",
            "last_name": "Session",
            "sessions": session_ids,
        }
        mock_dynamodb_table.get_item.return_value = {"Item": item}
        
        result = provider.get_user(sample_user_id)
        
        assert len(result.sessions) == 3
        assert result.sessions[0] == UUID(session_ids[0])
        assert result.sessions[1] == UUID(session_ids[1])
        assert result.sessions[2] == UUID(session_ids[2])
    
    def test_get_user_with_empty_sessions(self, provider, mock_dynamodb_table, sample_user_id):
        """Test user retrieval with empty sessions list."""
        item = {
            "id": str(sample_user_id),
            "first_name": "Empty",
            "last_name": "Sessions",
            "sessions": [],
        }
        mock_dynamodb_table.get_item.return_value = {"Item": item}
        
        result = provider.get_user(sample_user_id)
        
        assert result.first_name == "Empty"
        assert result.last_name == "Sessions"
        assert result.sessions == []
