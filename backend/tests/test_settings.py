"""Tests for settings API endpoints (US5)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_settings_returns_defaults(client: AsyncClient) -> None:
    resp = await client.get("/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["focus_minutes"] == 25
    assert data["break_minutes"] == 5


@pytest.mark.asyncio
async def test_put_settings_valid(client: AsyncClient) -> None:
    resp = await client.put("/settings", json={"focus_minutes": 50, "break_minutes": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert data["focus_minutes"] == 50
    assert data["break_minutes"] == 10


@pytest.mark.asyncio
async def test_get_settings_returns_updated_value(client: AsyncClient) -> None:
    await client.put("/settings", json={"focus_minutes": 45, "break_minutes": 15})
    resp = await client.get("/settings")
    assert resp.json()["focus_minutes"] == 45
    assert resp.json()["break_minutes"] == 15


@pytest.mark.asyncio
async def test_put_settings_invalid_zero_returns_422(client: AsyncClient) -> None:
    resp = await client.put("/settings", json={"focus_minutes": 0, "break_minutes": 5})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_put_settings_negative_returns_422(client: AsyncClient) -> None:
    resp = await client.put("/settings", json={"focus_minutes": -1, "break_minutes": 5})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_put_settings_over_max_focus_returns_422(client: AsyncClient) -> None:
    resp = await client.put("/settings", json={"focus_minutes": 481, "break_minutes": 5})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_put_settings_over_max_break_returns_422(client: AsyncClient) -> None:
    resp = await client.put("/settings", json={"focus_minutes": 25, "break_minutes": 121})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_successive_puts_last_wins(client: AsyncClient) -> None:
    await client.put("/settings", json={"focus_minutes": 30, "break_minutes": 5})
    await client.put("/settings", json={"focus_minutes": 60, "break_minutes": 20})
    resp = await client.get("/settings")
    assert resp.json()["focus_minutes"] == 60
    assert resp.json()["break_minutes"] == 20
