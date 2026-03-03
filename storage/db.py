"""Storage layer: SQLite (default) or PostgreSQL via DATABASE_URL."""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import Generator

import config
from utils.helpers import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_postgres() -> bool:
    return bool(config.DATABASE_URL)


@contextmanager
def _get_connection() -> Generator:
    if _is_postgres():
        import psycopg2  # type: ignore
        conn = psycopg2.connect(config.DATABASE_URL)
        try:
            yield conn
        finally:
            conn.close()
    else:
        os.makedirs(os.path.dirname(config.SQLITE_PATH) or ".", exist_ok=True)
        conn = sqlite3.connect(config.SQLITE_PATH)
        try:
            yield conn
        finally:
            conn.close()


def _placeholder() -> str:
    """Return the correct parameter placeholder for the active DB driver."""
    return "%s" if _is_postgres() else "?"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create the metrics table if it does not already exist."""
    ddl = """
    CREATE TABLE IF NOT EXISTS metrics (
        id         SERIAL PRIMARY KEY,
        platform   TEXT        NOT NULL,
        date       DATE        NOT NULL,
        metrics    TEXT        NOT NULL,
        created_at TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (platform, date)
    );
    """
    if not _is_postgres():
        # SQLite doesn't support SERIAL; use ROWID alias instead.
        ddl = """
        CREATE TABLE IF NOT EXISTS metrics (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            platform   TEXT    NOT NULL,
            date       TEXT    NOT NULL,
            metrics    TEXT    NOT NULL,
            created_at TEXT    DEFAULT (datetime('now')),
            UNIQUE (platform, date)
        );
        """
    with _get_connection() as conn:
        conn.cursor().execute(ddl)
        conn.commit()
    logger.info("Database initialised.")


def save_metrics(platform: str, report_date: date, metrics: dict) -> None:
    """Insert or replace metrics for a given platform/date."""
    ph = _placeholder()
    sql = f"""
    INSERT INTO metrics (platform, date, metrics)
    VALUES ({ph}, {ph}, {ph})
    ON CONFLICT (platform, date) DO UPDATE SET metrics = EXCLUDED.metrics;
    """
    if not _is_postgres():
        sql = f"""
        INSERT OR REPLACE INTO metrics (platform, date, metrics)
        VALUES ({ph}, {ph}, {ph});
        """
    with _get_connection() as conn:
        conn.cursor().execute(
            sql, (platform, report_date.isoformat(), json.dumps(metrics))
        )
        conn.commit()
    logger.debug("Saved metrics for %s on %s.", platform, report_date)


def get_month_summary(year: int, month: int) -> list[dict]:
    """Return all metric rows for the given month."""
    prefix = f"{year}-{month:02d}"
    ph = _placeholder()
    if _is_postgres():
        sql = f"SELECT platform, date, metrics FROM metrics WHERE date::text LIKE {ph};"
        param = f"{prefix}%"
    else:
        sql = f"SELECT platform, date, metrics FROM metrics WHERE date LIKE {ph};"
        param = f"{prefix}%"

    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, (param,))
        rows = cur.fetchall()

    return [
        {"platform": r[0], "date": r[1], "metrics": json.loads(r[2])} for r in rows
    ]
