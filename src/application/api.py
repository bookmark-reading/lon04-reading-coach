"""FastAPI application entry point."""

import logging
from typing import Optional

from fastapi import FastAPI, WebSocket, Query, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from jose import JWTError

from .config import settings
from .controller import ReadingCoachController
from ..infrastructure.local_book_provider import LocalBookProvider
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize providers (in production, these would be configured based on environment)
book_provider = LocalBookProvider()
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


@app.get("/pdf/{book_id}")
async def get_pdf(book_id: str):
    """Serve PDF file for a book from S3."""
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        book = book_provider.get_book_metadata(book_id)
        
        # Parse S3 path
        if book.path.startswith('s3://'):
            s3_path = book.path.replace('s3://', '')
            bucket_name = s3_path.split('/')[0]
            object_key = '/'.join(s3_path.split('/')[1:])
            
            # Download from S3
            s3_client = boto3.client('s3', region_name='us-west-2')
            try:
                response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
                pdf_content = response['Body'].read()
                
                from fastapi.responses import Response
                return Response(content=pdf_content, media_type="application/pdf")
            except ClientError as e:
                logger.error(f"S3 error: {e}")
                raise HTTPException(status_code=404, detail=f"PDF not found in S3: {e}")
        else:
            # Local file
            import os
            pdf_path = os.path.join("/workshop/lon04-reading-coach", book.path)
            if not os.path.exists(pdf_path):
                raise HTTPException(status_code=404, detail="PDF file not found")
            return FileResponse(pdf_path, media_type="application/pdf")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error serving PDF for book {book_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/textract/{book_id}")
async def get_textract(book_id: str, page: int = Query(1, description="Page number")):
    """Extract text from PDF page - mock implementation."""
    try:
        # Mock: Pages 1-2 are covers (blank), pages 3+ have text
        has_text = page > 2
        text = f"Story content on page {page}" if has_text else ""
        
        return {
            "page": page,
            "text": text,
            "book_id": book_id,
            "has_text": has_text
        }
    except Exception as e:
        logger.error(f"Textract error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-recording")
async def upload_recording(
    user_id: str = Form(...),
    book_id: str = Form(...),
    video: UploadFile = File(...)
):
    """Upload video recording to S3."""
    try:
        import boto3
        from datetime import datetime
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recordings/{user_id}/{book_id}_{timestamp}.webm"
        
        # Upload to S3
        s3_client = boto3.client('s3', region_name='us-west-2')
        video_content = await video.read()
        
        s3_client.put_object(
            Bucket='bookmark-hackathon-source-files',
            Key=filename,
            Body=video_content,
            ContentType='video/webm'
        )
        
        logger.info(f"Uploaded recording: {filename}")
        return {"success": True, "filename": filename, "size": len(video_content)}
    except Exception as e:
        logger.error(f"Error uploading recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))



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
    # For development, accept any token
    return True
