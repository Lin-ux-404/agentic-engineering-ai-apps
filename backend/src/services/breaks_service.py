from __future__ import annotations

import datetime

import aiosqlite
from fastapi import HTTPException

from ..models import BreakCountdownResponse


def _now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def _parse_utc(ts: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))


async def get_active_break(db: aiosqlite.Connection) -> BreakCountdownResponse | None:
    async with db.execute(
        "SELECT * FROM breaks WHERE status = 'active' LIMIT 1"
    ) as cur:
        row = await cur.fetchone()

    if row is None:
        return None

    now = _now_utc()
    expected_end = _parse_utc(row["expected_end_at"])

    if now >= expected_end:
        finished_at = now.isoformat()
        await db.execute(
            "UPDATE breaks SET status = 'finished', finished_at = ? WHERE id = ?",
            (finished_at, row["id"]),
        )
        await db.commit()
        return BreakCountdownResponse(
            id=row["id"],
            session_id=row["session_id"],
            start_at=row["start_at"],
            expected_end_at=row["expected_end_at"],
            configured_minutes=row["configured_minutes"],
            remaining_seconds=0.0,
            status="finished",
            skipped_at=row["skipped_at"],
            finished_at=finished_at,
        )

    remaining = max(0.0, (expected_end - now).total_seconds())
    return BreakCountdownResponse(
        id=row["id"],
        session_id=row["session_id"],
        start_at=row["start_at"],
        expected_end_at=row["expected_end_at"],
        configured_minutes=row["configured_minutes"],
        remaining_seconds=remaining,
        status="active",
        skipped_at=row["skipped_at"],
        finished_at=row["finished_at"],
    )


async def create_break(
    db: aiosqlite.Connection,
    session_id: int,
    break_minutes: int,
) -> BreakCountdownResponse:
    # Auto-finish any existing active break before creating a new one
    now = _now_utc()
    finished_at = now.isoformat()
    await db.execute(
        "UPDATE breaks SET status = 'finished', finished_at = ? WHERE status = 'active'",
        (finished_at,),
    )

    start_at = now.isoformat()
    expected_end_at = (now + datetime.timedelta(minutes=break_minutes)).isoformat()
    date_key = datetime.datetime.now().strftime("%Y-%m-%d")

    async with db.execute(
        """INSERT INTO breaks
           (session_id, start_at, expected_end_at, configured_minutes, status, date_key)
           VALUES (?, ?, ?, ?, 'active', ?)""",
        (session_id, start_at, expected_end_at, break_minutes, date_key),
    ) as cur:
        break_id = cur.lastrowid

    await db.commit()

    return BreakCountdownResponse(
        id=break_id,  # type: ignore[arg-type]
        session_id=session_id,
        start_at=start_at,
        expected_end_at=expected_end_at,
        configured_minutes=break_minutes,
        remaining_seconds=float(break_minutes * 60),
        status="active",
    )


async def skip_break(
    db: aiosqlite.Connection,
    break_id: int,
) -> BreakCountdownResponse:
    async with db.execute("SELECT * FROM breaks WHERE id = ?", (break_id,)) as cur:
        row = await cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Break not found.")

    if row["status"] != "active":
        raise HTTPException(status_code=409, detail="Break is not active.")

    skipped_at = _now_utc().isoformat()
    await db.execute(
        "UPDATE breaks SET status = 'skipped', skipped_at = ? WHERE id = ?",
        (skipped_at, break_id),
    )
    await db.commit()

    return BreakCountdownResponse(
        id=row["id"],
        session_id=row["session_id"],
        start_at=row["start_at"],
        expected_end_at=row["expected_end_at"],
        configured_minutes=row["configured_minutes"],
        remaining_seconds=0.0,
        status="skipped",
        skipped_at=skipped_at,
        finished_at=row["finished_at"],
    )
