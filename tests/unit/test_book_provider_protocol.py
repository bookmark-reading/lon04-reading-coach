"""Test that implementations conform to the BookProvider protocol."""

import pytest

from src.domain.entities.book import Book, BookMetadata
from src.domain.interfaces.book_provider import BookProvider


class InMemoryBookProvider:
    """Simple in-memory implementation used to validate the protocol contract."""

    def __init__(self) -> None:
        self._books: dict[str, tuple[BookMetadata, bytes]] = {}

    def add_book(self, metadata: BookMetadata, file_content: bytes) -> None:
        self._books[metadata.book_id] = (metadata, file_content)

    def get_book_metadata(self, book_id: str) -> BookMetadata:
        if book_id not in self._books:
            raise ValueError(f"Book with id {book_id} not found")
        return self._books[book_id][0]

    def get_book(self, book_id: str) -> Book:
        if book_id not in self._books:
            raise ValueError(f"Book with id {book_id} not found")
        metadata, file_content = self._books[book_id]
        return Book(book_id=book_id, file_content=file_content, metadata=metadata)

    def list_books(self) -> list[BookMetadata]:
        return [metadata for (metadata, _content) in self._books.values()]

    def get_books_by_reading_level(self, reading_level: int) -> list[BookMetadata]:
        return [
            metadata
            for (metadata, _content) in self._books.values()
            if metadata.reading_level == reading_level
        ]


@pytest.fixture
def provider() -> InMemoryBookProvider:
    provider = InMemoryBookProvider()
    provider.add_book(
        BookMetadata(
            book_id="book-1",
            book_name="Test Book",
            reading_level=3,
            total_pages=10,
            path="memory://book-1.pdf",
        ),
        b"%PDF-FAKE%",
    )
    return provider


def test_in_memory_provider_implements_protocol(provider: InMemoryBookProvider):
    """Test that InMemoryBookProvider implements BookProvider protocol."""
    assert isinstance(provider, BookProvider)

    # Required methods exist and are callable (runtime structural check).
    for method_name in (
        "get_book_metadata",
        "get_book",
        "list_books",
        "get_books_by_reading_level",
    ):
        assert hasattr(provider, method_name)
        assert callable(getattr(provider, method_name))


def test_provider_returns_expected_entities(provider: InMemoryBookProvider):
    """Test basic expected behavior for protocol methods."""
    metadata = provider.get_book_metadata("book-1")
    assert isinstance(metadata, BookMetadata)
    assert metadata.book_id == "book-1"
    assert metadata.reading_level == 3

    book = provider.get_book("book-1")
    assert isinstance(book, Book)
    assert book.book_id == "book-1"
    assert book.file_content == b"%PDF-FAKE%"
    assert book.metadata == metadata


def test_provider_not_found_raises_value_error(provider: InMemoryBookProvider):
    with pytest.raises(ValueError):
        provider.get_book_metadata("does-not-exist")
    with pytest.raises(ValueError):
        provider.get_book("does-not-exist")


def test_protocol_allows_interchangeable_use(provider: InMemoryBookProvider):
    """Smoke test: a consumer can type against the Protocol."""
    book_provider: BookProvider = provider
    assert book_provider.list_books()
    assert book_provider.get_books_by_reading_level(3)[0].book_id == "book-1"

