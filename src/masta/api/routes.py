"""The ``/api`` routes.

Thin handlers over the same :class:`Repository` and :class:`CoachingSession` the CLI uses.
The repository and provider are injected as dependencies so tests can swap in a temp
database and a fake provider.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import StreamingResponse

from masta import __version__
from masta.agent import CoachingSession
from masta.api.schemas import (
    ChatRequest,
    CheckInCreate,
    CheckInOut,
    CoachCreate,
    CoachDetail,
    CoachOut,
    CoachUpdate,
    GoalCreate,
    GoalOut,
    GoalUpdate,
    Health,
    MessageOut,
    ProfileOut,
    ProfileUpdate,
    SessionCreate,
    SessionOut,
    SettingsOut,
    SettingsUpdate,
)
from masta.coaches.loader import load_coach, load_coaches
from masta.coaches.model import Coach, CoachManifest
from masta.coaches.store import delete_coach, is_user_coach, save_coach
from masta.config import ModelProfile, get_settings
from masta.llm import get_provider
from masta.llm.base import LLMProvider
from masta.llm.profiles import (
    ProfileStatus,
    default_profile_from_env,
    list_profiles,
    remove_profile,
    save_profile,
    set_default_profile,
)
from masta.memory.models import ChatSession, GoalStatus
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
ProfileName = Annotated[str, Path(pattern=r"^[A-Za-z0-9_-]+$", max_length=64)]


def _coach_fields(coach: Coach) -> dict[str, object]:
    m = coach.manifest
    return {
        "name": m.name,
        "display_name": m.resolved_display_name(),
        "description": m.description.strip(),
        "tags": m.tags,
        "model_profile": m.model_profile,
        "tools": m.tools,
        "editable": is_user_coach(coach),
    }


def _coach_out(coach: Coach) -> CoachOut:
    return CoachOut(**_coach_fields(coach))


def _coach_detail(coach: Coach) -> CoachDetail:
    return CoachDetail(
        **_coach_fields(coach),
        persona=coach.persona.strip(),
        style=coach.manifest.style,
        guardrails=coach.manifest.guardrails,
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


# --- settings & model profiles ----------------------------------------------
def _settings_out() -> SettingsOut:
    s = get_settings()
    return SettingsOut(
        default_profile=s.default_profile,
        default_profile_from_env=default_profile_from_env(),
        config_file=str(s.config_file),
        data_dir=str(s.data_dir),
        coaches_dir=str(s.user_coaches_dir),
    )


@router.get("/settings")
def settings() -> SettingsOut:
    return _settings_out()


@router.patch("/settings")
def update_settings(body: SettingsUpdate) -> SettingsOut:
    if default_profile_from_env():
        raise HTTPException(
            status_code=409,
            detail="MASTA_DEFAULT_PROFILE is set in the environment and overrides config.toml.",
        )
    try:
        set_default_profile(body.default_profile)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=exc.args[0]) from exc
    return _settings_out()


def _profile_out(s: ProfileStatus) -> ProfileOut:
    return ProfileOut(
        name=s.name,
        model=s.profile.model,
        provider=s.provider,
        temperature=s.profile.temperature,
        max_tokens=s.profile.max_tokens,
        api_base=s.profile.api_base,
        configured=s.configured,
        missing_env=s.missing_env,
        is_default=s.is_default,
        builtin=s.builtin,
        customized=s.customized,
    )


@router.get("/profiles")
def profiles() -> list[ProfileOut]:
    return [_profile_out(s) for s in list_profiles()]


@router.put("/profiles/{name}")
def put_profile(name: ProfileName, body: ProfileUpdate) -> ProfileOut:
    """Create or replace a model profile in ``config.toml``. API keys stay in the environment."""
    existing = get_settings().profiles.get(name)
    save_profile(
        name,
        ModelProfile(
            model=body.model.strip(),
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            api_base=(body.api_base or "").strip() or None,
            extra=existing.extra if existing else {},  # not editable here; don't drop it
        ),
    )
    return next(_profile_out(s) for s in list_profiles() if s.name == name)


@router.delete("/profiles/{name}", status_code=204)
def delete_profile(name: ProfileName) -> None:
    try:
        remove_profile(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=exc.args[0]) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


# --- coaches ----------------------------------------------------------------
@router.get("/coaches")
def coaches() -> list[CoachOut]:
    loaded = load_coaches()
    return [_coach_out(loaded[name]) for name in sorted(loaded)]


@router.get("/coaches/{name}")
def coach(name: str) -> CoachDetail:
    return _coach_detail(_coach_or_404(name))


def _save_coach(name: str, body: CoachUpdate) -> CoachDetail:
    if body.model_profile is not None and body.model_profile not in get_settings().profiles:
        raise HTTPException(
            status_code=400, detail=f"Unknown model profile {body.model_profile!r}."
        )
    manifest = CoachManifest(name=name, **body.model_dump(exclude={"name", "persona"}))
    return _coach_detail(save_coach(manifest, body.persona))


def _editable_coach_or_error(name: str) -> Coach:
    loaded = _coach_or_404(name)
    if not is_user_coach(loaded):
        raise HTTPException(
            status_code=403,
            detail=f"{name!r} is a built-in coach. Copy it under a new name to change it.",
        )
    return loaded


@router.post("/coaches", status_code=201)
def create_coach(body: CoachCreate) -> CoachDetail:
    if body.name in load_coaches():
        raise HTTPException(status_code=409, detail=f"A coach named {body.name!r} already exists.")
    return _save_coach(body.name, body)


@router.put("/coaches/{name}")
def update_coach(name: str, body: CoachUpdate) -> CoachDetail:
    _editable_coach_or_error(name)
    return _save_coach(name, body)


@router.delete("/coaches/{name}", status_code=204)
def remove_coach(name: str) -> None:
    _editable_coach_or_error(name)
    delete_coach(name)


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


# --- chat sessions ----------------------------------------------------------
def _session_or_404(repo: Repository, session_id: int) -> ChatSession:
    found = repo.get_chat_session(session_id)
    if found is None:
        raise HTTPException(status_code=404, detail=f"Unknown session {session_id}")
    return found


@router.get("/sessions", response_model=list[SessionOut])
def sessions(repo: RepoDep, coach: str | None = None, limit: Limit = 50):
    return repo.list_chat_sessions(coach=coach, limit=limit)


@router.post("/sessions", response_model=SessionOut, status_code=201)
def create_session(body: SessionCreate, repo: RepoDep):
    return repo.add_chat_session(coach=_coach_or_404(body.coach).name)


@router.get("/sessions/{session_id}", response_model=SessionOut)
def session(session_id: int, repo: RepoDep):
    return _session_or_404(repo, session_id)


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: int, repo: RepoDep) -> None:
    if not repo.delete_chat_session(session_id):
        raise HTTPException(status_code=404, detail=f"Unknown session {session_id}")


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
def session_messages(session_id: int, repo: RepoDep, limit: Limit = 200):
    _session_or_404(repo, session_id)
    return repo.recent_messages(limit=limit, session_id=session_id)


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
    if body.session_id is not None:
        if _session_or_404(repo, body.session_id).coach != loaded.name:
            raise HTTPException(
                status_code=409,
                detail=f"Session {body.session_id} belongs to a different coach.",
            )
    try:
        provider = resolve(body.profile or loaded.manifest.model_profile)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=exc.args[0]) from exc

    turn = CoachingSession(coach=loaded, provider=provider, repo=repo, session_id=body.session_id)
    return StreamingResponse(
        _sse(turn.stream(body.message)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
