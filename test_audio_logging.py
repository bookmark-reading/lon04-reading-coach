#!/usr/bin/env python3
"""Simple test to verify audio is being received by the backend."""

import asyncio
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simulate what the frontend sends
STUDENT_ID = "12345678-1234-5678-1234-567812345678"
BOOK_ID = "monkey-business"

async def test_audio_reception():
    """Test that backend receives and logs audio."""
    import websockets
    
    WS_URL = "ws://localhost:8000/ws?token=demo-token"
    
    logger.info(f"Connecting to {WS_URL}")
    
    async with websockets.connect(WS_URL) as ws:
        logger.info("✅ Connected")
        
        # Send session.create
        await ws.send(json.dumps({
            "type": "session.create",
            "student_id": STUDENT_ID,
            "book_id": BOOK_ID,
            "current_page": 1
        }))
        logger.info("📤 Sent session.create")
        
        # Wait for session.ready
        msg = await ws.recv()
        data = json.loads(msg)
        logger.info(f"📥 Received: {data.get('type')}")
        
        if data.get("type") == "session.ready":
            logger.info(f"✅ Session ready: {data.get('session_id')}")
            
            # Send fake audio chunks
            logger.info("🎤 Sending audio chunks...")
            for i in range(20):
                # Send 1024 bytes of fake PCM audio
                fake_audio = bytes([0] * 1024)
                await ws.send(fake_audio)
                logger.info(f"  Sent chunk {i+1}/20")
                await asyncio.sleep(0.1)
            
            logger.info("✅ All audio chunks sent")
            logger.info("📊 Check backend logs for audio processing messages")
            
            # Wait a bit for responses
            await asyncio.sleep(2)
            
            # Try to receive any messages
            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    if isinstance(msg, bytes):
                        logger.info(f"📥 Received audio response: {len(msg)} bytes")
                    else:
                        data = json.loads(msg)
                        logger.info(f"📥 Received: {data}")
            except asyncio.TimeoutError:
                logger.info("⏱️  No more messages")

if __name__ == "__main__":
    asyncio.run(test_audio_reception())
