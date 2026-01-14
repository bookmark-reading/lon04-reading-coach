"""Book entities for the reading coach application."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class BookMetadata(BaseModel):
    """Book metadata containing information about a book.
    
    This entity stores metadata about a book including its name, 
    reading age level, and the path/key to the actual book file.
    """
    
    model_config = ConfigDict(frozen=True)
    
    book_id: str = Field(description="Unique identifier for the book")
    book_name: str = Field(min_length=1, max_length=200, description="Title of the book")
    reading_level: int = Field(ge=1, le=7, description="Recommended reading level (1-7)")
    total_pages: int = Field(ge=1, description="Total number of pages in the book")
    path: str = Field(min_length=1, description="Path or key to the book file (local path or S3 key)")
    content: Optional[bytes] = Field(default=None, description="The actual book file content")


class Book(BaseModel):
    """Book entity containing the book metadata and file content.
    
    This entity represents a complete book with both its metadata
    and the actual file content.
    """
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    book_id: str = Field(description="Unique identifier for the book")
    file_content: bytes = Field(description="The actual book file content")
    metadata: BookMetadata = Field(description="Book metadata")
