"""Test that provider implementations conform to the UserProfileProvider protocol."""

from typing import Protocol, runtime_checkable
from uuid import UUID

import pytest

from src.domain.entities.user_profile import UserProfile
from src.domain.interfaces.user_profile_provider import UserProfileProvider
from src.infrastructure.dynamodb_user_profile_provider import DynamoDBUserProfileProvider
from src.infrastructure.local_user_profile_provider import LocalUserProfileProvider


def test_local_provider_implements_protocol():
    """Test that LocalUserProfileProvider implements UserProfileProvider protocol."""
    provider = LocalUserProfileProvider()
    
    # Check that provider is an instance of the protocol
    assert isinstance(provider, UserProfileProvider)
    
    # Check that it has the required method
    assert hasattr(provider, 'get_user')
    assert callable(getattr(provider, 'get_user'))


def test_dynamodb_provider_implements_protocol():
    """Test that DynamoDBUserProfileProvider implements UserProfileProvider protocol."""
    provider = DynamoDBUserProfileProvider("test-table")
    
    # Check that provider is an instance of the protocol
    assert isinstance(provider, UserProfileProvider)
    
    # Check that it has the required method
    assert hasattr(provider, 'get_user')
    assert callable(getattr(provider, 'get_user'))


def test_local_provider_method_signature():
    """Test that LocalUserProfileProvider.get_user has correct signature."""
    provider = LocalUserProfileProvider()
    
    # Add a test user
    test_user_id = UUID('123e4567-e89b-12d3-a456-426614174000')
    test_profile = UserProfile(
        first_name="Test",
        last_name="User",
        current_reading_level=5
    )
    provider.add_user(test_user_id, test_profile)
    
    # Verify get_user accepts UUID and returns UserProfile
    result = provider.get_user(test_user_id)
    assert isinstance(result, UserProfile)
    assert result.first_name == "Test"
    assert result.last_name == "User"
    assert result.current_reading_level == 5


def test_providers_are_interchangeable():
    """Test that both providers can be used interchangeably through the protocol."""
    test_user_id = UUID('123e4567-e89b-12d3-a456-426614174000')
    test_profile = UserProfile(
        first_name="Test",
        last_name="User",
        current_reading_level=5
    )
    
    # Test with local provider
    local_provider: UserProfileProvider = LocalUserProfileProvider()
    local_provider.add_user(test_user_id, test_profile)
    result = local_provider.get_user(test_user_id)
    assert isinstance(result, UserProfile)
    
    # Test that DynamoDB provider also conforms (even if we can't test it fully without AWS)
    dynamo_provider: UserProfileProvider = DynamoDBUserProfileProvider("test-table")
    assert hasattr(dynamo_provider, 'get_user')
