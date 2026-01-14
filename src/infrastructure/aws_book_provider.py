"""AWS implementation of BookProvider using DynamoDB and S3."""

from typing import Any, Dict

import boto3
import io
from PyPDF2 import PdfReader

from ..domain.entities.book import Book, BookMetadata
from ..domain.interfaces.book_provider import BookProvider


class AWSBookProvider(BookProvider):
    """AWS implementation of the BookProvider protocol.
    
    Stores book metadata in DynamoDB and book files in S3.
    """
    
    def __init__(
        self, 
        table_name: str, 
        bucket_name: str, 
        region_name: str = "us-east-1"
    ):
        """Initialize the AWS book provider.
        
        Args:
            table_name: The name of the DynamoDB table for book metadata.
            bucket_name: The name of the S3 bucket for book files.
            region_name: AWS region name (default: us-east-1).
        """
        self.table_name = table_name
        self.bucket_name = bucket_name
        self.region_name = region_name
        
        # Initialize DynamoDB client
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.table = self.dynamodb.Table(table_name)
        
        # Initialize S3 client
        self.s3_client = boto3.client("s3", region_name=region_name)
    
    def get_book_metadata(self, book_id: str, include_content: bool = True) -> BookMetadata:
        """Retrieve book metadata by book ID from DynamoDB.
        
        Args:
            book_id: The unique identifier of the book.
            include_content: If True, download and populate the content field from S3.
                            Defaults to False for performance (content is large).
            
        Returns:
            BookMetadata: The book metadata entity.
            
        Raises:
            ValueError: If the book is not found.
        """
        # DynamoDB table uses 'bookId' as the key, not 'book_id'
        response = self.table.get_item(Key={"bookId": book_id})
        
        if "Item" not in response:
            raise ValueError(f"Book with id {book_id} not found")
        
        metadata = self._item_to_book_metadata(response["Item"])
        
        # Optionally download content from S3
        if include_content:
            metadata = self._load_content_for_metadata(metadata)
        
        return metadata
    
    def get_book(self, book_id: str) -> Book:
        """Retrieve a complete book by book ID.
        
        Retrieves metadata from DynamoDB and JSON content from S3.
        
        Args:
            book_id: The unique identifier of the book.
            
        Returns:
            Book: The complete book entity with metadata and JSON file content.
            
        Raises:
            ValueError: If the book metadata is not found.
        """
        metadata = self.get_book_metadata(book_id, include_content=False)
        
        # Load JSON content from S3 using metadata.content field
        if metadata.content and metadata.content.startswith('s3://'):
            import json
            
            s3_path = metadata.content.replace('s3://', '')
            bucket_name = s3_path.split('/')[0]
            object_key = '/'.join(s3_path.split('/')[1:])
            
            try:
                response = self.s3_client.get_object(Bucket=bucket_name, Key=object_key)
                file_content = response['Body'].read()
            except Exception:
                file_content = json.dumps({"book_id": book_id, "pages": []}).encode('utf-8')
        else:
            import json
            file_content = json.dumps({"book_id": book_id, "pages": []}).encode('utf-8')
        
        return Book(
            book_id=book_id,
            file_content=file_content,
            metadata=metadata
        )
    
    def list_books(self) -> list[BookMetadata]:
        """List all available books from DynamoDB.
        
        Returns:
            list[BookMetadata]: A list of all book metadata entries.
        """
        response = self.table.scan()
        books = [self._item_to_book_metadata(item) for item in response.get("Items", [])]
        
        # Handle pagination if there are more items
        while "LastEvaluatedKey" in response:
            response = self.table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            books.extend([self._item_to_book_metadata(item) for item in response.get("Items", [])])
        
        return books
    
    def _item_to_book_metadata(self, item: Dict[str, Any]) -> BookMetadata:
        """Convert a DynamoDB item to a BookMetadata entity.
        
        Maps DynamoDB schema (bookId, title, grade, s3Key) to BookMetadata schema.
        
        Args:
            item: The DynamoDB item with keys: bookId, title, grade, s3Key
            
        Returns:
            BookMetadata: The book metadata entity.
        """
        grade_value = item.get("grade")
        if hasattr(grade_value, '__int__'):
            reading_level = int(grade_value)
        else:
            reading_level = int(grade_value) if grade_value else 1
        
        s3_key = item.get("s3Key", "")
        if s3_key and not s3_key.startswith("s3://"):
            path = f"s3://{self.bucket_name}/{s3_key}"
        else:
            path = s3_key or f"s3://{self.bucket_name}/"
        
        # Derive JSON content path from PDF path
        content = path.replace('.pdf', '.json') if path.endswith('.pdf') else None
        
        return BookMetadata(
            book_id=item["bookId"],
            book_name=item["title"],
            reading_level=reading_level,
            total_pages=item.get("total_pages", 1),
            path=path,
            content=content
        )
    
    def _load_content_for_metadata(self, metadata: BookMetadata) -> BookMetadata:
        """Load PDF content from S3 for a given BookMetadata.
        
        Returns a new BookMetadata instance with the content field populated.
        If loading fails, logs a warning and returns the original metadata.
        """
        try:
            s3_key = metadata.path
            if s3_key.startswith("s3://"):
                parts = s3_key.split("/", 3)
                if len(parts) >= 4:
                    s3_key = parts[3]
                elif len(parts) >= 2:
                    s3_key = parts[-1]
            
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            content = response["Body"].read()

            # Compute accurate page count from the PDF bytes.
            pdf_file = io.BytesIO(content)
            pdf_reader = PdfReader(pdf_file)
            total_pages = len(pdf_reader.pages)
            
            return BookMetadata(
                book_id=metadata.book_id,
                book_name=metadata.book_name,
                reading_level=metadata.reading_level,
                total_pages=total_pages,
                path=metadata.path,
                content=content,
            )
        except (self.s3_client.exceptions.NoSuchKey, Exception):
            # On failure, return the original metadata without content
            # and preserve whatever total_pages was already set to.
            return metadata
    
    def put_book_metadata(self, metadata: BookMetadata) -> None:
        """Store book metadata in DynamoDB.
        
        Maps BookMetadata schema to DynamoDB schema (bookId, title, grade, s3Key).
        
        Args:
            metadata: The book metadata to store.
        """
        # Extract S3 key from path (remove s3://bucket/ prefix if present)
        s3_key = metadata.path
        if s3_key.startswith("s3://"):
            parts = s3_key.split("/", 3)
            if len(parts) >= 4:
                s3_key = parts[3]
            elif len(parts) >= 2:
                s3_key = parts[-1]
        
        self.table.put_item(
            Item={
                "bookId": metadata.book_id,
                "title": metadata.book_name,
                "grade": metadata.reading_level,
                "s3Key": s3_key,
                "total_pages": metadata.total_pages
            }
        )
    
    def upload_book_file(self, book_id: str, file_content: bytes, s3_key: str) -> None:
        """Upload a book file to S3.
        
        Args:
            book_id: The unique identifier of the book.
            file_content: The book file content to upload.
            s3_key: The S3 key (path) where the file will be stored.
        """
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=file_content
        )
    
    def get_books_by_reading_level(self, reading_level: int) -> list[BookMetadata]:
        """Retrieve all books suitable for a specific reading level from DynamoDB.
        
        Args:
            reading_level: The reading level to filter books by (1-7).
            
        Returns:
            list[BookMetadata]: A list of book metadata for books matching the reading level.
        """
        # Query with filter expression - DynamoDB uses 'grade' not 'reading_level'
        # Use 'grade' field from DynamoDB schema
        response = self.table.scan(
            FilterExpression="grade = :level",
            ExpressionAttributeValues={":level": reading_level}
        )
        
        # Convert to metadata and eagerly load content so callers can use PDFs directly.
        books = [
            self._load_content_for_metadata(self._item_to_book_metadata(item))
            for item in response.get("Items", [])
        ]
        
        # Handle pagination if there are more items
        while "LastEvaluatedKey" in response:
            response = self.table.scan(
                FilterExpression="grade = :level",
                ExpressionAttributeValues={":level": reading_level},
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            books.extend(
                self._load_content_for_metadata(self._item_to_book_metadata(item))
                for item in response.get("Items", [])
            )
        
        return books
