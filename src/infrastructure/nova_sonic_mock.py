"""Mock Nova Sonic implementation for testing without SDK."""
import asyncio
import logging

logger = logging.getLogger(__name__)


class NovaSonic:
    """Mock Nova Sonic client that simulates responses."""
    
    def __init__(self, model_id='amazon.nova-sonic-v1:0', region='us-east-1'):
        self.model_id = model_id
        self.region = region
        self.is_active = False
        self.audio_queue = asyncio.Queue()
        self.text_queue = asyncio.Queue()
        self.response_task = None
        self.audio_chunks_received = 0
        
    async def start_session(self, system_prompt: str = None):
        """Start mock session."""
        logger.info(f"🎭 MOCK: Starting Nova Sonic session")
        logger.info(f"🎭 MOCK: System prompt: {system_prompt[:100]}...")
        self.is_active = True
        self.response_task = asyncio.create_task(self._mock_responses())
        
    async def start_audio_input(self):
        """Start mock audio input."""
        logger.info("🎭 MOCK: Audio input started")
        
    async def send_audio_chunk(self, audio_bytes):
        """Receive audio chunk."""
        self.audio_chunks_received += 1
        if self.audio_chunks_received % 20 == 0:
            logger.info(f"🎭 MOCK: Received {self.audio_chunks_received} audio chunks")
            # Simulate text feedback
            await self.text_queue.put(f"Great reading! Keep going!")
            
    async def end_audio_input(self):
        """End mock audio input."""
        logger.info("🎭 MOCK: Audio input ended")
        
    async def end_session(self):
        """End mock session."""
        logger.info("🎭 MOCK: Ending session")
        self.is_active = False
        if self.response_task:
            self.response_task.cancel()
            
    async def get_audio_output(self):
        """Get mock audio output."""
        return await self.audio_queue.get()
        
    async def get_text_output(self):
        """Get mock text output."""
        return await self.text_queue.get()
        
    async def _mock_responses(self):
        """Generate mock responses."""
        try:
            while self.is_active:
                await asyncio.sleep(5)
                if self.audio_chunks_received > 0:
                    await self.text_queue.put("Nice job reading!")
        except asyncio.CancelledError:
            pass
