"""
Setup local environment with sample data and run the backend server.

This script:
1. Sets up a sample book in the LocalBookProvider
2. Creates a sample user profile in the LocalUserProfileProvider
3. Starts the FastAPI backend server

Run this before testing with the Jupyter notebook.
"""

import asyncio
import sys
import os
from pathlib import Path
from uuid import UUID

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.application.api import app, book_provider, user_profile_provider
from src.domain.entities.book import BookMetadata
from src.domain.entities.user_profile import UserProfile


def setup_sample_data():
    """Set up sample book and user profile."""
    
    print("=" * 60)
    print("Setting up sample data...")
    print("=" * 60)
    
    # 1. Add a sample book
    sample_book = BookMetadata(
        book_id="book-001",
        book_name="The Bathtub Safari",
        reading_level=3,
        path="books/bathtub_safari.txt"
    )
    book_provider.add_book(sample_book)
    print(f"\n✓ Added book: {sample_book.book_name}")
    print(f"  - Book ID: {sample_book.book_id}")
    print(f"  - Reading Level: {sample_book.reading_level}")
    
    # Add another book for reading level 5
    sample_book_2 = BookMetadata(
        book_id="book-002",
        book_name="Adventure Island",
        reading_level=5,
        path="books/adventure_island.txt"
    )
    book_provider.add_book(sample_book_2)
    print(f"\n✓ Added book: {sample_book_2.book_name}")
    print(f"  - Book ID: {sample_book_2.book_id}")
    print(f"  - Reading Level: {sample_book_2.reading_level}")
    
    # 2. Create a sample user profile
    sample_user_id = UUID("12345678-1234-5678-1234-567812345678")
    sample_profile = UserProfile(
        first_name="Alice",
        last_name="Johnson",
        current_reading_level=5,
        sessions=[]
    )
    user_profile_provider.add_user(sample_user_id, sample_profile)
    print(f"\n✓ Added user profile: {sample_profile.first_name} {sample_profile.last_name}")
    print(f"  - User ID: {sample_user_id}")
    print(f"  - Reading Level: {sample_profile.current_reading_level}")
    
    print("\n" + "=" * 60)
    print("Sample data setup complete!")
    print("=" * 60)
    print("\nYou can now:")
    print("1. Use the Jupyter notebook to connect and test audio streaming")
    print("2. Connect with WebSocket URL: ws://localhost:8000/ws?token=test-token")
    print(f"3. Use student_id: {sample_user_id}")
    print(f"4. Use book_id: {sample_book.book_id}")
    print("\n" + "=" * 60 + "\n")


def run_server():
    """Run the FastAPI server."""
    import uvicorn
    
    # Setup sample data first
    setup_sample_data()
    
    # Start the server
    print("Starting FastAPI server on http://localhost:8000")
    print("Press Ctrl+C to stop\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
