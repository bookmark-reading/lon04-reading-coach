"""DynamoDB implementation of UserProfileProvider."""

from typing import Any, Dict
from uuid import UUID

import boto3

from ..domain.entities.user_profile import UserProfile
from ..domain.interfaces.user_profile_provider import UserProfileProvider


class DynamoDBUserProfileProvider(UserProfileProvider):
    """DynamoDB implementation of the UserProfileProvider protocol."""
    
    def __init__(self, table_name: str, region_name: str = "us-east-1"):
        """Initialize the DynamoDB user profile provider.
        
        Args:
            table_name: The name of the DynamoDB table.
            region_name: AWS region name (default: us-east-1).
        """
        self.table_name = table_name
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.table = self.dynamodb.Table(table_name)
    
    def get_user(self, user_id: UUID) -> UserProfile:
        """Retrieve a user profile by user ID from DynamoDB.
        
        Args:
            user_id: The unique identifier of the user.
            
        Returns:
            UserProfile: The user profile entity.
            
        Raises:
            ValueError: If the user is not found.
        """
        response = self.table.get_item(Key={"id": str(user_id)})
        
        if "Item" not in response:
            raise ValueError(f"User with id {user_id} not found")
        
        return self._item_to_user_profile(response["Item"])
    
    def _item_to_user_profile(self, item: Dict[str, Any]) -> UserProfile:
        """Convert a DynamoDB item to a UserProfile entity.
        
        Args:
            item: The DynamoDB item.
            
        Returns:
            UserProfile: The user profile entity.
        """
        # Parse sessions list if present
        sessions = []
        if "sessions" in item and item["sessions"]:
            sessions = [UUID(session_id) for session_id in item["sessions"]]
        
        return UserProfile(
            first_name=item["first_name"],
            last_name=item["last_name"],
            current_reading_level=item.get("current_reading_level", 3),  # Default to reading level 3 if not present
            sessions=sessions,
        )
