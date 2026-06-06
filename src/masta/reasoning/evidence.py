"""Evidence gathering — search real sources and cite them (stub).

Post-MVP: combine the ``web_search`` tool with retrieval over a coach's ``knowledge/`` docs to
ground recommendations in actual science, returning claims with citations.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Evidence:
    claim: str
    sources: list[str] = field(default_factory=list)


def gather_evidence(query: str) -> list[Evidence]:  # pragma: no cover - stub
    raise NotImplementedError("Evidence search is planned for a post-MVP milestone.")
