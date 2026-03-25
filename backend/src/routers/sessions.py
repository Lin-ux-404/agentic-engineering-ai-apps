from fastapi import APIRouter

from ..database import get_db
from ..models import ActiveSessionResponse, SessionStartRequest, TodayResponse
from ..services import session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/active", response_model=ActiveSessionResponse | None)
async def get_active_session() -> ActiveSessionResponse | None:
    async with get_db() as db:
        return await session_service.get_active_with_auto_complete(db)


@router.post("/start", response_model=ActiveSessionResponse, status_code=201)
async def start_session(body: SessionStartRequest) -> ActiveSessionResponse:
    async with get_db() as db:
        return await session_service.start(db, body.configured_minutes, body.note)


@router.post("/{session_id}/complete", response_model=ActiveSessionResponse)
async def complete_session(session_id: int) -> ActiveSessionResponse:
    async with get_db() as db:
        return await session_service.complete(db, session_id)


@router.post("/{session_id}/pause", response_model=ActiveSessionResponse)
async def pause_session(session_id: int) -> ActiveSessionResponse:
    async with get_db() as db:
        return await session_service.pause(db, session_id)


@router.post("/{session_id}/resume", response_model=ActiveSessionResponse)
async def resume_session(session_id: int) -> ActiveSessionResponse:
    async with get_db() as db:
        return await session_service.resume(db, session_id)


@router.post("/{session_id}/stop", response_model=ActiveSessionResponse)
async def stop_session(session_id: int) -> ActiveSessionResponse:
    async with get_db() as db:
        return await session_service.stop_early(db, session_id)


@router.get("/today", response_model=TodayResponse)
async def get_today() -> TodayResponse:
    async with get_db() as db:
        return await session_service.get_today(db)
