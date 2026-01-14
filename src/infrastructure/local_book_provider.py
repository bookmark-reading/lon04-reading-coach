"""Local file system implementation of BookProvider."""

import os
from typing import Dict

from ..domain.entities.book import Book, BookMetadata
from ..domain.interfaces.book_provider import BookProvider


class LocalBookProvider(BookProvider):
    """Local implementation of the BookProvider protocol.
    
    Stores book metadata in a dictionary and reads book files from 
    the local file system. Useful for testing and development purposes.
    """
    
    def __init__(self, base_path: str = "."):
        """Initialize the local book provider.
        
        Args:
            base_path: Base directory path for book files. Paths in metadata
                      will be resolved relative to this base path.
        """
        self._metadata: Dict[str, BookMetadata] = {}
        self._base_path = base_path
        
        # Pre-populate with test book for e2e testing
        self._metadata["bathtub-safari"] = BookMetadata(
            book_id="bathtub-safari",
            title="Bathtub Safari",
            author="Unknown",
            difficulty_level="beginner",
            total_pages=16,
            book_name="Bathtub Safari",
            reading_level=2,
            path="resources/books/bathtub-safari_en.pdf"
        )
    
    def get_book_metadata(self, book_id: str) -> BookMetadata:
        """Retrieve book metadata by book ID from the in-memory dictionary.
        
        Args:
            book_id: The unique identifier of the book.
            
        Returns:
            BookMetadata: The book metadata entity.
            
        Raises:
            ValueError: If the book is not found.
        """
        if book_id not in self._metadata:
            raise ValueError(f"Book with id {book_id} not found")
        
        return self._metadata[book_id]
    
    def get_book(self, book_id: str) -> Book:
        """Retrieve a complete book by book ID.
        
        Retrieves metadata from the dictionary and reads the file from
        the local file system.
        
        Args:
            book_id: The unique identifier of the book.
            
        Returns:
            Book: The complete book entity with metadata and file content.
            
        Raises:
            ValueError: If the book metadata is not found.
            FileNotFoundError: If the book file cannot be accessed.
        """
        metadata = self.get_book_metadata(book_id)
        
        # Construct the full file path
        file_path = os.path.join(self._base_path, metadata.path)
        
        # Read the file content
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Book file not found at path: {file_path}"
            )
        except IOError as e:
            raise IOError(f"Error reading book file: {e}")
        
        return Book(
            book_id=book_id,
            file_content=file_content,
            metadata=metadata
        )
    
    def list_books(self) -> list[BookMetadata]:
        """List all available books.
        
        Returns:
            list[BookMetadata]: A list of all book metadata entries.
        """
        return list(self._metadata.values())
    
    def add_book(self, metadata: BookMetadata) -> None:
        """Add or update book metadata in the dictionary.
        
        Args:
            metadata: The book metadata to add or update.
        """
        self._metadata[metadata.book_id] = metadata
    
    def remove_book(self, book_id: str) -> None:
        """Remove book metadata from the dictionary.
        
        Args:
            book_id: The unique identifier of the book to remove.
            
        Raises:
            ValueError: If the book is not found.
        """
        if book_id not in self._metadata:
            raise ValueError(f"Book with id {book_id} not found")
        
        del self._metadata[book_id]
    
    def get_books_by_reading_level(self, reading_level: int) -> list[BookMetadata]:
        """Retrieve all books suitable for a specific reading level.
        
        Args:
            reading_level: The reading level to filter books by (1-7).
            
        Returns:
            list[BookMetadata]: A list of book metadata for books matching the reading level.
        """
        return [book for book in self._metadata.values() if book.reading_level == reading_level]
