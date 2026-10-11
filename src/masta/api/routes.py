"""The ``/api`` routes.

Thin handlers over the same :class:`Repository` and :class:`CoachingSession` the CLI uses.
The repository and provider are injected as dependencies so tests can swap in a temp
database and a fake provider.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from masta import __version__
from masta.agent import CoachingSession
from masta.api.schemas import (
    ChatRequest,
    CheckInCreate,
    CheckInOut,
    CoachOut,
    GoalCreate,
    GoalOut,
    GoalUpdate,
    Health,
    MessageOut,
    ProfileOut,
)
from masta.coaches.loader import load_coach, load_coaches
from masta.coaches.model import Coach
from masta.llm import get_provider
from masta.llm.base import LLMProvider
from masta.llm.profiles import list_profiles
from masta.memory.models import GoalStatus
from masta.memory.repository import Repository

router = APIRouter(prefix="/api")

ProviderResolver = Callable[[str | None], LLMProvider]


def get_repo() -> Repository:
    return Repository()


def get_provider_resolver() -> ProviderResolver:
    return get_provider


RepoDep = Annotated[Repository, Depends(get_repo)]
ResolverDep = Annotated[ProviderResolver, Depends(get_provider_resolver)]
Limit = Annotated[int, Query(ge=1, le=500)]


def _coach_out(coach: Coach) -> CoachOut:
    m = coach.manifest
    return CoachOut(
        name=m.name,
        display_name=m.resolved_display_name(),
        description=m.description.strip(),
        tags=m.tags,
        model_profile=m.model_profile,
        tools=m.tools,
    )


def _coach_or_404(name: str) -> Coach:
    try:
        return load_coach(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=exc.args[0]) from exc


# --- meta -------------------------------------------------------------------
@router.get("/health")
def health() -> Health:
    return Health(version=__version__)


@router.get("/profiles")
def profiles() -> list[ProfileOut]:
    return [
        ProfileOut(
            name=s.name,
            model=s.profile.model,
            provider=s.provider,
            configured=s.configured,
            is_default=s.is_default,
        )
        for s in list_profiles()
    ]


# --- coaches ----------------------------------------------------------------
@router.get("/coaches")
def coaches() -> list[CoachOut]:
    loaded = load_coaches()
    return [_coach_out(loaded[name]) for name in sorted(loaded)]


@router.get("/coaches/{name}")
def coach(name: str) -> CoachOut:
    return _coach_out(_coach_or_404(name))


# --- goals ------------------------------------------------------------------
@router.get("/goals", response_model=list[GoalOut])
def goals(repo: RepoDep, status: GoalStatus | None = None):
    return repo.list_goals(status=status)


@router.post("/goals", response_model=GoalOut, status_code=201)
def create_goal(body: GoalCreate, repo: RepoDep):
    return repo.add_goal(title=body.title, description=body.description, coach=body.coach)


@router.patch("/goals/{goal_id}", response_model=GoalOut)
def update_goal(goal_id: int, body: GoalUpdate, repo: RepoDep):
    goal = repo.set_goal_status(goal_id, body.status)
    if goal is None:
        raise HTTPException(status_code=404, detail=f"Unknown goal {goal_id}")
    return goal


# --- check-ins --------------------------------------------------------------
@router.get("/checkins", response_model=list[CheckInOut])
def checkins(repo: RepoDep, limit: Limit = 20):
    return repo.recent_checkins(limit=limit)


@router.post("/checkins", response_model=CheckInOut, status_code=201)
def create_checkin(body: CheckInCreate, repo: RepoDep):
    return repo.add_checkin(
        note=body.note, goal_id=body.goal_id, mood=body.mood, energy=body.energy
    )


# --- conversation -----------------------------------------------------------
@router.get("/messages", response_model=list[MessageOut])
def messages(repo: RepoDep, coach: str | None = None, limit: Limit = 50):
    return repo.recent_messages(limit=limit, coach=coach)


def _event(type_: str, **fields: object) -> str:
    return f"data: {json.dumps({'type': type_, **fields})}\n\n"


def _sse(chunks: Iterator[str]) -> Iterator[str]:
    """Frame reply chunks as server-sent events: ``delta``\\* then ``done`` or ``error``."""
    try:
        for piece in chunks:
            yield _event("delta", text=piece)
    except Exception as exc:  # the status line is already sent; report in-band instead
        yield _event("error", message=str(exc))
        return
    yield _event("done")


@router.post("/chat")
def chat(
    body: ChatRequest,
    repo: RepoDep,
    resolve: ResolverDep,
) -> StreamingResponse:
    """Stream one coaching turn. The exchange is persisted by the session."""
    loaded = _coach_or_404(body.coach)
    try:
        provider = resolve(body.profile or loaded.manifest.model_profile)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=exc.args[0]) from exc

    session = CoachingSession(coach=loaded, provider=provider, repo=repo)
    return StreamingResponse(
        _sse(session.stream(body.message)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
