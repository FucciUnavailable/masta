"""SQLModel tables for masta's persistent memory.

Kept deliberately small and readable — these rows are the user's coaching history.

Note: this module intentionally does NOT use ``from __future__ import annotations`` —
SQLModel/SQLAlchemy needs the real (non-stringized) annotations to resolve ``Relationship``
forward references.
"""

from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


class GoalStatus(str, Enum):
    active = "active"
    paused = "paused"
    achieved = "achieved"
    abandoned = "abandoned"


class UserProfile(SQLModel, table=True):
    """The person being coached. Single-user for now, but modeled as a row for the future."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = "you"
    # Free-form context the coach should keep in mind (constraints, preferences, history).
    notes: str = ""
    created_at: datetime = Field(default_factory=_now)


class Goal(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str = ""
    coach: str | None = None  # which coach owns/created this goal
    status: GoalStatus = Field(default=GoalStatus.active)
    created_at: datetime = Field(default_factory=_now)
    target_date: datetime | None = None

    milestones: list["Milestone"] = Relationship(back_populates="goal")
    checkins: list["CheckIn"] = Relationship(back_populates="goal")


class Milestone(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    goal_id: int = Field(foreign_key="goal.id")
    title: str
    done: bool = False
    order: int = 0
    created_at: datetime = Field(default_factory=_now)

    goal: Goal | None = Relationship(back_populates="milestones")


class CheckIn(SQLModel, table=True):
    """A progress log — how things are going, mood/energy, and any blockers."""

    id: int | None = Field(default=None, primary_key=True)
    goal_id: int | None = Field(default=None, foreign_key="goal.id")
    note: str = ""
    mood: int | None = None  # 1-5, optional
    energy: int | None = None  # 1-5, optional, feeds rest reminders
    created_at: datetime = Field(default_factory=_now)

    goal: Goal | None = Relationship(back_populates="checkins")


class Message(SQLModel, table=True):
    """Conversation history, so sessions have continuity."""

    id: int | None = Field(default=None, primary_key=True)
    coach: str | None = None
    role: str = "user"  # user | assistant | system | tool
    content: str = ""
    created_at: datetime = Field(default_factory=_now)


class Reflection(SQLModel, table=True):
    """A coach-generated insight or summary distilled from recent activity."""

    id: int | None = Field(default=None, primary_key=True)
    coach: str | None = None
    content: str = ""
    created_at: datetime = Field(default_factory=_now)
