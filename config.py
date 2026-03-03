"""Central configuration – reads from environment / .env file."""
from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    """Return an env var value, raising clearly if it is absent."""
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"Required environment variable '{name}' is not set.")
    return value


def _optional(name: str, default: str = "") -> str:
    return os.getenv(name, default)


# ---------- Meta / Facebook ----------
META_ACCESS_TOKEN: str = _optional("META_ACCESS_TOKEN")
FB_PAGE_ID: str = _optional("FB_PAGE_ID")

# ---------- Instagram ----------
IG_ACCOUNT_ID: str = _optional("IG_ACCOUNT_ID")

# ---------- TikTok ----------
TIKTOK_ACCESS_TOKEN: str = _optional("TIKTOK_ACCESS_TOKEN")
TIKTOK_ADVERTISER_ID: str = _optional("TIKTOK_ADVERTISER_ID")

# ---------- LinkedIn ----------
LINKEDIN_ACCESS_TOKEN: str = _optional("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_ORG_ID: str = _optional("LINKEDIN_ORG_ID")

# ---------- YouTube ----------
YOUTUBE_API_KEY: str = _optional("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID: str = _optional("YOUTUBE_CHANNEL_ID")

# ---------- Email ----------
SMTP_SERVER: str = _optional("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT: int = int(_optional("SMTP_PORT", "587"))
EMAIL_USER: str = _optional("EMAIL_USER")
EMAIL_PASSWORD: str = _optional("EMAIL_PASSWORD")
EMAIL_RECIPIENTS: list[str] = [
    r.strip() for r in _optional("EMAIL_RECIPIENTS").split(",") if r.strip()
]

# ---------- Google Sheets ----------
GOOGLE_SERVICE_ACCOUNT_JSON: str = _optional("GOOGLE_SERVICE_ACCOUNT_JSON")
SHEET_ID: str = _optional("SHEET_ID")

# ---------- Database ----------
DATABASE_URL: str = _optional("DATABASE_URL")  # empty → SQLite fallback
SQLITE_PATH: str = _optional("SQLITE_PATH", "data/metrics.db")
