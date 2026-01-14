"""Book provider protocol."""

from typing import Protocol, runtime_checkable

from ..entities.book import Book, BookMetadata


@runtime_checkable
class BookProvider(Protocol):
    """Protocol for book data providers.
    
    This interface defines methods for retrieving books and their metadata.
    Implementations can use different storage backends (local filesystem + dict,
    DynamoDB + S3, etc.).
    """
    
    def get_book_metadata(self, book_id: str) -> BookMetadata:
        """Retrieve book metadata by book ID.
        
        Args:
            book_id: The unique identifier of the book.
            
        Returns:
            BookMetadata: The book metadata entity.
            
        Raises:
            ValueError: If the book is not found.
        """
        ...
    
    def get_book(self, book_id: str) -> Book:
        """Retrieve a complete book by book ID.
        
        This method retrieves both the metadata and the file content.
        
        Args:
            book_id: The unique identifier of the book.
            
        Returns:
            Book: The complete book entity with metadata and file content.
            
        Raises:
            ValueError: If the book is not found.
            FileNotFoundError: If the book file cannot be accessed.
        """
        ...
    
    def list_books(self) -> list[BookMetadata]:
        """List all available books.
        
        Returns:
            list[BookMetadata]: A list of all book metadata entries.
        """
        ...    
    def get_books_by_reading_level(self, reading_level: int) -> list[BookMetadata]:
        """Retrieve all books suitable for a specific reading level.
        
        Args:
            reading_level: The reading level to filter books by (1-7).
            
        Returns:
            list[BookMetadata]: A list of book metadata for books matching the reading level.
        """
        ...