import asyncio
import hashlib
import html
import logging
import re
import time
from typing import Any, Dict, List

from bs4 import BeautifulSoup
import httpx

from database import (
    get_calendar_by_url,
    get_calendars,
    save_calendar,
)

logger = logging.getLogger(__name__)

CALENDAR_URL = "https://www.uiu.ac.bd/academics/calendar/"
CACHE_TTL = 600

_cached_calendars: List[Dict[str, Any]] = []
_last_cache_time: float = 0.0
_calendar_lock = asyncio.Lock()

CALENDAR_FALLBACKS = [
    {
        "title": "Fall 2026 Semester Bachelor of Pharmacy (B. Pharm.)",
        "year": "2026",
        "url": "https://www.uiu.ac.bd/wp-content/uploads/2026/07/Academic-Calendar_263-BPharm.pdf",
    },
    {
        "title": "Summer 2026 Trimester Undergraduate Programs",
        "year": "2026",
        "url": "https://www.uiu.ac.bd/wp-content/uploads/2026/06/Academic-Calendar_262_Undergraduate-Programs_compressed.pdf",
    },
    {
        "title": "Summer 2026 Trimester Graduate Programs",
        "year": "2026",
        "url": "https://www.uiu.ac.bd/wp-content/uploads/2026/06/Academic-Calendar_262_Graduate-Programs_compressed.pdf",
    },
    {
        "title": "Spring 2026 Trimester Undergraduate Programs [Revised]",
        "year": "2026",
        "url": "https://www.uiu.ac.bd/wp-content/uploads/2026/02/Revised-Academic-Calendar-UG-261-12.5.26.pdf",
    },
    {
        "title": "Spring 2026 Trimester Graduate Programs [Revised]",
        "year": "2026",
        "url": "https://www.uiu.ac.bd/wp-content/uploads/2026/02/Revised-Academic-Calendar-Grad-261-12.5.26.pdf",
    },
]


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_year(title: str) -> str:
    match = re.search(r"\b20\d{2}\b", title)
    return match.group(0) if match else ""


async def fetch_calendars() -> List[Dict[str, Any]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            headers=headers,
        ) as client:
            response = await client.get(CALENDAR_URL)

            if response.status_code == 200:
                soup = BeautifulSoup(
                    response.text,
                    "html.parser",
                )

                found_items: List[Dict[str, Any]] = []

                items = soup.find_all("div", class_="calender-item")

                for item in items:
                    summary = item.find("summary")
                    pdf_link = item.find(
                        "a",
                        href=lambda h: h and ".pdf" in h.lower(),
                    )

                    if summary and pdf_link and pdf_link.get("href"):
                        title = _clean_text(summary.get_text())
                        url = pdf_link["href"].strip()
                        year = _extract_year(title)

                        if title and url:
                            found_items.append(
                                {
                                    "title": title,
                                    "url": url,
                                    "year": year,
                                }
                            )

                if found_items:
                    return found_items

    except Exception as error:
        logger.error(
            "Calendar fetch error: %s",
            error,
        )

    db_items = await asyncio.to_thread(get_calendars, 10)
    if db_items:
        return [
            {
                "title": item["title"],
                "url": item["url"],
                "year": _extract_year(item["title"]),
            }
            for item in db_items
        ]

    return CALENDAR_FALLBACKS


async def sync_calendars() -> Dict[str, Any]:
    global _cached_calendars, _last_cache_time

    async with _calendar_lock:
        calendars = await fetch_calendars()
        new_items: List[Dict[str, Any]] = []
        updated_items: List[Dict[str, Any]] = []

        for item in calendars:
            title = item["title"]
            url = item["url"]
            content_hash = hashlib.sha256(
                f"{title}:{url}".encode("utf-8")
            ).hexdigest()

            item["content_hash"] = content_hash

            try:
                existing = await asyncio.to_thread(get_calendar_by_url, url)

                if not existing:
                    await asyncio.to_thread(
                        save_calendar,
                        title,
                        url,
                        content_hash,
                    )
                    new_items.append(item)

                elif existing.get("content_hash") != content_hash:
                    await asyncio.to_thread(
                        save_calendar,
                        title,
                        url,
                        content_hash,
                    )
                    updated_items.append(item)

            except Exception as db_err:
                logger.error(
                    "Error syncing calendar in DB: %s",
                    db_err,
                )

        _cached_calendars = calendars
        _last_cache_time = time.time()

        return {
            "new": new_items,
            "updated": updated_items,
            "calendars": calendars,
        }


async def get_latest_calendars(limit: int = 5) -> List[Dict[str, Any]]:
    global _cached_calendars, _last_cache_time

    now = time.time()

    if _cached_calendars and (now - _last_cache_time < CACHE_TTL):
        return _cached_calendars[:limit]

    db_items = await asyncio.to_thread(get_calendars, limit)
    if db_items:
        formatted = [
            {
                "title": item["title"],
                "url": item["url"],
                "year": _extract_year(item["title"]),
            }
            for item in db_items
        ]
        _cached_calendars = formatted
        if now - _last_cache_time >= CACHE_TTL:
            asyncio.create_task(sync_calendars())
        return formatted[:limit]

    sync_result = await sync_calendars()
    return sync_result.get("calendars", [])[:limit]
