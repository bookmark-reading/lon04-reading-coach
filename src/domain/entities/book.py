"""Book entities for the reading coach application."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BookMetadata(BaseModel):
    """Book metadata containing information about a book.
    
    This entity stores metadata about a book including its name, 
    reading age level, and the path/key to the actual book file.
    """
    
    model_config = ConfigDict(frozen=True)
    
    book_id: str = Field(description="Unique identifier for the book")
    title: str = Field(min_length=1, max_length=200, description="Title of the book")
    author: str = Field(default="Unknown", description="Author of the book")
    difficulty_level: str = Field(default="beginner", description="Difficulty level of the book")
    total_pages: int = Field(ge=1, description="Total number of pages in the book")
    
    # Legacy fields for backwards compatibility
    book_name: Optional[str] = Field(None, min_length=1, max_length=200, description="Title of the book (legacy)")
    reading_level: Optional[int] = Field(None, ge=1, le=7, description="Recommended reading level (1-7) (legacy)")
    path: Optional[str] = Field(None, min_length=1, description="Path or key to the book file (legacy)")


class BookPage(BaseModel):
    """Represents a single page in a book."""
    
    page_number: int = Field(ge=1, description="Page number")
    text: str = Field(description="Text content of the page")
    image_url: Optional[str] = Field(None, description="Optional URL to page image")


class Book(BaseModel):
    """Book entity containing the book metadata and pages.
    
    This entity represents a complete book with both its metadata
    and the actual page content.
    """
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    metadata: BookMetadata = Field(description="Book metadata")
    pages: list[BookPage] = Field(default_factory=list, description="List of book pages")
    
    # Legacy fields for backwards compatibility
    book_id: Optional[str] = Field(None, description="Unique identifier for the book (legacy)")
    file_content: Optional[bytes] = Field(None, description="The actual book file content (legacy)")
    
    def __init__(self, **data):
        """Initialize Book and sync book_id with metadata if needed."""
        super().__init__(**data)
        if self.book_id is None and self.metadata:
            object.__setattr__(self, 'book_id', self.metadata.book_id)
