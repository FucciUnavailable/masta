"""Persistent memory — what makes masta a coaching *system* rather than a chatbot.

Goals, milestones, check-ins, conversation history, and reflections are stored in a local
SQLite database so the sensei has continuity across sessions.
"""

from __future__ import annotations

from masta.memory.db import get_session, init_db
from masta.memory.models import (
    CheckIn,
    Goal,
    GoalStatus,
    Message,
    Milestone,
    Reflection,
    UserProfile,
)
from masta.memory.repository import Repository

__all__ = [
    "get_session",
    "init_db",
    "Repository",
    "UserProfile",
    "Goal",
    "GoalStatus",
    "Milestone",
    "CheckIn",
    "Message",
    "Reflection",
]
