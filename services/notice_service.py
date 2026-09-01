import asyncio
import html
import logging
import re
import time
from typing import Any, Dict, List

import feedparser
import httpx

from database import (
    add_notice_if_new,
    get_recent_notices,
)

logger = logging.getLogger(__name__)

NOTICE_FEED_URL = "https://www.uiu.ac.bd/notice/feed/"
CACHE_TTL = 300

_cached_notices: List[Dict[str, Any]] = []
_last_cache_time: float = 0.0
_sync_lock = asyncio.Lock()


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


async def fetch_live_notices(limit: int = 15) -> List[Dict[str, Any]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers=headers,
        ) as client:
            response = await client.get(NOTICE_FEED_URL)

            if response.status_code != 200:
                logger.warning(
                    "UIU notice feed returned status code: %s",
                    response.status_code,
                )
                return []

            feed = feedparser.parse(response.text)
            notices: List[Dict[str, Any]] = []

            for entry in feed.entries[:limit]:
                title = _clean_text(entry.get("title", "Untitled Notice"))
                link = entry.get("link", "").strip()
                published = entry.get("published", "").strip()
                description = _clean_text(entry.get("summary", ""))

                if title and link:
                    notices.append(
                        {
                            "title": title,
                            "link": link,
                            "url": link,
                            "published_date": published,
                            "description": description,
                        }
                    )

            return notices

    except Exception as error:
        logger.error(
            "Failed to fetch live notices: %s",
            error,
        )
        return []


async def sync_notices() -> Dict[str, Any]:
    global _cached_notices, _last_cache_time

    async with _sync_lock:
        live_notices = await fetch_live_notices()
        new_items: List[Dict[str, Any]] = []

        if live_notices:
            for item in live_notices:
                try:
                    is_new = await asyncio.to_thread(
                        add_notice_if_new,
                        item["title"],
                        item["link"],
                        item.get("published_date", ""),
                    )

                    if is_new:
                        new_items.append(item)

                except Exception as db_err:
                    logger.error(
                        "Error saving notice to database: %s",
                        db_err,
                    )

            _cached_notices = live_notices
            _last_cache_time = time.time()

            return {
                "new": new_items,
                "notices": _cached_notices,
            }

        db_notices = await asyncio.to_thread(get_recent_notices, 10)
        if db_notices:
            _cached_notices = db_notices
            _last_cache_time = time.time()

        return {
            "new": [],
            "notices": _cached_notices,
        }


async def get_cached_notices(limit: int = 5) -> List[Dict[str, Any]]:
    global _cached_notices, _last_cache_time

    now = time.time()

    if _cached_notices and (now - _last_cache_time < CACHE_TTL):
        return _cached_notices[:limit]

    db_notices = await asyncio.to_thread(get_recent_notices, limit)
    if db_notices:
        _cached_notices = db_notices
        if now - _last_cache_time >= CACHE_TTL:
            asyncio.create_task(sync_notices())
        return db_notices[:limit]

    sync_result = await sync_notices()
    return sync_result.get("notices", [])[:limit]
