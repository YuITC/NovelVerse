import bleach

ALLOWED_TAGS = ["b", "i", "em", "strong", "p", "br", "ul", "ol", "li", "a"]
ALLOWED_ATTRS = {"a": ["href", "title"]}


def sanitize_html(text: str) -> str:
    """Strip unsafe HTML, allow a small safe subset."""
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


def sanitize_plain(text: str) -> str:
    """Strip all HTML tags — plain text only."""
    return bleach.clean(text, tags=[], strip=True)
