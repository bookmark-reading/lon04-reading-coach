"""
Test client for the Reading Coach application.

This script provides three test modes:

1. WebSocket Client (default):
   Tests the full stack through the FastAPI WebSocket endpoint.
   Usage: python demo_reading_agent.py
   
   Requirements:
   - Start the server first: uvicorn src.application.api:app --reload
   - Speak into your microphone
   - Audio flows: Microphone -> WebSocket -> Backend -> Nova Sonic -> WebSocket -> Speaker

2. Direct Agent Test:
   Tests the ReadingAgent protocol implementation directly.
   Usage: python demo_reading_agent.py --agent
   
   Requirements:
   - No server needed
   - Direct interaction with NovaSonicReadingAgent

3. Direct Nova Sonic Client:
   Tests the raw Nova Sonic SDK client.
   Usage: python demo_reading_agent.py --direct
   
   Requirements:
   - No server needed
   - Direct interaction with Nova Sonic SDK
"""

import os
import asyncio
import logging
import pyaudio
import json
from datetime import datetime

import websockets

from src.infrastructure.nova_sonic import NovaSonic
from src.infrastructure.nova_sonic_reading_agent import NovaSonicReadingAgent
# Import domain entities and protocol
from src.domain.entities.reading_session import ReadingSession
from src.domain.entities.book import Book, BookMetadata, BookPage
from src.domain.entities.audio import AudioFrame

# Configure logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger('smithy_aws_event_stream.aio').setLevel(logging.INFO)

# Audio configuration
INPUT_SAMPLE_RATE = 16000
OUTPUT_SAMPLE_RATE = 24000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK_SIZE = 1024


class Client:
    """Handles audio I/O and console interaction."""
    
    def __init__(self, nova_sonic: NovaSonic):
        self.nova_sonic = nova_sonic
        self.is_active = False
        
    async def play_audio(self):
        """Play audio responses."""
        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=OUTPUT_SAMPLE_RATE,
            output=True
        )
        
        try:
            while self.is_active:
                audio_data = await self.nova_sonic.get_audio_output()
                stream.write(audio_data)
        except Exception as e:
            print(f"Error playing audio: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
            print("Audio playing stopped.")

    async def capture_audio(self):
        """Capture audio from microphone and send to Nova Sonic."""
        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=INPUT_SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )
        
        print("Starting audio capture. Speak into your microphone...")
        print("Press Enter to stop...")
        
        await self.nova_sonic.start_audio_input()
        
        try:
            while self.is_active:
                audio_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                await self.nova_sonic.send_audio_chunk(audio_data)
                await asyncio.sleep(0.01)
        except Exception as e:
            print(f"Error capturing audio: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
            print("Audio capture stopped.")
            await self.nova_sonic.end_audio_input()


async def test_direct_client():
    """Test the direct NovaSonic client with microphone."""
    # Create Nova Sonic instance
    nova_sonic = NovaSonic()
    
    # Create client
    client = Client(nova_sonic)
    
    # Start session
    await nova_sonic.start_session()
    
    # Mark client as active
    client.is_active = True
    
    # Start audio playback task
    playback_task = asyncio.create_task(client.play_audio())
    
    # Start audio capture task
    capture_task = asyncio.create_task(client.capture_audio())
    
    # Wait for user to press Enter to stop
    await asyncio.get_event_loop().run_in_executor(None, input)
        
    # Signal stop
    client.is_active = False
    
    # Cancel tasks
    tasks = []
    if not playback_task.done():
        tasks.append(playback_task)
    if not capture_task.done():
        tasks.append(capture_task)
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    
    # End session
    await nova_sonic.end_session()
    nova_sonic.is_active = False

    # cancel the response task
    if nova_sonic.response_task and not nova_sonic.response_task.done():
        nova_sonic.response_task.cancel()

    print("Session ended")


async def test_websocket_client():
    """Test the WebSocket API with microphone audio."""
    print("Testing WebSocket API with NovaSonic backend...")
    
    # WebSocket configuration
    WS_URL = "ws://localhost:8000/ws"
    TOKEN = "test-token-123"  # Development token
    STUDENT_ID = "12345678-1234-5678-1234-567812345678"  # Test user from LocalUserProfileProvider
    BOOK_ID = "bathtub-safari"  # Test book from LocalBookProvider
    
    # Setup audio capture
    p = pyaudio.PyAudio()
    input_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=INPUT_SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE
    )
    
    # Setup audio playback
    output_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=OUTPUT_SAMPLE_RATE,
        output=True
    )
    
    print(f"Connecting to WebSocket at {WS_URL}...")
    
    try:
        # Connect to WebSocket with token
        async with websockets.connect(f"{WS_URL}?token={TOKEN}") as websocket:
            print("✓ Connected to WebSocket")
            
            # Send session.create message
            create_message = {
                "type": "session.create",
                "student_id": STUDENT_ID,
                "book_id": BOOK_ID,
                "current_page": 1
            }
            await websocket.send(json.dumps(create_message))
            print(f"✓ Sent session.create message")
            
            # Wait for session.created response
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get("type") == "session.created":
                session_id = response_data.get("session_id")
                print(f"✓ Session created: {session_id}")
            elif response_data.get("type") == "error":
                print(f"✗ Error creating session: {response_data.get('message')}")
                return
            else:
                print(f"✗ Unexpected response: {response_data}")
                return
            
            # Wait for session.ready message
            print("⏳ Waiting for session to be ready...")
            ready_response = await websocket.recv()
            ready_data = json.loads(ready_response)
            
            if ready_data.get("type") == "session.ready":
                print(f"✓ Session ready!")
            else:
                print(f"⚠️  Expected session.ready, got: {ready_data.get('type')}")
            
            print("\n🎤 Speak into your microphone (Ctrl+C to stop)\n")
            
            # Flag to control tasks
            running = True
            
            async def send_audio():
                """Capture audio and send to WebSocket."""
                try:
                    while running:
                        audio_data = input_stream.read(CHUNK_SIZE, exception_on_overflow=False)
                        # Send audio as binary message
                        await websocket.send(audio_data)
                        await asyncio.sleep(0.001)
                except Exception as e:
                    print(f"Error sending audio: {e}")
            
            async def receive_messages():
                """Receive messages from WebSocket (audio and JSON)."""
                nonlocal running
                message_count = 0
                try:
                    while running:
                        message = await websocket.recv()
                        message_count += 1
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        
                        # Check if it's binary (audio) or text (JSON)
                        if isinstance(message, bytes):
                            # Audio response - play it
                            print(f"[{timestamp}] #{message_count} 🔊 BINARY: Audio data ({len(message)} bytes)")
                            output_stream.write(message)
                        else:
                            # JSON message - handle events
                            try:
                                data = json.loads(message)
                                msg_type = data.get("type")
                                
                                # Log full message for debugging
                                print(f"[{timestamp}] #{message_count} 📨 JSON: {json.dumps(data, indent=2)}")
                                
                                if msg_type == "agent.response.started":
                                    print(f"[{timestamp}]     → 🤖 Agent is responding...")
                                elif msg_type == "agent.response.audio":
                                    # Audio data in JSON format (base64 encoded)
                                    # Usually audio comes as binary, but handle this case too
                                    print(f"[{timestamp}]     → 🔊 Audio in JSON format")
                                elif msg_type == "agent.response.completed":
                                    print(f"[{timestamp}]     → ✓ Agent response completed")
                                elif msg_type == "page.completed":
                                    page_num = data.get("page_number")
                                    print(f"[{timestamp}]     → 📖 Page {page_num} completed!")
                                elif msg_type == "session.ended":
                                    print(f"[{timestamp}]     → 🛑 Session ended by server")
                                    running = False
                                elif msg_type == "error":
                                    print(f"[{timestamp}]     → ❌ Error: {data.get('message')}")
                                    print(f"[{timestamp}]     → Error code: {data.get('code')}")
                            except json.JSONDecodeError:
                                print(f"[{timestamp}] #{message_count} ⚠️  Non-JSON text: {message[:100]}")
                except websockets.exceptions.ConnectionClosed:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Connection closed (received {message_count} messages)")
                    running = False
                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Error receiving messages: {e}")
                    import traceback
                    traceback.print_exc()
                    running = False
            
            # Run send and receive concurrently
            send_task = asyncio.create_task(send_audio())
            receive_task = asyncio.create_task(receive_messages())
            
            try:
                # Wait for both tasks
                await asyncio.gather(send_task, receive_task)
            except KeyboardInterrupt:
                print("\n\n🛑 Stopping...")
                running = False
                
                # Cancel tasks
                send_task.cancel()
                receive_task.cancel()
                await asyncio.gather(send_task, receive_task, return_exceptions=True)
                
                # Send session end message
                try:
                    end_message = {"type": "session.end"}
                    await websocket.send(json.dumps(end_message))
                except:
                    pass
    
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
        print("\nMake sure the server is running:")
        print("  uvicorn src.application.api:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Cleanup
        input_stream.stop_stream()
        input_stream.close()
        output_stream.stop_stream()
        output_stream.close()
        p.terminate()
        print("Session ended")


async def test_reading_agent():
    """Test the ReadingAgent protocol implementation."""
    print("Testing NovaSonicReadingAgent...")
    
    # Create mock reading session
    session = ReadingSession(
        student_id="test-student",
        book_id="test-book-001",
        current_page=1
    )
    
    # Create mock book
    book = Book(
        metadata=BookMetadata(
            book_id="test-book-001",
            title="The Cat in the Hat",
            author="Dr. Seuss",
            difficulty_level="beginner",
            total_pages=5
        ),
        pages=[
            BookPage(page_number=1, text="The sun did not shine. It was too wet to play."),
            BookPage(page_number=2, text="So we sat in the house all that cold, cold, wet day."),
            BookPage(page_number=3, text="I sat there with Sally. We sat there, we two."),
            BookPage(page_number=4, text="And I said, How I wish we had something to do!"),
            BookPage(page_number=5, text="Too wet to go out and too cold to play ball."),
        ]
    )
    
    # Create reading agent
    agent = NovaSonicReadingAgent()
    
    # Setup audio capture
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=INPUT_SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE
    )
    
    # Setup audio playback
    playback_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=OUTPUT_SAMPLE_RATE,
        output=True
    )
    
    print(f"Reading session started for '{book.metadata.title}'")
    print(f"Student on page {session.current_page}")
    print("\nInitializing Nova Sonic agent...")
    
    # Pre-initialize the session by creating it directly (not with dummy frame)
    nova = await agent._get_or_create_session(session, book)
    print(f"✓ Session initialized - speak into your microphone (Ctrl+C to stop)\n")
    
    async def capture_and_send():
        """Capture audio and send to agent."""
        while True:
            try:
                audio_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                audio_frame = AudioFrame(
                    pcm_bytes=audio_data,
                    timestamp=datetime.now().timestamp()
                )
                
                # Send audio directly to nova
                await nova.send_audio_chunk(audio_frame.pcm_bytes)
                await asyncio.sleep(0.001)  # Minimal delay
            except Exception as e:
                print(f"Error in capture: {e}")
                break
    
    async def playback_responses():
        """Play audio responses as they arrive."""
        while True:
            try:
                # Get audio directly from Nova Sonic's queue
                audio_bytes = await nova.get_audio_output()
                playback_stream.write(audio_bytes)
            except Exception as e:
                print(f"Error in playback: {e}")
                break
    
    try:
        # Run capture and playback concurrently
        capture_task = asyncio.create_task(capture_and_send())
        playback_task = asyncio.create_task(playback_responses())
        
        # Wait for keyboard interrupt
        await asyncio.gather(capture_task, playback_task)
            
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        # Cleanup
        stream.stop_stream()
        stream.close()
        playback_stream.stop_stream()
        playback_stream.close()
        p.terminate()
        
        # Close agent session
        await agent.close_session(session.id)
        print("Session ended")


async def main():
    """Main entry point - choose which test to run."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--direct':
        await test_direct_client()
    elif len(sys.argv) > 1 and sys.argv[1] == '--agent':
        await test_reading_agent()
    else:
        # Default to WebSocket client
        await test_websocket_client()

if __name__ == "__main__":
    # Set AWS credentials if not using environment variables

    asyncio.run(main())