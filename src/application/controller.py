"""Reading Coach Controller for handling business logic and coordination."""

import asyncio
import logging
from typing import Dict, Optional
from uuid import UUID

from fastapi import WebSocket

from ..domain.entities import ReadingSession
from ..domain.services import ReadingService
from .websocket_handler import WebSocketHandler
from ..domain.interfaces.book_provider import BookProvider
from ..domain.interfaces.page_completion_detector import PageCompletionDetector
from ..domain.interfaces.reading_agent import ReadingAgent
from ..domain.interfaces.session_repository import SessionRepository
from ..domain.interfaces.user_profile_provider import UserProfileProvider

logger = logging.getLogger(__name__)


class ReadingCoachController:
    """
    Controller for coordinating reading coach operations.
    
    This controller is injected with all necessary providers and handles
    the business logic for each endpoint, keeping the API layer thin.
    """
    
    def __init__(
        self,
        book_provider: BookProvider,
        user_profile_provider: UserProfileProvider,
        session_repository: SessionRepository,
        reading_agent: ReadingAgent,
        persist_interval: int = 10,  # Save session every 10 seconds
    ):
        """
        Initialize the controller with injected dependencies.
        
        Args:
            book_provider: Provider for book data
            user_profile_provider: Provider for user profile data
            session_repository: Repository for session persistence
            persist_interval: Seconds between session saves
        """
        self.reading_agent = reading_agent
        self.book_provider = book_provider
        self.user_profile_provider = user_profile_provider
        self.session_repository = session_repository
        self.persist_interval = persist_interval
        
        logger.info("ReadingCoachController initialized with providers")
    
    async def handle_websocket_connection(
        self,
        websocket: WebSocket,
        book_id: Optional[str],
        student_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        logger.info(f"Handling new WebSocket connection from {websocket.client}")
        
        # Get or create session
        if session_id:
            session = await self.session_repository.get_session(session_id)
            assert book_id == session.book_id
            logger.info(f"Resuming existing session {session_id}")
        else:
            session = ReadingSession(
                student_id=student_id,
                book_id=book_id,
                current_page=1,  # Start at page 1
            )
            await self.session_repository.save_session(session)
            logger.info(f"Created new session {session.id}")
            
            # Send session.created response to client
            await websocket.send_json({
                "type": "session.created",
                "session_id": str(session.id)
            })
        
        # Create services
        book = self.book_provider.get_book(book_id)
        reading_service = ReadingService(session=session, book=book, agent=self.reading_agent)
        handler = WebSocketHandler(reading_service=reading_service)
        
        # Start the reading service
        await reading_service.start()
        
        # Start periodic session persistence
        persist_task = asyncio.create_task(
            self._periodic_session_save(reading_service)
        )
        
        try:
            # Handle websocket connection
            await handler.handle_websocket(websocket)
        finally:
            # Cleanup
            persist_task.cancel()
            try:
                await persist_task
            except asyncio.CancelledError:
                pass
            
            # Final save on disconnect
            await self.session_repository.update_session(reading_service.session)
            logger.info(f"Session {session.id} final save completed")
    
    async def _periodic_session_save(self, reading_service: ReadingService) -> None:
        """
        Periodically save session state to repository.
        
        Args:
            reading_service: The reading service whose session to save
        """
        while True:
            try:
                await asyncio.sleep(self.persist_interval)
                session = reading_service.session
                await self.session_repository.update(session)
                logger.debug(f"Session {session.session_id} auto-saved")
            except asyncio.CancelledError:
                logger.debug("Session persistence task cancelled")
                break
            except Exception as e:
                logger.error(f"Error persisting session: {e}", exc_info=True)
    
    def get_health_status(self) -> dict:
        """
        Get application health status.
        
        Returns:
            Dict containing health status information
        """
        return {
            "status": "healthy",
            "providers": {
                "book_provider": type(self.book_provider).__name__,
                "user_profile_provider": type(self.user_profile_provider).__name__,
                "session_repository": type(self.session_repository).__name__,
            },
        }
    
    async def get_books_for_user(self, user_id: str) -> list:
        """
        Get books suitable for a user based on their reading age.
        
        Args:
            user_id: The UUID string of the user.
            
        Returns:
            List of book metadata dictionaries suitable for the user's reading age.
            
        Raises:
            ValueError: If user not found.
        """
        from uuid import UUID
        
        # Get user profile
        user_profile = self.user_profile_provider.get_user(UUID(user_id))
        
        # Get books for the user's reading level with real page counts
        books = self.book_provider.get_books_by_reading_level(user_profile.current_reading_level)
        
        # Ensure we get real page counts from PDFs
        updated_books = []
        for book in books:
            # Get metadata with content to calculate real page count
            book_with_content = self.book_provider.get_book_metadata(book.book_id, include_content=True)
            updated_books.append(book_with_content)
        
        # Convert to dict for JSON response.
        # We intentionally exclude the raw PDF bytes in `content` because JSON
        # encoding of arbitrary binary data will fail (and is inefficient).
        # The server-side code can still use `BookMetadata.content` internally.
        return [book.model_dump(exclude={"content"}) for book in updated_books]
