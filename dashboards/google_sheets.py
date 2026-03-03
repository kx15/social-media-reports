"""Google Sheets dashboard updater."""
from __future__ import annotations

import base64
import json
import os

import config
from utils.helpers import get_logger

logger = get_logger(__name__)


def _get_credentials() -> dict:
    """Parse the service-account JSON from the env var (raw JSON or base64)."""
    raw = config.GOOGLE_SERVICE_ACCOUNT_JSON
    if not raw:
        raise EnvironmentError("GOOGLE_SERVICE_ACCOUNT_JSON is not set.")

    # Attempt base64 decode first, fall back to raw JSON
    try:
        decoded = base64.b64decode(raw).decode("utf-8")
        return json.loads(decoded)
    except Exception:  # noqa: BLE001
        pass

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "GOOGLE_SERVICE_ACCOUNT_JSON must be valid JSON or base64-encoded JSON."
        ) from exc


def push(year: int, month: int, all_metrics: dict[str, dict]) -> None:
    """Write the monthly summary to the configured Google Sheet.

    The sheet is expected to have columns: Platform | Metric | Value | Year | Month
    Data is appended to the first worksheet.
    """
    if not config.GOOGLE_SERVICE_ACCOUNT_JSON:
        logger.warning("GOOGLE_SERVICE_ACCOUNT_JSON not set – skipping Sheets update.")
        return

    if not config.SHEET_ID:
        logger.warning("SHEET_ID not set – skipping Sheets update.")
        return

    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError as exc:
        logger.error("gspread / google-auth not installed: %s", exc)
        return

    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds_dict = _get_credentials()
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(config.SHEET_ID).sheet1

    rows: list[list] = []
    for platform, metrics in all_metrics.items():
        for metric, value in metrics.items():
            rows.append([platform.capitalize(), metric.replace("_", " ").title(), value, year, month])

    if rows:
        sheet.append_rows(rows, value_input_option="USER_ENTERED")
        logger.info("Google Sheets updated with %d rows for %d-%02d.", len(rows), year, month)
    else:
        logger.info("No data to push to Google Sheets.")
