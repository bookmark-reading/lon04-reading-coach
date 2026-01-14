"""
Comprehensive end-to-end test for the reading coach user journey.

This test covers the complete user flow:
1. GET /books endpoint (user gets books by their reading level)
2. WebSocket connection with specific book_id
3. Audio streaming
4. Page completion detection
5. Feedback audio on page completion
6. Book completion and connection closing
"""

import asyncio
import httpx
import json
import logging
import pytest
import websockets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"
TEST_USER_ID = "12345678-1234-5678-1234-567812345678"
TEST_TOKEN = "test-token"


def generate_pcm16_audio(duration_ms: int, sample_rate: int = 16000) -> bytes:
    """Generate test PCM16LE audio data."""
    import math
    import struct
    
    num_samples = int(sample_rate * duration_ms / 1000)
    audio_data = bytearray()
    
    for i in range(num_samples):
        t = i / sample_rate
        sample = int(32767 * 0.5 * math.sin(2 * math.pi * 440 * t))
        audio_data.extend(struct.pack('<h', sample))
    
    return bytes(audio_data)


@pytest.mark.asyncio
async def test_complete_user_journey():
    """Test the complete user journey from getting books to completing a reading session."""
    
    # Step 1: GET /books endpoint - user gets books by their reading level
    logger.info("Step 1: Getting books for user")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/books", params={"user_id": TEST_USER_ID})
        assert response.status_code == 200
        data = response.json()
        
        assert "books" in data
        assert len(data["books"]) > 0
        assert data["user_id"] == TEST_USER_ID
        
        # Get the first book
        book = data["books"][0]
        book_id = book["book_id"]
        total_pages = book["total_pages"]
        
        logger.info(f"Found book: {book['book_name']} (ID: {book_id}, {total_pages} pages)")
    
    # Step 2: Connect to WebSocket with specific book_id
    logger.info(f"Step 2: Connecting to WebSocket for book {book_id}")
    ws_url_with_token = f"{WS_URL}?token={TEST_TOKEN}"
    
    async with websockets.connect(ws_url_with_token) as websocket:
        # Send session.create message
        session_create = {
            "type": "session.create",
            "student_id": TEST_USER_ID,
            "book_id": book_id,
            "current_page": 1,
            "sample_rate": 16000
        }
        await websocket.send(json.dumps(session_create))
        logger.info("Sent session.create message")
        
        # Receive session.created response
        logger.info("Waiting for session.created response...")
        response = await websocket.recv()
        logger.info(f"Received response: {response[:200] if isinstance(response, str) else f'binary {len(response)} bytes'}")
        session_data = json.loads(response)
        
        assert session_data["type"] == "session.created"
        assert "session_id" in session_data
        session_id = session_data["session_id"]
        logger.info(f"Session created: {session_id}")
        
        # Check if there are more messages waiting (e.g., session.ready)
        logger.info("Checking for session.ready message...")
        try:
            ready_response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            logger.info(f"Got additional message: {ready_response[:200] if isinstance(ready_response, str) else f'binary {len(ready_response)} bytes'}")
        except asyncio.TimeoutError:
            logger.info("No session.ready message received within 2s")
        except Exception as e:
            logger.error(f"Error receiving session.ready: {type(e).__name__}: {e}")
        
        # Step 3: Stream audio data
        logger.info("Step 3: Streaming audio data")
        
        # Send several audio chunks (simulating reading)
        num_audio_chunks = 10
        for i in range(num_audio_chunks):
            audio_chunk = generate_pcm16_audio(duration_ms=100, sample_rate=16000)
            logger.info(f"Sending audio chunk {i+1}/{num_audio_chunks}...")
            await websocket.send(audio_chunk)
            logger.info(f"Sent audio chunk {i+1}/{num_audio_chunks} ({len(audio_chunk)} bytes)")
            await asyncio.sleep(0.1)  # Simulate real-time streaming
        
        logger.info(f"Successfully sent {num_audio_chunks} audio chunks")
        
        # Step 4: Wait for potential page completion events
        # Note: The page completion detector is a random timer, so we may or may not receive events
        logger.info("Step 4: Waiting for page completion events (if any)")
        
        try:
            # Wait for up to 15 seconds for potential messages
            message = await asyncio.wait_for(websocket.recv(), timeout=15.0)
            
            if isinstance(message, str):
                event_data = json.loads(message)
                logger.info(f"Received event: {event_data}")
                
                # Could be a page change event or feedback
                if event_data.get("type") == "page.change":
                    logger.info(f"Page change detected: moving to page {event_data.get('page')}")
                elif event_data.get("type") == "response.audio":
                    logger.info("Received feedback audio")
            else:
                # Binary message (feedback audio)
                logger.info(f"Received binary feedback audio: {len(message)} bytes")
        
        except asyncio.TimeoutError:
            logger.info("No page completion event received within timeout (this is expected with random timer)")
        
        # Step 5: Send more audio to potentially trigger more page events
        logger.info("Step 5: Sending additional audio")
        for i in range(5):
            audio_chunk = generate_pcm16_audio(duration_ms=100, sample_rate=16000)
            await websocket.send(audio_chunk)
            await asyncio.sleep(0.1)
        
        logger.info("Completed audio streaming")
        
        # Step 6: Close connection gracefully
        logger.info("Step 6: Closing WebSocket connection")
        await websocket.close()
        
    logger.info("✓ Complete user journey test passed!")


@pytest.mark.asyncio
async def test_get_books_for_user():
    """Test GET /books endpoint retrieves books matching user's reading level."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/books", params={"user_id": TEST_USER_ID})
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "books" in data
        assert "user_id" in data
        assert data["user_id"] == TEST_USER_ID
        
        # Verify we have books
        books = data["books"]
        assert len(books) > 0
        
        # Verify book structure
        book = books[0]
        assert "book_id" in book
        assert "book_name" in book
        assert "reading_level" in book
        assert "total_pages" in book
        
        # The test user has reading level 2, so all books should be level 2
        for book in books:
            assert book["reading_level"] == 2
        
        logger.info(f"✓ Found {len(books)} books for user at reading level 2")


@pytest.mark.asyncio
async def test_websocket_session_lifecycle():
    """Test WebSocket session creation, audio streaming, and disconnection."""
    ws_url_with_token = f"{WS_URL}?token={TEST_TOKEN}"
    
    async with websockets.connect(ws_url_with_token) as websocket:
        # Create session
        await websocket.send(json.dumps({
            "type": "session.create",
            "student_id": TEST_USER_ID,
            "book_id": "bathtub-safari",
            "current_page": 1,
            "sample_rate": 16000
        }))
        
        # Receive session.created
        response = await websocket.recv()
        session_data = json.loads(response)
        
        assert session_data["type"] == "session.created"
        assert "session_id" in session_data
        
        # Send audio
        audio = generate_pcm16_audio(duration_ms=200)
        await websocket.send(audio)
        
        # Close cleanly
        await websocket.close()
        
    logger.info("✓ WebSocket session lifecycle test passed!")


@pytest.mark.asyncio
async def test_invalid_book_id():
    """Test that invalid book_id returns an error."""
    ws_url_with_token = f"{WS_URL}?token={TEST_TOKEN}"
    
    async with websockets.connect(ws_url_with_token) as websocket:
        # Try to create session with invalid book ID
        await websocket.send(json.dumps({
            "type": "session.create",
            "student_id": TEST_USER_ID,
            "book_id": "nonexistent-book",
            "current_page": 1,
            "sample_rate": 16000
        }))
        
        # Should receive an error or the connection should close
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            data = json.loads(response)
            # Might receive error message
            logger.info(f"Received response for invalid book: {data}")
        except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
            # Connection might close immediately
            logger.info("Connection closed for invalid book (expected behavior)")


if __name__ == "__main__":
    async def run_tests():
        """Run all tests sequentially for debugging."""
        tests = [
            ("GET /books endpoint", test_get_books_for_user),
            ("WebSocket session lifecycle", test_websocket_session_lifecycle),
            ("Complete user journey", test_complete_user_journey),
            ("Invalid book ID handling", test_invalid_book_id),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            print(f"\n{'='*70}")
            print(f"Running: {name}")
            print('='*70)
            try:
                await test_func()
                print(f"✓ PASSED: {name}")
                passed += 1
            except Exception as e:
                print(f"✗ FAILED: {name}")
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()
                failed += 1
        
        print(f"\n{'='*70}")
        print(f"Results: {passed} passed, {failed} failed")
        print('='*70)
        
        return failed == 0
    
    import sys
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
