from typing import Protocol

from ..entities import OutboundMessage, ReadingSession, Book, AudioFrame


class ReadingAgent(Protocol):

    async def coach(self,
                    session: ReadingSession,
                    book: Book,
                    audio_frame: AudioFrame) -> OutboundMessage:
        """Logic to process audio frame and return audio or page turns."""
        ...