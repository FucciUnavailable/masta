"""Request/response shapes for the HTTP API.

Kept separate from the SQLModel tables so the wire format can evolve independently of
storage. ``web/src/api/types.ts`` mirrors these — change them together.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from masta.memory.models import GoalStatus


def _as_utc(value: datetime) -> datetime:
    # SQLite drops tzinfo on the way out; rows are stored in UTC, so say so on the wire.
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


UTCDatetime = Annotated[datetime, AfterValidator(_as_utc)]


class Health(BaseModel):
    status: str = "ok"
    version: str


class CoachOut(BaseModel):
    name: str
    display_name: str
    description: str
    tags: list[str]
    model_profile: str | None
    tools: list[str]


class ProfileOut(BaseModel):
    name: str
    model: str
    provider: str
    configured: bool
    is_default: bool


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    coach: str | None
    status: GoalStatus
    created_at: UTCDatetime
    target_date: UTCDatetime | None


class GoalCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""
    coach: str | None = None


class GoalUpdate(BaseModel):
    status: GoalStatus


class CheckInOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    goal_id: int | None
    note: str
    mood: int | None
    energy: int | None
    created_at: UTCDatetime


class CheckInCreate(BaseModel):
    note: str = ""
    goal_id: int | None = None
    mood: int | None = Field(default=None, ge=1, le=5)
    energy: int | None = Field(default=None, ge=1, le=5)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    coach: str | None
    role: str
    content: str
    created_at: UTCDatetime


class ChatRequest(BaseModel):
    coach: str
    message: str = Field(min_length=1)
    profile: str | None = None  # override the coach's model profile for this turn
