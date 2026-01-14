"""Page completion detector interface."""

from typing import Protocol


class PageCompletionDetector(Protocol):
    """Protocol for detecting when a page has been completed.
    
    Implementations can use various strategies to determine page completion:
    - Random timer (for testing)
    - Audio analysis (silence detection)
    - ML model predictions
    - Fixed duration
    """
    
    async def start_page(self, session_id: str, page_number: int) -> None:
        """Start monitoring for page completion.
        
        Args:
            session_id: The session ID
            page_number: The current page number
        """
        ...
    
    async def wait_for_page_completion(self) -> bool:
        """Wait for the current page to be completed.
        
        This method should block until the page is determined to be complete.
        
        Returns:
            bool: True if page completed normally, False if cancelled/error
        """
        ...
    
    async def cancel(self) -> None:
        """Cancel the current page monitoring."""
        ...
