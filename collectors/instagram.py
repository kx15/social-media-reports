"""Instagram business account insights collector."""
from __future__ import annotations

from datetime import date

import requests

import config
from utils.helpers import get_logger, retry_with_backoff

logger = get_logger(__name__)

BASE_URL = "https://graph.facebook.com/v18.0"


@retry_with_backoff(max_retries=3, exceptions=(requests.RequestException,))
def collect(start: date, end: date) -> dict:
    """Fetch Instagram account-level insights for the given period."""
    if not config.META_ACCESS_TOKEN or not config.IG_ACCOUNT_ID:
        logger.warning("Instagram credentials not configured – returning empty metrics.")
        return _empty()

    metrics = ",".join([
        "impressions",
        "reach",
        "profile_views",
        "follower_count",
        "website_clicks",
    ])

    params = {
        "metric": metrics,
        "period": "month",
        "since": start.isoformat(),
        "until": end.isoformat(),
        "access_token": config.META_ACCESS_TOKEN,
    }

    url = f"{BASE_URL}/{config.IG_ACCOUNT_ID}/insights"
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json().get("data", [])

    result: dict = _empty()
    for item in data:
        name: str = item.get("name", "")
        values: list = item.get("values", [])
        total = sum(v.get("value", 0) for v in values if isinstance(v.get("value"), (int, float)))
        result[name] = total

    logger.info("Instagram: collected metrics %s → %s", start, end)
    return result


def _empty() -> dict:
    return {
        "impressions": 0,
        "reach": 0,
        "profile_views": 0,
        "follower_count": 0,
        "website_clicks": 0,
    }
