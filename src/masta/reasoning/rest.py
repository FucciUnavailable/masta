"""Rest & break heuristics (stub).

Post-MVP: use session duration and recent check-in energy/mood to decide when to nudge a
break or a full rest day. Rest is treated as part of progress, not a reward for it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RestNudge:
    should_rest: bool
    message: str


def assess_rest(session_minutes: float, recent_energy: int | None) -> RestNudge:
    # pragma: no cover - stub
    raise NotImplementedError("Rest heuristics are planned for a post-MVP milestone.")
