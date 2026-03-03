"""Facebook page insights collector."""
from __future__ import annotations

from datetime import date

import requests

import config
from utils.helpers import get_logger, retry_with_backoff

logger = get_logger(__name__)

BASE_URL = "https://graph.facebook.com/v18.0"


@retry_with_backoff(max_retries=3, exceptions=(requests.RequestException,))
def collect(start: date, end: date) -> dict:
    """Fetch Facebook page insights for the given date range.

    Returns a normalised dict with key metrics.
    """
    if not config.META_ACCESS_TOKEN or not config.FB_PAGE_ID:
        logger.warning("Facebook credentials not configured – returning empty metrics.")
        return _empty()

    metrics = ",".join([
        "page_impressions",
        "page_engaged_users",
        "page_post_engagements",
        "page_fans",
        "page_views_total",
    ])

    params = {
        "metric": metrics,
        "since": start.isoformat(),
        "until": end.isoformat(),
        "period": "total_over_range",
        "access_token": config.META_ACCESS_TOKEN,
    }

    url = f"{BASE_URL}/{config.FB_PAGE_ID}/insights"
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json().get("data", [])

    result: dict = _empty()
    for item in data:
        name: str = item.get("name", "")
        values: list = item.get("values", [])
        total = sum(v.get("value", 0) for v in values if isinstance(v.get("value"), (int, float)))
        result[name] = total

    logger.info("Facebook: collected metrics %s → %s", start, end)
    return result


def _empty() -> dict:
    return {
        "page_impressions": 0,
        "page_engaged_users": 0,
        "page_post_engagements": 0,
        "page_fans": 0,
        "page_views_total": 0,
    }
