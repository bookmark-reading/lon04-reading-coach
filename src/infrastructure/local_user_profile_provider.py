"""Local in-memory implementation of UserProfileProvider."""

from typing import Dict
from uuid import UUID

from ..domain.entities.user_profile import UserProfile
from ..domain.interfaces.user_profile_provider import UserProfileProvider


class LocalUserProfileProvider(UserProfileProvider):
    """Local in-memory implementation of the UserProfileProvider protocol.
    
    Stores user profiles in a dictionary for testing and development purposes.
    """
    
    def __init__(self):
        """Initialize the local user profile provider with test data."""
        from uuid import UUID
        
        self._profiles: Dict[UUID, UserProfile] = {}
        
        # Pre-populate with test user for e2e testing
        test_user_id = UUID("12345678-1234-5678-1234-567812345678")
        self._profiles[test_user_id] = UserProfile(
            user_id=test_user_id,
            first_name="Test",
            last_name="Student",
            current_reading_level=3,
            sessions_completed=0
        )
    
    def get_user(self, user_id: UUID) -> UserProfile:
        """Retrieve a user profile by user ID from the in-memory dictionary.
        
        Args:
            user_id: The unique identifier of the user.
            
        Returns:
            UserProfile: The user profile entity.
            
        Raises:
            ValueError: If the user is not found.
        """
        if user_id not in self._profiles:
            raise ValueError(f"User with id {user_id} not found")
        
        return self._profiles[user_id]
    
    def add_user(self, user_id: UUID, profile: UserProfile) -> None:
        """Add or update a user profile in the dictionary.
        
        Args:
            user_id: The unique identifier of the user.
            profile: The user profile to store.
        """
        self._profiles[user_id] = profile
    
    def delete_user(self, user_id: UUID) -> None:
        """Delete a user profile from the dictionary.
        
        Args:
            user_id: The unique identifier of the user.
            
        Raises:
            ValueError: If the user is not found.
        """
        if user_id not in self._profiles:
            raise ValueError(f"User with id {user_id} not found")
        
        del self._profiles[user_id]
    
    def clear(self) -> None:
        """Clear all user profiles from the dictionary."""
        self._profiles.clear()
    
    def get_all_users(self) -> Dict[UUID, UserProfile]:
        """Get all user profiles.
        
        Returns:
            Dict[UUID, UserProfile]: Dictionary of all user profiles.
        """
        return self._profiles.copy()
