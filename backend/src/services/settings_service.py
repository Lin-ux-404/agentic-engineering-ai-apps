from __future__ import annotations

import aiosqlite

from ..models import SettingsResponse


async def get_settings(db: aiosqlite.Connection) -> SettingsResponse:
    async with db.execute("SELECT focus_minutes, break_minutes FROM settings WHERE id=1") as cur:
        row = await cur.fetchone()

    if row is None:
        return SettingsResponse(focus_minutes=25, break_minutes=5)

    return SettingsResponse(
        focus_minutes=row["focus_minutes"],
        break_minutes=row["break_minutes"],
    )


async def update_settings(
    db: aiosqlite.Connection,
    focus_minutes: int,
    break_minutes: int,
) -> SettingsResponse:
    await db.execute(
        """INSERT INTO settings (id, focus_minutes, break_minutes) VALUES (1, ?, ?)
           ON CONFLICT(id) DO UPDATE SET focus_minutes=excluded.focus_minutes,
                                         break_minutes=excluded.break_minutes""",
        (focus_minutes, break_minutes),
    )
    await db.commit()
    return SettingsResponse(focus_minutes=focus_minutes, break_minutes=break_minutes)
