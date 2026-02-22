"""Parser for biquge-family sites (biquge.info, biquge.tv, xbiquge.la)."""
import re
from bs4 import BeautifulSoup
from app.workers.parsers.base import BaseCrawlParser

BIQUGE_DOMAINS = {"biquge.info", "biquge.tv", "xbiquge.la"}


class BiqugeParser(BaseCrawlParser):
    """Handles biquge-family sites that share the same HTML structure."""

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower().lstrip("www.")
        return domain in BIQUGE_DOMAINS

    def chapter_url(self, source_url: str, chapter_number: int) -> str:
        """source_url is the book index page, e.g. https://biquge.info/book/12345/
        Chapter URLs follow: https://biquge.info/book/12345/{chapter_number}.html
        """
        base = source_url.rstrip("/")
        return f"{base}/{chapter_number}.html"

    def parse_content(self, html: str) -> str:
        """Extract chapter text from biquge HTML page."""
        soup = BeautifulSoup(html, "lxml")

        # Try common content div IDs/classes used across biquge variants
        content_div = (
            soup.find("div", id="content")
            or soup.find("div", id="chaptercontent")
            or soup.find("div", class_="read-content")
            or soup.find("div", class_="content")
        )

        if not content_div:
            return ""

        # Remove script/style tags that might be inside
        for tag in content_div.find_all(["script", "style"]):
            tag.decompose()

        # Get text, preserving paragraph breaks
        text = content_div.get_text(separator="\n")

        # Clean up excessive whitespace and common noise
        lines = [line.strip() for line in text.splitlines()]
        lines = [line for line in lines if line and not _is_noise(line)]
        return "\n\n".join(lines)


def _is_noise(line: str) -> bool:
    """Filter out common ad/navigation text found in scraped pages."""
    noise_patterns = [
        r"biquge", r"笔趣阁", r"www\.", r"请收藏", r"书友推荐",
        r"手机阅读", r"本章未完", r"请翻页",
    ]
    lower = line.lower()
    return any(re.search(p, lower) for p in noise_patterns)
