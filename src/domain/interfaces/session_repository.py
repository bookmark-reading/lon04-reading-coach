"""Session Repository interface."""

from typing import Protocol

from ..entities.reading_session import ReadingSession


class SessionRepository(Protocol):
    """Protocol defining the interface for session repositories.
    
    This interface can be implemented by different storage backends
    (in-memory, DynamoDB, etc.) to provide session persistence.
    """
    
    async def save_session(self, session: ReadingSession) -> None:
        """Save a session to the repository.
        
        Args:
            session: The session entity to save.
        """
        ...
    
    async def get_session(self, session_id: str) -> ReadingSession:
        """Retrieve a session by ID from the repository.
        
        Args:
            session_id: The unique identifier of the session.
            
        Returns:
            ReadingSession: The session entity.
            
        Raises:
            ValueError: If the session is not found.
        """
        ...
    
    async def update_session(self, session: ReadingSession) -> None:
        """Update an existing session in the repository.
        
        Args:
            session: The session entity to update.
            
        Raises:
            ValueError: If the session is not found.
        """
        ...
    
    async def delete_session(self, session_id: str) -> None:
        """Delete a session from the repository.
        
        Args:
            session_id: The unique identifier of the session to delete.
            
        Raises:
            ValueError: If the session is not found.
        """
        ...
