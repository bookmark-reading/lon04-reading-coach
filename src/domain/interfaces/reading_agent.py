from typing import Protocol, List

from ..entities import OutboundMessage, ReadingSession, Book, AudioFrame


class ReadingAgent(Protocol):

    async def coach(self,
                    session: ReadingSession,
                    book: Book,
                    audio: List[AudioFrame]) -> OutboundMessage:
        """Logic to process audio and return audio or page turns."""
        ...