"""A small in-memory registry over the loaded coaches.

Convenience wrapper used by the CLI and agent to list coaches and track the active one.
"""

from __future__ import annotations

from masta.coaches.loader import load_coaches
from masta.coaches.model import Coach


class CoachRegistry:
    def __init__(self, coaches: dict[str, Coach] | None = None) -> None:
        self._coaches = coaches if coaches is not None else load_coaches()

    def names(self) -> list[str]:
        return sorted(self._coaches)

    def all(self) -> list[Coach]:
        return [self._coaches[n] for n in self.names()]

    def get(self, name: str) -> Coach:
        if name not in self._coaches:
            raise KeyError(
                f"Unknown coach {name!r}. Available: {', '.join(self.names()) or '(none)'}"
            )
        return self._coaches[name]

    def __contains__(self, name: object) -> bool:
        return name in self._coaches

    def __len__(self) -> int:
        return len(self._coaches)
