"""User profile provider protocol."""

from typing import Protocol, runtime_checkable
from uuid import UUID

from ..entities.user_profile import UserProfile


@runtime_checkable
class UserProfileProvider(Protocol):
    """Protocol for user profile data providers."""
    
    def get_user(self, user_id: UUID) -> UserProfile:
        """Retrieve a user profile by user ID.
        
        Args:
            user_id: The unique identifier of the user.
            
        Returns:
            UserProfile: The user profile entity.
        """
        ...
