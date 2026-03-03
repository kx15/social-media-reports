"""Aggregator: collect metrics from all platforms and persist them."""
from __future__ import annotations

import calendar
from datetime import date

from collectors import facebook, instagram, linkedin, tiktok, youtube
from storage import db
from utils.helpers import get_logger

logger = get_logger(__name__)

PLATFORMS = {
    "facebook": facebook.collect,
    "instagram": instagram.collect,
    "linkedin": linkedin.collect,
    "tiktok": tiktok.collect,
    "youtube": youtube.collect,
}


def run(year: int, month: int) -> dict[str, dict]:
    """Collect and store metrics for every platform for the given month.

    Returns a mapping of platform → metrics dict.
    """
    db.init_db()

    start = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end = date(year, month, last_day)

    all_metrics: dict[str, dict] = {}

    for platform, collector in PLATFORMS.items():
        logger.info("Collecting metrics for %s (%s – %s)…", platform, start, end)
        try:
            metrics = collector(start, end)
            db.save_metrics(platform, end, metrics)
            all_metrics[platform] = metrics
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to collect %s metrics: %s", platform, exc)
            all_metrics[platform] = {}

    logger.info("Aggregation complete for %d-%02d.", year, month)
    return all_metrics
