"""A typed CRUD/query layer over the memory tables.

The CLI and the agent talk to this rather than touching sessions directly, so persistence
logic stays in one place.
"""

from __future__ import annotations

from pathlib import Path

from sqlmodel import select

from masta.memory.db import get_session
from masta.memory.models import (
    CheckIn,
    Goal,
    GoalStatus,
    Message,
    Milestone,
    Reflection,
    UserProfile,
)


class Repository:
    """Thin data-access façade. Each method opens a short-lived session.

    Pass ``db_path`` to target a non-default database (used in tests).
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path

    # --- profile -------------------------------------------------------------
    def get_or_create_profile(self) -> UserProfile:
        with get_session(self._db_path) as s:
            profile = s.exec(select(UserProfile)).first()
            if profile is None:
                profile = UserProfile()
                s.add(profile)
                s.commit()
                s.refresh(profile)
            return profile

    # --- goals ---------------------------------------------------------------
    def add_goal(
        self,
        title: str,
        description: str = "",
        coach: str | None = None,
    ) -> Goal:
        with get_session(self._db_path) as s:
            goal = Goal(title=title, description=description, coach=coach)
            s.add(goal)
            s.commit()
            s.refresh(goal)
            return goal

    def list_goals(self, status: GoalStatus | None = None) -> list[Goal]:
        with get_session(self._db_path) as s:
            stmt = select(Goal).order_by(Goal.created_at)
            if status is not None:
                stmt = stmt.where(Goal.status == status)
            return list(s.exec(stmt).all())

    def set_goal_status(self, goal_id: int, status: GoalStatus) -> Goal | None:
        with get_session(self._db_path) as s:
            goal = s.get(Goal, goal_id)
            if goal is None:
                return None
            goal.status = status
            s.add(goal)
            s.commit()
            s.refresh(goal)
            return goal

    # --- milestones ----------------------------------------------------------
    def add_milestone(self, goal_id: int, title: str, order: int = 0) -> Milestone:
        with get_session(self._db_path) as s:
            m = Milestone(goal_id=goal_id, title=title, order=order)
            s.add(m)
            s.commit()
            s.refresh(m)
            return m

    def complete_milestone(self, milestone_id: int) -> Milestone | None:
        with get_session(self._db_path) as s:
            m = s.get(Milestone, milestone_id)
            if m is None:
                return None
            m.done = True
            s.add(m)
            s.commit()
            s.refresh(m)
            return m

    # --- check-ins -----------------------------------------------------------
    def add_checkin(
        self,
        note: str = "",
        goal_id: int | None = None,
        mood: int | None = None,
        energy: int | None = None,
    ) -> CheckIn:
        with get_session(self._db_path) as s:
            c = CheckIn(note=note, goal_id=goal_id, mood=mood, energy=energy)
            s.add(c)
            s.commit()
            s.refresh(c)
            return c

    def recent_checkins(self, limit: int = 10) -> list[CheckIn]:
        with get_session(self._db_path) as s:
            stmt = select(CheckIn).order_by(CheckIn.created_at.desc()).limit(limit)
            return list(s.exec(stmt).all())

    # --- conversation --------------------------------------------------------
    def add_message(self, role: str, content: str, coach: str | None = None) -> Message:
        with get_session(self._db_path) as s:
            msg = Message(role=role, content=content, coach=coach)
            s.add(msg)
            s.commit()
            s.refresh(msg)
            return msg

    def recent_messages(self, limit: int = 20, coach: str | None = None) -> list[Message]:
        with get_session(self._db_path) as s:
            stmt = select(Message)
            if coach is not None:
                stmt = stmt.where(Message.coach == coach)
            stmt = stmt.order_by(Message.created_at.desc()).limit(limit)
            rows = list(s.exec(stmt).all())
            rows.reverse()  # chronological for prompt construction
            return rows

    # --- reflections ---------------------------------------------------------
    def add_reflection(self, content: str, coach: str | None = None) -> Reflection:
        with get_session(self._db_path) as s:
            r = Reflection(content=content, coach=coach)
            s.add(r)
            s.commit()
            s.refresh(r)
            return r
