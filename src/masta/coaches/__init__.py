"""The coach engine: pluggable domain experts defined as data, not code."""

from __future__ import annotations

from masta.coaches.loader import load_coach, load_coaches
from masta.coaches.model import Coach, CoachManifest, CoachStyle, Guardrails
from masta.coaches.registry import CoachRegistry

__all__ = [
    "Coach",
    "CoachManifest",
    "CoachStyle",
    "Guardrails",
    "CoachRegistry",
    "load_coach",
    "load_coaches",
]
