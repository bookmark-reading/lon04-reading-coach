"""Simple stub implementation of ReadingAgent for testing and development."""

import logging
import random
from typing import List

from ..domain.entities import OutboundMessage, ReadingSession, Book, AudioFrame
from ..domain.entities.messages import NoticeMessage, PageChangeMessage, FeedbackMessage

logger = logging.getLogger(__name__)


class SimpleReadingAgent:
    """
    A simple stub implementation of the ReadingAgent interface.
    
    This agent doesn't perform real AI coaching, but returns simple responses
    for testing and development purposes. It simulates page turn decisions
    based on accumulated audio buffer size.
    """
    
    def __init__(self):
        """Initialize the simple reading agent."""
        self._audio_count = 0
        self._page_turn_threshold = random.randint(8, 15)  # Random threshold per page
    
    async def coach(
        self,
        session: ReadingSession,
        book: Book,
        audio: List[AudioFrame]
    ) -> OutboundMessage:
        """
        Process audio and return a simple response.
        
        This stub implementation:
        - Counts audio chunks
        - Randomly decides to turn pages after accumulating enough audio
        - Provides simple feedback messages
        
        Args:
            session: The current reading session
            book: The book being read
            audio: Audio frames to process
            
        Returns:
            Either a notice, feedback, or page turn message
        """
        logger.debug(f"SimpleReadingAgent processing {len(audio)} audio frames")
        
        self._audio_count += 1
        
        # Simulate page turn decision after threshold
        if self._audio_count >= self._page_turn_threshold:
            # Agent decides which page to go to (usually next, but could be any page)
            # For this simple implementation, mostly go to next page, but occasionally skip ahead
            if session.current_page < book.metadata.total_pages:
                # 90% of the time go to next page, 10% skip ahead
                if random.random() < 0.9:
                    target_page = session.current_page + 1
                    direction = "next"
                else:
                    # Skip ahead 1-2 pages (if possible)
                    skip_amount = random.randint(1, 2)
                    target_page = min(
                        session.current_page + skip_amount,
                        book.metadata.total_pages
                    )
                    direction = "next"  # Still "next" even if skipping
                
                logger.info(
                    f"SimpleReadingAgent deciding to turn to page {target_page} "
                    f"from {session.current_page} (accumulated {self._audio_count} audio chunks)"
                )
                
                # Reset counter and set new threshold for next page
                self._audio_count = 0
                self._page_turn_threshold = random.randint(8, 15)
                
                return PageChangeMessage(
                    page=target_page,
                    direction=direction
                )
            else:
                logger.info("SimpleReadingAgent: Already on last page, no page turn")
                return FeedbackMessage(
                    message="Great job finishing the book!",
                    feedback_type="positive"
                )
        
        # Occasionally provide encouragement
        if self._audio_count % 3 == 0:
            return FeedbackMessage(
                message="Keep reading!",
                feedback_type="encouragement"
            )
        
        # Default: just acknowledge audio receipt
        return NoticeMessage(
            message="Listening..."
        )
