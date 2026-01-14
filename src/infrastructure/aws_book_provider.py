"""AWS implementation of BookProvider using DynamoDB and S3."""

from typing import Any, Dict

import boto3

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
    
    def get_book_metadata(self, book_id: str) -> BookMetadata:
        """Retrieve book metadata by book ID from DynamoDB.
        
        Args:
            book_id: The unique identifier of the book.
            
        Returns:
            BookMetadata: The book metadata entity.
            
        Raises:
            ValueError: If the book is not found.
        """
        response = self.table.get_item(Key={"book_id": book_id})
        
        if "Item" not in response:
            raise ValueError(f"Book with id {book_id} not found")
        
        return self._item_to_book_metadata(response["Item"])
    
    def get_book(self, book_id: str) -> Book:
        """Retrieve a complete book by book ID.
        
        Retrieves metadata from DynamoDB and the file from S3.
        
        Args:
            book_id: The unique identifier of the book.
            
        Returns:
            Book: The complete book entity with metadata and file content.
            
        Raises:
            ValueError: If the book metadata is not found.
            FileNotFoundError: If the book file cannot be accessed from S3.
        """
        metadata = self.get_book_metadata(book_id)
        
        # Download file from S3
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=metadata.path
            )
            file_content = response["Body"].read()
        except self.s3_client.exceptions.NoSuchKey:
            raise FileNotFoundError(
                f"Book file not found in S3 at path: {metadata.path}"
            )
        except Exception as e:
            raise IOError(f"Error reading book file from S3: {e}")
        
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
        
        Args:
            item: The DynamoDB item.
            
        Returns:
            BookMetadata: The book metadata entity.
        """
        return BookMetadata(
            book_id=item["book_id"],
            book_name=item["book_name"],
            reading_level=int(item["reading_level"]),
            path=item["path"]
        )
    
    def put_book_metadata(self, metadata: BookMetadata) -> None:
        """Store book metadata in DynamoDB.
        
        Args:
            metadata: The book metadata to store.
        """
        self.table.put_item(
            Item={
                "book_id": metadata.book_id,
                "book_name": metadata.book_name,
                "reading_level": metadata.reading_level,
                "path": metadata.path
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
        # Query with filter expression
        response = self.table.scan(
            FilterExpression="reading_level = :level",
            ExpressionAttributeValues={":level": reading_level}
        )
        
        books = [self._item_to_book_metadata(item) for item in response.get("Items", [])]
        
        # Handle pagination if there are more items
        while "LastEvaluatedKey" in response:
            response = self.table.scan(
                FilterExpression="reading_level = :level",
                ExpressionAttributeValues={":level": reading_level},
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            books.extend([self._item_to_book_metadata(item) for item in response.get("Items", [])])
        
        return books
