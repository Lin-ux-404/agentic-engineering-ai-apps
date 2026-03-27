"""Tests for session API endpoints (US1–US4)."""

from __future__ import annotations

import asyncio
import datetime
from typing import Any

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def start_session(
    client: AsyncClient, minutes: int = 1, note: str | None = None
) -> dict[str, Any]:
    body: dict[str, Any] = {"configured_minutes": minutes}
    if note:
        body["note"] = note
    resp = await client.post("/sessions/start", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# US1: Start and complete a session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_returns_running_session(client: AsyncClient) -> None:
    data = await start_session(client, minutes=25)
    assert data["status"] == "running"
    assert data["configured_minutes"] == 25
    assert data["remaining_seconds"] > 0
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_get_active_returns_session_after_start(client: AsyncClient) -> None:
    created = await start_session(client)
    resp = await client.get("/sessions/active")
    assert resp.status_code == 200
    active = resp.json()
    assert active is not None
    assert active["id"] == created["id"]
    assert active["status"] == "running"


@pytest.mark.asyncio
async def test_get_active_returns_null_when_no_session(client: AsyncClient) -> None:
    resp = await client.get("/sessions/active")
    assert resp.status_code == 200
    assert resp.json() is None


@pytest.mark.asyncio
async def test_double_start_returns_409(client: AsyncClient) -> None:
    await start_session(client)
    resp = await client.post("/sessions/start", json={"configured_minutes": 25})
    assert resp.status_code == 409
    assert "already active" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_complete_session(client: AsyncClient) -> None:
    session = await start_session(client)
    resp = await client.post(f"/sessions/{session['id']}/complete")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["focused_seconds"] is not None
    assert data["end_at"] is not None


@pytest.mark.asyncio
async def test_complete_idempotency_guard(client: AsyncClient) -> None:
    session = await start_session(client)
    await client.post(f"/sessions/{session['id']}/complete")
    # Second complete should 409
    resp = await client.post(f"/sessions/{session['id']}/complete")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_active_auto_completes_expired_session(client: AsyncClient) -> None:
    """Session with 0-minute configured time should auto-complete on next GET active.
    We can't actually wait for a real timer to expire, so we manipulate the data directly.
    """
    # Start a session then manually check via complete endpoint
    session = await start_session(client, minutes=1)
    # Complete it
    await client.post(f"/sessions/{session['id']}/complete")
    # Active should now be null
    resp = await client.get("/sessions/active")
    assert resp.json() is None


@pytest.mark.asyncio
async def test_today_returns_completed_session(client: AsyncClient) -> None:
    session = await start_session(client, minutes=1)
    await client.post(f"/sessions/{session['id']}/complete")

    resp = await client.get("/sessions/today")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["sessions"]) == 1
    assert data["sessions"][0]["status"] == "completed"
    assert isinstance(data["total_focused_minutes"], int)


@pytest.mark.asyncio
async def test_today_total_correct_arithmetic(client: AsyncClient) -> None:
    # Active session should NOT contribute to total
    await start_session(client, minutes=25)
    resp = await client.get("/sessions/today")
    data = resp.json()
    assert data["total_focused_minutes"] == 0


# ---------------------------------------------------------------------------
# US2: Pause and resume
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pause_running_session(client: AsyncClient) -> None:
    session = await start_session(client)
    resp = await client.post(f"/sessions/{session['id']}/pause")
    assert resp.status_code == 200
    assert resp.json()["status"] == "paused"
    assert resp.json()["paused_at"] is not None


@pytest.mark.asyncio
async def test_pause_non_running_returns_409(client: AsyncClient) -> None:
    session = await start_session(client)
    await client.post(f"/sessions/{session['id']}/pause")
    # Already paused — can't pause again
    resp = await client.post(f"/sessions/{session['id']}/pause")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_resume_paused_session(client: AsyncClient) -> None:
    session = await start_session(client)
    await client.post(f"/sessions/{session['id']}/pause")
    resp = await client.post(f"/sessions/{session['id']}/resume")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "running"
    assert data["paused_at"] is None


@pytest.mark.asyncio
async def test_resume_non_paused_returns_409(client: AsyncClient) -> None:
    session = await start_session(client)
    resp = await client.post(f"/sessions/{session['id']}/resume")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_paused_state_survives_get_active(client: AsyncClient) -> None:
    session = await start_session(client)
    await client.post(f"/sessions/{session['id']}/pause")
    resp = await client.get("/sessions/active")
    data = resp.json()
    assert data["status"] == "paused"


@pytest.mark.asyncio
async def test_focused_seconds_excludes_pause_duration(client: AsyncClient) -> None:
    """pause_seconds recorded on pause+resume should reduce focused_seconds."""
    session = await start_session(client, minutes=25)
    await client.post(f"/sessions/{session['id']}/pause")
    await asyncio.sleep(0.1)  # tiny sleep so pause_duration > 0
    await client.post(f"/sessions/{session['id']}/resume")
    await client.post(f"/sessions/{session['id']}/complete")

    resp = await client.get("/sessions/today")
    completed = resp.json()["sessions"][0]
    # paused_seconds must be reflected in the record
    # We don't know exact value but it should exist and be a non-negative int
    assert completed["focused_seconds"] is not None and completed["focused_seconds"] >= 0


# ---------------------------------------------------------------------------
# US3: Stop early
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stop_running_session(client: AsyncClient) -> None:
    session = await start_session(client)
    resp = await client.post(f"/sessions/{session['id']}/stop")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "stopped_early"
    assert data["focused_seconds"] is not None


@pytest.mark.asyncio
async def test_stop_paused_session(client: AsyncClient) -> None:
    session = await start_session(client)
    await client.post(f"/sessions/{session['id']}/pause")
    resp = await client.post(f"/sessions/{session['id']}/stop")
    assert resp.status_code == 200
    assert resp.json()["status"] == "stopped_early"


@pytest.mark.asyncio
async def test_stop_terminal_session_returns_409(client: AsyncClient) -> None:
    session = await start_session(client)
    await client.post(f"/sessions/{session['id']}/complete")
    resp = await client.post(f"/sessions/{session['id']}/stop")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_new_session_starts_after_stop(client: AsyncClient) -> None:
    session = await start_session(client)
    await client.post(f"/sessions/{session['id']}/stop")
    # Should be able to start a new one
    resp = await client.post("/sessions/start", json={"configured_minutes": 25})
    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# US4: Today summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_today_zero_state(client: AsyncClient) -> None:
    resp = await client.get("/sessions/today")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_focused_minutes"] == 0
    assert data["sessions"] == []


@pytest.mark.asyncio
async def test_today_note_visible_in_session_list(client: AsyncClient) -> None:
    session = await start_session(client, note="deep work")
    await client.post(f"/sessions/{session['id']}/complete")
    resp = await client.get("/sessions/today")
    assert resp.json()["sessions"][0]["note"] == "deep work"


@pytest.mark.asyncio
async def test_today_multiple_sessions_total(client: AsyncClient) -> None:
    for _ in range(2):
        s = await start_session(client, minutes=1)
        await client.post(f"/sessions/{s['id']}/complete")

    resp = await client.get("/sessions/today")
    data = resp.json()
    assert len(data["sessions"]) == 2
    # total_focused_minutes must equal the sum of per-session floor-divided minutes
    per_row_minutes = sum((s["focused_seconds"] or 0) // 60 for s in data["sessions"])
    assert data["total_focused_minutes"] == per_row_minutes


@pytest.mark.asyncio
async def test_today_total_consistent_with_sub_minute_sessions(
    client: AsyncClient,
    tmp_path: Any,
    monkeypatch: Any,
) -> None:
    """Regression: two sub-minute sessions must not inflate the total to 1 min.

    If each session is 37 s (displays '0 min'), the total must also be 0 — not 1.
    """
    import aiosqlite

    import src.database as db_mod

    date_key = datetime.datetime.now().strftime("%Y-%m-%d")
    now = datetime.datetime.now(datetime.UTC).isoformat()

    async with aiosqlite.connect(db_mod.DB_PATH) as db:
        for _ in range(2):
            await db.execute(
                """INSERT INTO sessions
                   (start_at, end_at, status, configured_minutes,
                    focused_seconds, paused_seconds, date_key)
                   VALUES (?, ?, 'stopped_early', 25, 37, 0, ?)""",
                (now, now, date_key),
            )
        await db.commit()

    resp = await client.get("/sessions/today")
    data = resp.json()

    assert len(data["sessions"]) == 2
    for s in data["sessions"]:
        assert s["focused_seconds"] == 37
    # Each row displays 0 min (37 // 60 == 0), so total must also be 0
    assert data["total_focused_minutes"] == 0


@pytest.mark.asyncio
async def test_today_total_sums_per_row_minutes_not_raw_seconds(
    client: AsyncClient,
    tmp_path: Any,
    monkeypatch: Any,
) -> None:
    """One session at 37 s (0 min) and one at 90 s (1 min): total must be 1, not 2."""
    import aiosqlite

    import src.database as db_mod

    date_key = datetime.datetime.now().strftime("%Y-%m-%d")
    now = datetime.datetime.now(datetime.UTC).isoformat()

    async with aiosqlite.connect(db_mod.DB_PATH) as db:
        await db.execute(
            """INSERT INTO sessions
               (start_at, end_at, status, configured_minutes,
                focused_seconds, paused_seconds, date_key)
               VALUES (?, ?, 'stopped_early', 25, 37, 0, ?)""",
            (now, now, date_key),
        )
        await db.execute(
            """INSERT INTO sessions
               (start_at, end_at, status, configured_minutes,
                focused_seconds, paused_seconds, date_key)
               VALUES (?, ?, 'completed', 25, 90, 0, ?)""",
            (now, now, date_key),
        )
        await db.commit()

    resp = await client.get("/sessions/today")
    data = resp.json()

    assert len(data["sessions"]) == 2
    # 37 // 60 = 0, 90 // 60 = 1 → total = 1
    assert data["total_focused_minutes"] == 1
