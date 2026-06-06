"""Web/evidence search tool (stub).

Post-MVP: query a search backend (or scientific source) and return ranked, citable snippets so
coaches can ground advice in real evidence. Will self-register on the global registry.
"""

from __future__ import annotations


def web_search(query: str, limit: int = 5) -> list[dict]:  # pragma: no cover - stub
    raise NotImplementedError("web_search is planned for a post-MVP milestone.")
