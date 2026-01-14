"""Unit tests for user profile entities."""

import pytest
from datetime import datetime
from uuid import UUID

from src.domain.entities import UserProfile, ReadingLevel


class TestReadingLevel:
    """Tests for ReadingLevel enum."""
    
    def test_reading_level_values(self):
        """Test that reading levels have correct numeric values."""
        assert ReadingLevel.LEVEL_1.value == 1
        assert ReadingLevel.LEVEL_2.value == 2
        assert ReadingLevel.LEVEL_3.value == 3
        assert ReadingLevel.LEVEL_4.value == 4
        assert ReadingLevel.LEVEL_5.value == 5
        assert ReadingLevel.LEVEL_6.value == 6
        assert ReadingLevel.LEVEL_7.value == 7
    
    def test_reading_level_count(self):
        """Test that there are exactly 7 reading levels."""
        assert len(ReadingLevel) == 7


class TestUserProfile:
    """Tests for UserProfile entity."""
    
    def test_user_profile_creation_minimal(self):
        """Test creating a user profile with minimal required fields."""
        profile = UserProfile(
            first_name="John",
            last_name="Doe",
            current_reading_level=5
        )
        
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.current_reading_level == 5
        assert profile.sessions == []
    
    def test_user_profile_creation_with_all_fields(self):
        """Test creating a user profile with all fields."""
        from uuid import uuid4
        session_id1 = uuid4()
        session_id2 = uuid4()
        
        profile = UserProfile(
            first_name="Jane",
            last_name="Smith",
            current_reading_level=6,
            sessions=[session_id1, session_id2]
        )
        
        assert profile.first_name == "Jane"
        assert profile.last_name == "Smith"
        assert profile.current_reading_level == 6
        assert len(profile.sessions) == 2
        assert session_id1 in profile.sessions
        assert session_id2 in profile.sessions
    
    def test_user_profile_validation_first_name_not_empty(self):
        """Test that empty first name raises validation error."""
        with pytest.raises(Exception):  # Pydantic validation error
            UserProfile(
                first_name="",
                last_name="Doe",
                current_reading_level=5
            )
    
    def test_user_profile_validation_first_name_max_length(self):
        """Test that first name exceeding max length raises validation error."""
        with pytest.raises(Exception):  # Pydantic validation error
            UserProfile(
                first_name="a" * 101,  # 101 characters
                last_name="Doe",
                current_reading_level=5
            )
    
    def test_user_profile_validation_last_name_not_empty(self):
        """Test that empty last name raises validation error."""
        with pytest.raises(Exception):  # Pydantic validation error
            UserProfile(
                first_name="John",
                last_name="",
                current_reading_level=5
            )
    
    def test_user_profile_validation_last_name_max_length(self):
        """Test that last name exceeding max length raises validation error."""
        with pytest.raises(Exception):  # Pydantic validation error
            UserProfile(
                first_name="John",
                last_name="a" * 101,  # 101 characters
                current_reading_level=5
            )
    
    def test_user_profile_validation_reading_level_too_low(self):
        """Test that reading level below 1 raises validation error."""
        with pytest.raises(Exception):  # Pydantic validation error
            UserProfile(
                first_name="John",
                last_name="Doe",
                current_reading_level=0
            )
    
    def test_user_profile_validation_reading_level_too_high(self):
        """Test that reading level above 7 raises validation error."""
        with pytest.raises(Exception):  # Pydantic validation error
            UserProfile(
                first_name="John",
                last_name="Doe",
                current_reading_level=8
            )
    
    def test_user_profile_validation_reading_level_valid_range(self):
        """Test that reading levels 1-7 are all valid."""
        for level in range(1, 8):
            profile = UserProfile(
                first_name="John",
                last_name="Doe",
                current_reading_level=level
            )
            assert profile.current_reading_level == level
    
    def test_user_profile_sessions_management(self):
        """Test managing sessions list."""
        from uuid import uuid4
        
        profile = UserProfile(
            first_name="John",
            last_name="Doe",
            current_reading_level=5
        )
        
        # Initially empty
        assert profile.sessions == []
        
        # Add sessions
        session1 = uuid4()
        session2 = uuid4()
        profile.sessions.append(session1)
        profile.sessions.append(session2)
        
        assert len(profile.sessions) == 2
        assert session1 in profile.sessions
        assert session2 in profile.sessions
    
    def test_user_profile_serialization(self):
        """Test that user profile can be serialized to dict."""
        from uuid import uuid4
        session_id = uuid4()
        
        profile = UserProfile(
            first_name="John",
            last_name="Doe",
            current_reading_level=5,
            sessions=[session_id]
        )
        
        profile_dict = profile.model_dump()
        
        assert isinstance(profile_dict, dict)
        assert profile_dict["first_name"] == "John"
        assert profile_dict["last_name"] == "Doe"
        assert profile_dict["current_reading_level"] == 5
        assert len(profile_dict["sessions"]) == 1
    
    def test_user_profile_json_serialization(self):
        """Test that user profile can be serialized to JSON."""
        profile = UserProfile(
            first_name="John",
            last_name="Doe",
            current_reading_level=5
        )
        
        json_str = profile.model_dump_json()
        
        assert isinstance(json_str, str)
        assert "John" in json_str
        assert "Doe" in json_str
