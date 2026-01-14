"""Local in-memory implementation of Session Repository."""

from typing import Dict

from ..domain.entities.reading_session import ReadingSession
from ..domain.interfaces.session_repository import SessionRepository


class LocalSessionRepository(SessionRepository):
    """Local in-memory implementation of the Session Repository.
    
    Stores sessions in a dictionary for testing and development purposes.
    """
    
    def __init__(self):
        """Initialize the local session repository with an empty dictionary."""
        self._sessions: Dict[str, ReadingSession] = {}
    
    async def save_session(self, session: ReadingSession) -> None:
        """Save a session to the in-memory dictionary.
        
        Args:
            session: The session entity to save.
        """
        self._sessions[str(session.id)] = session
    
    async def get_session(self, session_id: str) -> ReadingSession:
        """Retrieve a session by ID from the in-memory dictionary.
        
        Args:
            session_id: The unique identifier of the session.
            
        Returns:
            ReadingSession: The session entity.
            
        Raises:
            ValueError: If the session is not found.
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session with id {session_id} not found")
        
        return self._sessions[session_id]
    
    async def update_session(self, session: ReadingSession) -> None:
        """Update an existing session in the in-memory dictionary.
        
        Args:
            session: The session entity to update.
            
        Raises:
            ValueError: If the session is not found.
        """
        if str(session.id) not in self._sessions:
            raise ValueError(f"Session with id {session.id} not found")
        
        self._sessions[str(session.id)] = session
    
    async def delete_session(self, session_id: str) -> None:
        """Delete a session from the in-memory dictionary.
        
        Args:
            session_id: The unique identifier of the session to delete.
            
        Raises:
            ValueError: If the session is not found.
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session with id {session_id} not found")
        
        del self._sessions[session_id]
    
    def clear(self) -> None:
        """Clear all sessions from the dictionary."""
        self._sessions.clear()
    
    def get_all_sessions(self) -> Dict[str, ReadingSession]:
        """Get all sessions.
        
        Returns:
            Dict[str, ReadingSession]: Dictionary of all sessions.
        """
        return self._sessions.copy()
    
    async def list_sessions(self) -> list[ReadingSession]:
        """List all sessions.
        
        Returns:
            list[ReadingSession]: List of all sessions.
        """
        return list(self._sessions.values())
    
    # Aliases for convenience
    async def save(self, session: ReadingSession) -> None:
        """Alias for save_session."""
        await self.save_session(session)
    
    async def update(self, session: ReadingSession) -> None:
        """Alias for update_session."""
        await self.update_session(session)
