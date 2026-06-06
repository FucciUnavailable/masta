"""Embedding-based recall (stub).

Post-MVP this will index reflections/messages/knowledge as vectors (via
``LLMProvider.embed``) and surface the most relevant memories for a given turn, so the coach
recalls *pertinent* history rather than just the most recent N messages.

For the MVP, recall is recency-based (see :meth:`Repository.recent_messages`).
"""

from __future__ import annotations

from masta.llm.base import LLMProvider


class SemanticMemory:
    """Placeholder semantic index. Not wired into the agent yet."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def index(self, texts: list[str]) -> None:  # pragma: no cover - stub
        raise NotImplementedError("Semantic memory is planned for a post-MVP milestone.")

    def recall(self, query: str, k: int = 5) -> list[str]:  # pragma: no cover - stub
        raise NotImplementedError("Semantic memory is planned for a post-MVP milestone.")
