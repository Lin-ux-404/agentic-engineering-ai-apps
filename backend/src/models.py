from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SessionStartRequest(BaseModel):
    configured_minutes: int = Field(..., ge=1, le=480)
    note: str | None = Field(default=None, max_length=500)

    @field_validator("note", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: object) -> object:
        if v == "":
            return None
        return v


class ActiveSessionResponse(BaseModel):
    id: int
    start_at: str
    end_at: str | None
    status: str
    configured_minutes: int
    paused_seconds: int
    paused_at: str | None
    remaining_seconds: float
    focused_seconds: int | None = None
    note: str | None


class SessionSummaryResponse(BaseModel):
    id: int
    start_at: str
    end_at: str | None
    status: str
    focused_seconds: int | None
    note: str | None


class TodayResponse(BaseModel):
    date: str
    total_focused_minutes: int
    sessions: list[SessionSummaryResponse]


class SettingsRequest(BaseModel):
    focus_minutes: int = Field(..., ge=1, le=480)
    break_minutes: int = Field(..., ge=0, le=120)


class SettingsResponse(BaseModel):
    focus_minutes: int
    break_minutes: int


class BreakCountdownResponse(BaseModel):
    id: int
    session_id: int
    start_at: str
    expected_end_at: str
    configured_minutes: int = Field(ge=1, le=120)
    remaining_seconds: float
    status: Literal["active", "skipped", "finished"]
    skipped_at: str | None = None
    finished_at: str | None = None
