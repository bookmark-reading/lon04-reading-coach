"""Audio-related entities."""

from uuid import uuid4


class AudioFrame:
    """Container for audio data with metadata."""
    
    def __init__(self, pcm_bytes: bytes, timestamp: float):
        self.pcm_bytes = pcm_bytes
        self.timestamp = timestamp
        self.frame_id = str(uuid4())
