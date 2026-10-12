"""Request/response shapes for the HTTP API.

Kept separate from the SQLModel tables so the wire format can evolve independently of
storage. ``web/src/api/types.ts`` mirrors these — change them together.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from masta.coaches.model import CoachStyle, Guardrails
from masta.coaches.store import NAME_PATTERN
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
    editable: bool  # lives in the user's coach directory, so it can be changed or deleted


class CoachDetail(CoachOut):
    persona: str
    style: CoachStyle
    guardrails: Guardrails


class CoachUpdate(BaseModel):
    display_name: str | None = None
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    model_profile: str | None = None
    tools: list[str] = Field(default_factory=list)
    style: CoachStyle = Field(default_factory=CoachStyle)
    guardrails: Guardrails = Field(default_factory=Guardrails)
    persona: str = Field(min_length=1)


class CoachCreate(CoachUpdate):
    name: str = Field(pattern=NAME_PATTERN, max_length=64)


class ProfileOut(BaseModel):
    name: str
    model: str
    provider: str
    temperature: float
    max_tokens: int | None
    api_base: str | None
    configured: bool
    missing_env: list[str]  # environment variables to set before it can be used
    is_default: bool
    builtin: bool
    customized: bool  # defined or overridden in config.toml


class ProfileUpdate(BaseModel):
    model: str = Field(min_length=1)
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1)
    api_base: str | None = None


class SettingsOut(BaseModel):
    default_profile: str
    default_profile_from_env: bool  # MASTA_DEFAULT_PROFILE is set and wins over the file
    config_file: str
    data_dir: str
    coaches_dir: str


class SettingsUpdate(BaseModel):
    default_profile: str


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


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    coach: str
    title: str
    created_at: UTCDatetime
    updated_at: UTCDatetime


class SessionCreate(BaseModel):
    coach: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    coach: str | None
    session_id: int | None
    role: str
    content: str
    created_at: UTCDatetime


class ChatRequest(BaseModel):
    coach: str
    message: str = Field(min_length=1)
    session_id: int | None = None  # continue this session; omit for the coach-wide history
    profile: str | None = None  # override the coach's model profile for this turn
