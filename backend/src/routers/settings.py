from fastapi import APIRouter

from ..database import get_db
from ..models import SettingsRequest, SettingsResponse
from ..services import settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    async with get_db() as db:
        return await settings_service.get_settings(db)


@router.put("", response_model=SettingsResponse)
async def update_settings(body: SettingsRequest) -> SettingsResponse:
    async with get_db() as db:
        return await settings_service.update_settings(db, body.focus_minutes, body.break_minutes)
