"""Crawl worker: fetches new chapters from registered sources into crawl_queue."""
import asyncio
import logging

import httpx

from app.core.database import get_supabase
from app.workers.parsers.biquge import BiqugeParser

logger = logging.getLogger(__name__)

PARSERS = [BiqugeParser()]
RATE_LIMIT_DELAY = 1.0  # seconds between requests per domain
REQUEST_TIMEOUT = 30.0

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def _get_parser(url: str):
    for parser in PARSERS:
        if parser.can_handle(url):
            return parser
    return None


async def crawl_source(source: dict, client: httpx.AsyncClient) -> int:
    """Crawl one source, insert new chapters into crawl_queue. Returns count of new items."""
    supabase = get_supabase()
    source_url = source["source_url"]
    novel_id = source["novel_id"]
    source_id = source["id"]
    last_chapter = source["last_chapter"]

    parser = _get_parser(source_url)
    if not parser:
        logger.warning("No parser for %s", source_url)
        return 0

    new_count = 0
    chapter_num = last_chapter + 1

    while True:
        chapter_url = parser.chapter_url(source_url, chapter_num)
        try:
            resp = await client.get(chapter_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 404:
                break  # No more chapters
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("HTTP error fetching %s: %s", chapter_url, e)
            break

        content = parser.parse_content(resp.text)
        if not content:
            logger.warning("Empty content at %s", chapter_url)
            break

        # Insert into crawl_queue (ignore conflict if already crawled)
        try:
            supabase.table("crawl_queue").insert({
                "crawl_source_id": source_id,
                "novel_id": novel_id,
                "chapter_number": chapter_num,
                "raw_content": content,
                "status": "crawled",
            }).execute()
            new_count += 1
        except Exception as e:
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                pass  # Already in queue
            else:
                logger.error("DB error inserting chapter %s: %s", chapter_num, e)
                break

        # Update last_chapter on source
        supabase.table("crawl_sources").update(
            {"last_chapter": chapter_num}
        ).eq("id", source_id).execute()

        chapter_num += 1
        await asyncio.sleep(RATE_LIMIT_DELAY)

    return new_count


async def run_crawl_job(novel_id: str | None = None) -> dict:
    """Main entry point. Crawl all active sources (or just one novel if specified)."""
    supabase = get_supabase()
    query = supabase.table("crawl_sources").select("*").eq("is_active", True)
    if novel_id:
        query = query.eq("novel_id", novel_id)
    sources_result = query.execute()
    sources = sources_result.data or []

    if not sources:
        return {"crawled": 0, "sources": 0}

    total_new = 0
    async with httpx.AsyncClient() as client:
        for source in sources:
            try:
                n = await crawl_source(source, client)
                total_new += n
                logger.info("Source %s: %d new chapters", source["source_url"], n)
            except Exception as e:
                logger.error("Error crawling source %s: %s", source["id"], e)

    return {"crawled": total_new, "sources": len(sources)}
