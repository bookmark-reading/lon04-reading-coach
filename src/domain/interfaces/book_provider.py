"""Book provider protocol and implementation."""

from typing import Protocol, runtime_checkable
import boto3
import os
import io
from PyPDF2 import PdfReader

from ..entities.book import Book, BookMetadata


@runtime_checkable
class BookProvider(Protocol):
    """Protocol for book data providers.
    
    This interface defines methods for retrieving books and their metadata.
    Implementations can use different storage backends (DynamoDB + S3, etc.).
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
            reading_level: The reading level to filter books by (e.g., "1", "2", etc.).
            
        Returns:
            list[BookMetadata]: A list of book metadata for books matching the reading level.
        """
        ...


class S3BookProvider:
    """S3-based implementation of BookProvider.
    
    This implementation stores books in S3 and retrieves them on demand.
    Book filenames follow the format: "L.{level} - {title}.pdf"
    """
    
    def __init__(self, bucket_name: str = "bookmark-hackathon-source-files"):
        """Initialize the S3 book provider.
        
        Args:
            bucket_name: The name of the S3 bucket containing books.
        """
        self.bucket_name = bucket_name
        self.s3_client = boto3.client("s3")
    
    def get_book_metadata(self, book_id: str) -> BookMetadata:
        """Retrieve book metadata by book ID (S3 key).
        
        Args:
            book_id: The S3 key of the book.
            
        Returns:
            BookMetadata: The book metadata entity.
            
        Raises:
            ValueError: If the book is not found.
        """
        try:
            # Check if object exists and get its metadata
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=book_id
            )
            
            # Download to get page count
            file_obj = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=book_id
            )
            content = file_obj["Body"].read()
            
            # Parse PDF to get page count
            pdf_file = io.BytesIO(content)
            pdf_reader = PdfReader(pdf_file)
            num_pages = len(pdf_reader.pages)
            
            # Parse filename to extract title and reading level
            filename = os.path.basename(book_id)
            name_without_ext = os.path.splitext(filename)[0]
            
            if " - " in name_without_ext:
                level_part, title_part = name_without_ext.split(" - ", 1)
                reading_level = level_part.replace("L.", "").strip()
                title = title_part.strip()
            else:
                reading_level = 1  # Default level if not specified
                title = name_without_ext
            
            return BookMetadata(
                book_id=book_id,
                book_name=title,
                reading_level=int(reading_level),
                total_pages=num_pages,
                path=f"s3://{self.bucket_name}/{book_id}"
            )
            
        except self.s3_client.exceptions.NoSuchKey:
            raise ValueError(f"Book with id {book_id} not found")
    
    def get_book(self, book_id: str) -> Book:
        """Retrieve a complete book by book ID (S3 key).
        
        Args:
            book_id: The S3 key of the book.
            
        Returns:
            Book: The complete book entity with metadata and file content.
            
        Raises:
            ValueError: If the book is not found.
            FileNotFoundError: If the book file cannot be accessed.
        """
        try:
            # Get file content
            file_obj = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=book_id
            )
            file_content = file_obj["Body"].read()
            
            # Get metadata (this will parse the file again, but ensures consistency)
            metadata = self.get_book_metadata(book_id)
            
            return Book(
                book_id=book_id,
                file_content=file_content,
                metadata=metadata
            )
            
        except self.s3_client.exceptions.NoSuchKey:
            raise FileNotFoundError(f"Book file not found: {book_id}")

    def list_books(self) -> list[BookMetadata]:
        """List all available books in the S3 bucket.
        
        Returns:
            list[BookMetadata]: A list of all book metadata entries.
        """
        books = []
        
        # List all objects in the bucket
        paginator = self.s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket_name)
        
        for page in pages:
            if "Contents" not in page:
                continue
                
            for obj in page["Contents"]:
                key = obj["Key"]
                try:
                    metadata = self.get_book_metadata(key)
                    books.append(metadata)
                except Exception:
                    # Skip files that can't be parsed as books
                    continue
        
        return books
    
    def get_books_by_reading_level(self, reading_level: int) -> list[BookMetadata]:
        """Retrieve all books suitable for a specific reading level.
        
        Args:
            reading_level: The reading level to filter books by (e.g., 1, 2, etc.).
        Returns:
            list[BookMetadata]: A list of book metadata for books matching the reading level.
        """
        prefix = f"L.{reading_level}"
        
        # List objects that start with the prefix
        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix
        )
        
        if "Contents" not in response:
            return []
        
        books = []
        for obj in response["Contents"]:
            key = obj["Key"]
            try:
                metadata = self.get_book_metadata(key)
                books.append(metadata)
            except Exception:
                # Skip files that can't be parsed
                continue
        
        return books