from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import src.database as db_module
from src.database import init_db
from src.main import app

if TYPE_CHECKING:
    from pytest import MonkeyPatch


@pytest_asyncio.fixture
async def client(tmp_path: Path, monkeypatch: MonkeyPatch) -> AsyncClient:  # type: ignore[override]
    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_file)
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
