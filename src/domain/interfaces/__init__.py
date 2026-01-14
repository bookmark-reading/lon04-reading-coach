"""Domain interfaces for the reading coach application."""

from .book_provider import BookProvider
from .user_profile_provider import UserProfileProvider

__all__ = ["BookProvider", "UserProfileProvider"]
