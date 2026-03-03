"""LinkedIn organization follower & share statistics collector."""
from __future__ import annotations

import calendar
from datetime import date

import requests

import config
from utils.helpers import get_logger, retry_with_backoff

logger = get_logger(__name__)

BASE_URL = "https://api.linkedin.com/v2"


@retry_with_backoff(max_retries=3, exceptions=(requests.RequestException,))
def collect(start: date, end: date) -> dict:
    """Fetch LinkedIn organization follower statistics and share statistics."""
    if not config.LINKEDIN_ACCESS_TOKEN or not config.LINKEDIN_ORG_ID:
        logger.warning("LinkedIn credentials not configured – returning empty metrics.")
        return _empty()

    headers = {
        "Authorization": f"Bearer {config.LINKEDIN_ACCESS_TOKEN}",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    org_urn = f"urn:li:organization:{config.LINKEDIN_ORG_ID}"

    # Use calendar.timegm for cross-platform UTC timestamp conversion
    next_year = end.year + 1 if end.month == 12 else end.year
    next_month = 1 if end.month == 12 else end.month + 1
    start_ms = calendar.timegm(date(start.year, start.month, 1).timetuple()) * 1000
    end_ms = calendar.timegm(date(next_year, next_month, 1).timetuple()) * 1000

    result: dict = _empty()

    # Follower stats
    follower_url = (
        f"{BASE_URL}/organizationalEntityFollowerStatistics"
        f"?q=organizationalEntity&organizationalEntity={org_urn}"
    )
    resp = requests.get(follower_url, headers=headers, timeout=30)
    if resp.ok:
        elements = resp.json().get("elements", [])
        if elements:
            stats = elements[0].get("followerCountsByAssociationType", [])
            for s in stats:
                result["followers"] += s.get("followerCounts", {}).get("organicFollowerCount", 0)
    else:
        logger.warning("LinkedIn follower stats failed: %s", resp.status_code)

    # Share stats
    share_url = (
        f"{BASE_URL}/organizationalEntityShareStatistics"
        f"?q=organizationalEntity&organizationalEntity={org_urn}"
        f"&timeIntervals.timeGranularityType=MONTH"
        f"&timeIntervals.timeRange.start={start_ms}"
        f"&timeIntervals.timeRange.end={end_ms}"
    )
    resp = requests.get(share_url, headers=headers, timeout=30)
    if resp.ok:
        for el in resp.json().get("elements", []):
            s = el.get("totalShareStatistics", {})
            result["impressions"] += s.get("impressionCount", 0)
            result["clicks"] += s.get("clickCount", 0)
            result["shares"] += s.get("shareCount", 0)
            result["reactions"] += s.get("likeCount", 0)
    else:
        logger.warning("LinkedIn share stats failed: %s", resp.status_code)

    logger.info("LinkedIn: collected metrics %s → %s", start, end)
    return result


def _empty() -> dict:
    return {
        "followers": 0,
        "impressions": 0,
        "clicks": 0,
        "shares": 0,
        "reactions": 0,
    }
