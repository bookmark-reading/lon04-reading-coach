"""DynamoDB implementation of Session Repository."""

from datetime import datetime
from typing import Any, Dict, Optional

import aioboto3

from ..domain.entities.reading_session import ReadingSession, SessionStatus
from ..domain.interfaces.session_repository import SessionRepository


class DynamoDBSessionRepository(SessionRepository):
    """DynamoDB repository for managing session persistence."""
    
    def __init__(self, table_name: str, region_name: str = "us-east-1"):
        """Initialize the DynamoDB session repository.
        
        Args:
            table_name: The name of the DynamoDB table.
            region_name: AWS region name (default: us-east-1).
        """
        self.table_name = table_name
        self.region_name = region_name
        self._session = aioboto3.Session()
    
    async def save_session(self, session: ReadingSession) -> None:
        """Save a session to DynamoDB.
        
        Args:
            session: The session entity to save.
            
        Raises:
            Exception: If the save operation fails.
        """
        async with self._session.resource("dynamodb", region_name=self.region_name) as dynamodb:
            table = await dynamodb.Table(self.table_name)
            item = self._session_to_item(session)
            await table.put_item(Item=item)
    
    async def get_session(self, session_id: str) -> ReadingSession:
        """Retrieve a session by ID from DynamoDB.
        
        Args:
            session_id: The unique identifier of the session.
            
        Returns:
            ReadingSession: The session entity.
            
        Raises:
            ValueError: If the session is not found.
        """
        async with self._session.resource("dynamodb", region_name=self.region_name) as dynamodb:
            table = await dynamodb.Table(self.table_name)
            response = await table.get_item(Key={"id": session_id})
            
            if "Item" not in response:
                raise ValueError(f"Session with id {session_id} not found")
            
            return self._item_to_session(response["Item"])
    
    async def update_session(self, session: ReadingSession) -> None:
        """Update an existing session in DynamoDB.
        
        Args:
            session: The session entity to update.
            
        Raises:
            Exception: If the update operation fails.
        """
        await self.save_session(session)
    
    async def delete_session(self, session_id: str) -> None:
        """Delete a session from DynamoDB.
        
        Args:
            session_id: The unique identifier of the session to delete.
            
        Raises:
            Exception: If the delete operation fails.
        """
        async with self._session.resource("dynamodb", region_name=self.region_name) as dynamodb:
            table = await dynamodb.Table(self.table_name)
            await table.delete_item(Key={"id": session_id})
    
    def _session_to_item(self, session: ReadingSession) -> Dict[str, Any]:
        """Convert a Session entity to a DynamoDB item.
        
        Args:
            session: The session entity.
            
        Returns:
            Dict: The DynamoDB item representation.
        """
        return {
            "id": str(session.id),
            "student_id": session.student_id,
            "book_id": session.book_id,
            "current_page": session.current_page,
            "sample_rate": session.sample_rate,
            "status": session.status.value,
            "started_at": session.started_at.isoformat(),
            "last_activity_at": session.last_activity_at.isoformat(),
        }
    
    def _item_to_session(self, item: Dict[str, Any]) -> ReadingSession:
        """Convert a DynamoDB item to a Session entity.
        
        Args:
            item: The DynamoDB item.
            
        Returns:
            ReadingSession: The session entity.
        """
        return ReadingSession(
            id=item["id"],
            student_id=item["student_id"],
            book_id=item["book_id"],
            current_page=item["current_page"],
            sample_rate=item["sample_rate"],
            status=SessionStatus(item["status"]),
            started_at=datetime.fromisoformat(item["started_at"]),
            last_activity_at=datetime.fromisoformat(item["last_activity_at"]),
        )
