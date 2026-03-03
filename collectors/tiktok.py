"""TikTok ads / organic insights collector."""
from __future__ import annotations

from datetime import date

import requests

import config
from utils.helpers import get_logger, retry_with_backoff

logger = get_logger(__name__)

BASE_URL = "https://business-api.tiktok.com/open_api/v1.3"


@retry_with_backoff(max_retries=3, exceptions=(requests.RequestException,))
def collect(start: date, end: date) -> dict:
    """Fetch TikTok advertiser insights for the given date range."""
    if not config.TIKTOK_ACCESS_TOKEN or not config.TIKTOK_ADVERTISER_ID:
        logger.warning("TikTok credentials not configured – returning empty metrics.")
        return _empty()

    headers = {
        "Access-Token": config.TIKTOK_ACCESS_TOKEN,
        "Content-Type": "application/json",
    }

    params = {
        "advertiser_id": config.TIKTOK_ADVERTISER_ID,
        "report_type": "BASIC",
        "dimensions": ["stat_time_day"],
        "metrics": ["impressions", "clicks", "spend", "reach", "video_play_actions"],
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "data_level": "ADVERTISER",
    }

    url = f"{BASE_URL}/report/integrated/get/"
    resp = requests.get(url, headers=headers, params={"advertiser_id": config.TIKTOK_ADVERTISER_ID}, json=params, timeout=30)
    resp.raise_for_status()
    body = resp.json()

    result: dict = _empty()
    rows = body.get("data", {}).get("list", [])
    for row in rows:
        metrics = row.get("metrics", {})
        result["impressions"] += int(metrics.get("impressions", 0))
        result["clicks"] += int(metrics.get("clicks", 0))
        result["spend"] += float(metrics.get("spend", 0))
        result["reach"] += int(metrics.get("reach", 0))
        result["video_play_actions"] += int(metrics.get("video_play_actions", 0))

    logger.info("TikTok: collected metrics %s → %s", start, end)
    return result


def _empty() -> dict:
    return {
        "impressions": 0,
        "clicks": 0,
        "spend": 0.0,
        "reach": 0,
        "video_play_actions": 0,
    }
