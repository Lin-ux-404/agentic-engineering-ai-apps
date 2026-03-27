from fastapi import APIRouter

from ..database import get_db
from ..models import BreakCountdownResponse
from ..services import breaks_service

router = APIRouter(prefix="/breaks", tags=["breaks"])


@router.get("/active", response_model=BreakCountdownResponse | None)
async def get_active_break() -> BreakCountdownResponse | None:
    async with get_db() as db:
        return await breaks_service.get_active_break(db)


@router.post("/{break_id}/skip", response_model=BreakCountdownResponse)
async def skip_break(break_id: int) -> BreakCountdownResponse:
    async with get_db() as db:
        return await breaks_service.skip_break(db, break_id)
