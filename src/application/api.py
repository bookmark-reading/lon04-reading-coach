"""FastAPI application entry point."""

import logging
from typing import Optional

from fastapi import FastAPI, WebSocket, Query, HTTPException, status
from jose import JWTError

from .config import settings
from .controller import ReadingCoachController
from ..infrastructure.aws_book_provider import AWSBookProvider
from ..infrastructure.local_session_repository import LocalSessionRepository
from ..infrastructure.local_user_profile_provider import LocalUserProfileProvider
from ..domain.agents.simple_reading_agent import SimpleReadingAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

# Initialize providers (configured via environment)
book_provider = AWSBookProvider(
    table_name=settings.books_table_name,
    bucket_name=settings.books_bucket_name,
    region_name=settings.aws_region,
)
user_profile_provider = LocalUserProfileProvider()
session_repository = LocalSessionRepository()
reading_agent = SimpleReadingAgent()

# Initialize controller with injected dependencies
controller = ReadingCoachController(
    book_provider=book_provider,
    user_profile_provider=user_profile_provider,
    session_repository=session_repository,
    reading_agent=reading_agent,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return controller.get_health_status()


@app.get("/books")
async def get_books(user_id: str = Query(..., description="User ID to get books for")):
    """Get books suitable for a user based on their reading age.
    
    Args:
        user_id: The UUID of the user.
        
    Returns:
        List of books suitable for the user's reading age.
    """
    try:
        books = await controller.get_books_for_user(user_id)
        return {"books": books, "user_id": user_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting books for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")



@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for reading coach sessions.
    
    Handles full-duplex communication for:
    - Audio frames (binary messages)
    - JSON control/event messages (text messages)
    
    Args:
        websocket: WebSocket connection
        token: Authentication token (query parameter)
    
    Connection lifecycle:
    1. Client connects with valid token
    2. Client sends session.create message
    3. Server responds with session.created (includes session_id)
    4. Bidirectional audio + JSON messages
    5. On disconnect, server finalizes session
    
    Audio format:
    - PCM16LE
    - Mono
    - 16 kHz sample rate
    - 20-50ms chunks
    
    Note:
        Session ID is generated server-side and returned in the
        session.created message, not provided in the URL.
    """
    # Validate authentication token
    if not _validate_token(token):
        logger.warning(f"Invalid or missing token for WebSocket connection")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Accept the websocket connection
    await websocket.accept()
    
    try:
        # Wait for session.create message from client
        message = await websocket.receive_json()
        
        if message.get("type") != "session.create":
            logger.error(f"Expected session.create message, got {message.get('type')}")
            await websocket.send_json({
                "type": "error",
                "code": "INVALID_MESSAGE",
                "message": "First message must be session.create"
            })
            await websocket.close()
            return
        
        # Extract session parameters
        student_id = message.get("student_id")
        book_id = message.get("book_id")
        current_page = message.get("current_page", 1)
        
        if not student_id or not book_id:
            logger.error("Missing required fields in session.create")
            await websocket.send_json({
                "type": "error",
                "code": "INVALID_MESSAGE",
                "message": "student_id and book_id are required"
            })
            await websocket.close()
            return
        
        # Delegate to controller with session parameters
        await controller.handle_websocket_connection(
            websocket=websocket,
            book_id=book_id,
            student_id=student_id,
            session_id=None
        )
    except Exception as e:
        logger.error(f"Error handling websocket connection: {e}", exc_info=True)
        try:
            await websocket.close()
        except:
            pass


def _validate_token(token: Optional[str]) -> bool:
    """
    Validate authentication token.
    
    Args:
        token: JWT or signed token string
        
    Returns:
        True if valid, False otherwise
    
    Note:
        This is a placeholder implementation. In production:
        - Validate JWT signature
        - Check expiration
        - Verify claims (student_id, permissions, etc.)
        - Check against revocation list
    """
    # TODO: Implement proper JWT validation
    # For now, accept any non-empty token in development mode
    if settings.debug:
        return token is not None and len(token) > 0
    
    if not token:
        return False
    
    try:
        # Example JWT validation (requires proper SECRET_KEY in production)
        # payload = jwt.decode(
        #     token, 
        #     settings.secret_key,
        #     algorithms=["HS256"]
        # )
        # return True
        return True  # Placeholder
    except JWTError:
        return False
