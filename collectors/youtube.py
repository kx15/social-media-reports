"""YouTube channel statistics collector."""
from __future__ import annotations

from datetime import date

import requests

import config
from utils.helpers import get_logger, retry_with_backoff

logger = get_logger(__name__)

BASE_URL = "https://www.googleapis.com/youtube/v3"
ANALYTICS_URL = "https://youtubeanalytics.googleapis.com/v2"


@retry_with_backoff(max_retries=3, exceptions=(requests.RequestException,))
def collect(start: date, end: date) -> dict:
    """Fetch YouTube channel statistics and analytics."""
    if not config.YOUTUBE_API_KEY or not config.YOUTUBE_CHANNEL_ID:
        logger.warning("YouTube credentials not configured – returning empty metrics.")
        return _empty()

    result: dict = _empty()

    # Channel statistics (subscribers, views, videos)
    params = {
        "part": "statistics",
        "id": config.YOUTUBE_CHANNEL_ID,
        "key": config.YOUTUBE_API_KEY,
    }
    resp = requests.get(f"{BASE_URL}/channels", params=params, timeout=30)
    resp.raise_for_status()
    items = resp.json().get("items", [])
    if items:
        stats = items[0].get("statistics", {})
        result["subscribers"] = int(stats.get("subscriberCount", 0))
        result["total_views"] = int(stats.get("viewCount", 0))
        result["total_videos"] = int(stats.get("videoCount", 0))

    # Period-specific analytics via YouTube Analytics API
    analytics_params = {
        "ids": f"channel=={config.YOUTUBE_CHANNEL_ID}",
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "metrics": "views,estimatedMinutesWatched,likes,comments,shares",
        "key": config.YOUTUBE_API_KEY,
    }
    a_resp = requests.get(f"{ANALYTICS_URL}/reports", params=analytics_params, timeout=30)
    if a_resp.ok:
        rows = a_resp.json().get("rows", [])
        if rows:
            row = rows[0]
            result["views"] = int(row[0]) if len(row) > 0 else 0
            result["watch_minutes"] = int(row[1]) if len(row) > 1 else 0
            result["likes"] = int(row[2]) if len(row) > 2 else 0
            result["comments"] = int(row[3]) if len(row) > 3 else 0
            result["shares"] = int(row[4]) if len(row) > 4 else 0
    else:
        logger.warning("YouTube Analytics API failed: %s", a_resp.status_code)

    logger.info("YouTube: collected metrics %s → %s", start, end)
    return result


def _empty() -> dict:
    return {
        "subscribers": 0,
        "total_views": 0,
        "total_videos": 0,
        "views": 0,
        "watch_minutes": 0,
        "likes": 0,
        "comments": 0,
        "shares": 0,
    }
