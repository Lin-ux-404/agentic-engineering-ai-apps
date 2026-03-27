from __future__ import annotations

import datetime

import aiosqlite
from fastapi import HTTPException

from ..models import ActiveSessionResponse, SessionSummaryResponse, TodayResponse


def _now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def _parse_utc(ts: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _compute_remaining(
    start_at: str,
    configured_minutes: int,
    paused_seconds: int,
    paused_at: str | None,
) -> float:
    now = _now_utc()
    start = _parse_utc(start_at)
    total_seconds = configured_minutes * 60
    elapsed = (now - start).total_seconds()
    # If currently paused, paused time since paused_at does not count as elapsed focused time
    current_pause = 0.0
    if paused_at is not None:
        current_pause = (now - _parse_utc(paused_at)).total_seconds()
    return total_seconds - elapsed + paused_seconds + current_pause


def _row_to_active(row: aiosqlite.Row, remaining: float) -> ActiveSessionResponse:
    return ActiveSessionResponse(
        id=row["id"],
        start_at=row["start_at"],
        end_at=row["end_at"],
        status=row["status"],
        configured_minutes=row["configured_minutes"],
        paused_seconds=row["paused_seconds"],
        paused_at=row["paused_at"],
        remaining_seconds=remaining,
        focused_seconds=row["focused_seconds"],
        note=row["note"],
    )


async def get_active_with_auto_complete(
    db: aiosqlite.Connection,
) -> ActiveSessionResponse | None:
    async with db.execute(
        "SELECT * FROM sessions WHERE status IN ('running','paused') LIMIT 1"
    ) as cur:
        row = await cur.fetchone()

    if row is None:
        return None

    remaining = _compute_remaining(
        row["start_at"],
        row["configured_minutes"],
        row["paused_seconds"],
        row["paused_at"],
    )

    if remaining <= 0 and row["status"] == "running":
        end_at = _now_utc().isoformat()
        # elapsed total − paused = focused
        start = _parse_utc(row["start_at"])
        elapsed = (_now_utc() - start).total_seconds()
        focused = max(0, int(elapsed - row["paused_seconds"]))
        await db.execute(
            "UPDATE sessions SET status='completed', end_at=?, focused_seconds=? WHERE id=?",
            (end_at, focused, row["id"]),
        )
        await db.commit()
        async with db.execute("SELECT * FROM sessions WHERE id=?", (row["id"],)) as cur:
            row = await cur.fetchone()
        remaining = 0.0

    return _row_to_active(row, remaining)  # type: ignore[arg-type]


async def start(
    db: aiosqlite.Connection,
    configured_minutes: int,
    note: str | None,
) -> ActiveSessionResponse:
    # Single-active-session guard (belt + suspenders — DB also constrains via unique index)
    async with db.execute(
        "SELECT id FROM sessions WHERE status IN ('running','paused') LIMIT 1"
    ) as cur:
        existing = await cur.fetchone()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="A focus session is already active. Stop or complete it before starting a new one.",  # noqa: E501
        )

    now = _now_utc()
    # Use local calendar date per spec ("Calendar date of start_at in local time")
    date_key = datetime.datetime.now().strftime("%Y-%m-%d")
    start_at = now.isoformat()

    async with db.execute(
        """INSERT INTO sessions
           (start_at, status, configured_minutes, paused_seconds, note, date_key)
           VALUES (?, 'running', ?, 0, ?, ?)""",
        (start_at, configured_minutes, note, date_key),
    ) as cur:
        session_id = cur.lastrowid

    await db.commit()

    async with db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)) as cur:
        row = await cur.fetchone()

    remaining = float(configured_minutes * 60)
    return _row_to_active(row, remaining)  # type: ignore[arg-type]


async def complete(db: aiosqlite.Connection, session_id: int) -> ActiveSessionResponse:
    async with db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)) as cur:
        row = await cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    if row["status"] != "running":
        raise HTTPException(
            status_code=409,
            detail="Session is not running; cannot complete.",
        )

    now = _now_utc()
    end_at = now.isoformat()
    start = _parse_utc(row["start_at"])
    elapsed = (now - start).total_seconds()
    focused = max(0, int(elapsed - row["paused_seconds"]))

    await db.execute(
        "UPDATE sessions SET status='completed', end_at=?, focused_seconds=? WHERE id=?",
        (end_at, focused, session_id),
    )
    await db.commit()

    async with db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)) as cur:
        row = await cur.fetchone()

    return _row_to_active(row, 0.0)  # type: ignore[arg-type]


async def pause(db: aiosqlite.Connection, session_id: int) -> ActiveSessionResponse:
    async with db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)) as cur:
        row = await cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    if row["status"] != "running":
        raise HTTPException(
            status_code=409,
            detail="Session is not running; cannot pause.",
        )

    paused_at = _now_utc().isoformat()
    await db.execute(
        "UPDATE sessions SET status='paused', paused_at=? WHERE id=?",
        (paused_at, session_id),
    )
    await db.commit()

    async with db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)) as cur:
        row = await cur.fetchone()

    assert row is not None  # just committed the UPDATE above
    remaining = _compute_remaining(
        row["start_at"],
        row["configured_minutes"],
        row["paused_seconds"],
        row["paused_at"],
    )
    return _row_to_active(row, remaining)


async def resume(db: aiosqlite.Connection, session_id: int) -> ActiveSessionResponse:
    async with db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)) as cur:
        row = await cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    if row["status"] != "paused":
        raise HTTPException(
            status_code=409,
            detail="Session is not paused; cannot resume.",
        )

    now = _now_utc()
    pause_duration = int((now - _parse_utc(row["paused_at"])).total_seconds())
    new_paused_seconds = row["paused_seconds"] + pause_duration

    await db.execute(
        "UPDATE sessions SET status='running', paused_seconds=?, paused_at=NULL WHERE id=?",
        (new_paused_seconds, session_id),
    )
    await db.commit()

    async with db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)) as cur:
        row = await cur.fetchone()

    assert row is not None  # just committed the UPDATE above
    remaining = _compute_remaining(
        row["start_at"],
        row["configured_minutes"],
        row["paused_seconds"],
        None,
    )
    return _row_to_active(row, remaining)


async def stop_early(db: aiosqlite.Connection, session_id: int) -> ActiveSessionResponse:
    async with db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)) as cur:
        row = await cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    if row["status"] not in ("running", "paused"):
        raise HTTPException(status_code=409, detail="Session has already ended.")

    now = _now_utc()
    end_at = now.isoformat()

    # Finalize any open pause interval
    total_paused = row["paused_seconds"]
    if row["paused_at"] is not None:
        total_paused += int((now - _parse_utc(row["paused_at"])).total_seconds())

    start = _parse_utc(row["start_at"])
    elapsed = (now - start).total_seconds()
    focused = max(0, int(elapsed - total_paused))

    await db.execute(
        """UPDATE sessions
           SET status='stopped_early', end_at=?, focused_seconds=?,
               paused_seconds=?, paused_at=NULL
           WHERE id=?""",
        (end_at, focused, total_paused, session_id),
    )
    await db.commit()

    async with db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)) as cur:
        row = await cur.fetchone()

    return _row_to_active(row, 0.0)  # type: ignore[arg-type]


async def get_today(db: aiosqlite.Connection) -> TodayResponse:
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    async with db.execute(
        """SELECT id, start_at, end_at, status, focused_seconds, note
           FROM sessions
           WHERE date_key = ?
           ORDER BY start_at ASC""",
        (today,),
    ) as cur:
        rows = await cur.fetchall()

    sessions = [
        SessionSummaryResponse(
            id=r["id"],
            start_at=r["start_at"],
            end_at=r["end_at"],
            status=r["status"],
            focused_seconds=r["focused_seconds"],
            note=r["note"],
        )
        for r in rows
    ]

    # Sum per-session floor-divided minutes so the total matches the displayed per-row values
    total_minutes = sum(
        (s.focused_seconds or 0) // 60
        for s in sessions
        if s.status in ("completed", "stopped_early")
    )

    return TodayResponse(
        date=today,
        total_focused_minutes=total_minutes,
        sessions=sessions,
    )
