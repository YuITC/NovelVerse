"""Base class for chapter content parsers."""
from abc import ABC, abstractmethod


class BaseCrawlParser(ABC):
    """Abstract parser for a specific novel website."""

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Return True if this parser can handle the given source URL."""
        ...

    @abstractmethod
    def chapter_url(self, source_url: str, chapter_number: int) -> str:
        """Build the full URL for a specific chapter."""
        ...

    @abstractmethod
    def parse_content(self, html: str) -> str:
        """Extract and clean chapter text from raw HTML."""
        ...
