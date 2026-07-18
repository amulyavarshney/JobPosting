"""Lightweight SQLite column upgrades for existing local databases."""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

_SOURCE_COLUMNS = {
    "scrape_interval_minutes": "INTEGER DEFAULT 0",
    "last_scraped_at": "DATETIME",
    "last_error": "TEXT",
    "last_run_status": "VARCHAR(32) DEFAULT 'never'",
    "updated_at": "DATETIME",
}

_JOB_COLUMNS = {
    "last_seen_at": "DATETIME",
    "status": "VARCHAR(32) DEFAULT 'active'",
    "content_changed": "BOOLEAN DEFAULT 0",
}


def upgrade_sqlite_schema(engine: Engine) -> None:
    if not str(engine.url).startswith("sqlite"):
        return

    with engine.begin() as conn:
        _add_missing(conn, "sources", _SOURCE_COLUMNS)
        _add_missing(conn, "jobs", _JOB_COLUMNS)
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS scrape_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER NOT NULL,
                    status VARCHAR(32) NOT NULL DEFAULT 'running',
                    jobs_found INTEGER DEFAULT 0,
                    jobs_created INTEGER DEFAULT 0,
                    jobs_updated INTEGER DEFAULT 0,
                    jobs_archived INTEGER DEFAULT 0,
                    error_message TEXT,
                    duration_ms FLOAT DEFAULT 0,
                    started_at DATETIME,
                    finished_at DATETIME,
                    FOREIGN KEY(source_id) REFERENCES sources (id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS brand_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    organization_name VARCHAR(255) NOT NULL DEFAULT '',
                    tone VARCHAR(255) NOT NULL DEFAULT 'professional, clear',
                    voice_notes TEXT NOT NULL DEFAULT '',
                    banned_words TEXT NOT NULL DEFAULT '',
                    hashtag_policy TEXT NOT NULL DEFAULT '',
                    cta_preference TEXT NOT NULL DEFAULT '',
                    updated_at DATETIME
                )
                """
            )
        )


def _add_missing(conn, table: str, columns: dict[str, str]) -> None:
    existing = {
        row[1] for row in conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    }
    if not existing:
        return
    for name, ddl in columns.items():
        if name in existing:
            continue
        logger.info("Adding column %s.%s", table, name)
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
