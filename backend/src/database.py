import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import aiosqlite

DB_PATH = os.environ.get("DB_PATH", "focus_timer.db")

_DDL = """
CREATE TABLE IF NOT EXISTS sessions (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    start_at           TEXT    NOT NULL,
    end_at             TEXT,
    status             TEXT    NOT NULL  -- noqa: E501
        CHECK(status IN ('running','paused','completed','stopped_early')),
    configured_minutes INTEGER NOT NULL CHECK(configured_minutes BETWEEN 1 AND 480),
    focused_seconds    INTEGER,
    paused_seconds     INTEGER NOT NULL DEFAULT 0,
    paused_at          TEXT,
    note               TEXT    CHECK(LENGTH(note) <= 500),
    date_key           TEXT    NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_session
    ON sessions (CASE WHEN status IN ('running', 'paused') THEN 1 END);

CREATE TABLE IF NOT EXISTS settings (
    id            INTEGER PRIMARY KEY CHECK(id = 1),
    focus_minutes INTEGER NOT NULL DEFAULT 25 CHECK(focus_minutes BETWEEN 1 AND 480),
    break_minutes INTEGER NOT NULL DEFAULT 5  CHECK(break_minutes BETWEEN 0 AND 120)
);

INSERT OR IGNORE INTO settings (id, focus_minutes, break_minutes) VALUES (1, 25, 5);

CREATE TABLE IF NOT EXISTS breaks (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id          INTEGER NOT NULL UNIQUE REFERENCES sessions(id),
    start_at            TEXT    NOT NULL,
    expected_end_at     TEXT    NOT NULL,
    configured_minutes  INTEGER NOT NULL CHECK(configured_minutes BETWEEN 1 AND 120),
    status              TEXT    NOT NULL DEFAULT 'active'
                        CHECK(status IN ('active','skipped','finished')),
    skipped_at          TEXT,
    finished_at         TEXT,
    date_key            TEXT    NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uix_breaks_single_active
    ON breaks(status) WHERE status = 'active';
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(_DDL)
        await db.commit()


@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
