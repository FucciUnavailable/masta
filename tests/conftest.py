"""Shared test fixtures.

Tests never hit a real LLM or the user's real database — a fake provider and a temp DB keep
them fast, deterministic, and runnable without API keys.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

import pytest

from masta.llm.base import CompletionResult, Message
from masta.memory.repository import Repository


class FakeProvider:
    """An :class:`LLMProvider` that returns canned/echoed responses."""

    def __init__(self, response: str = "ok", model: str = "fake/model") -> None:
        self._response = response
        self._model = model
        self.calls: list[list[Message]] = []

    @property
    def model(self) -> str:
        return self._model

    def complete(self, messages: Iterable[Message], **overrides: object) -> CompletionResult:
        msgs = list(messages)
        self.calls.append(msgs)
        return CompletionResult(text=self._response, model=self._model)

    def stream(self, messages: Iterable[Message], **overrides: object) -> Iterator[str]:
        self.calls.append(list(messages))
        for word in self._response.split():
            yield word + " "

    def embed(self, texts: Iterable[str]) -> list[list[float]]:
        return [[0.0, 1.0, 2.0] for _ in texts]


@pytest.fixture
def fake_provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def temp_repo(tmp_path) -> Repository:
    """A repository backed by a throwaway SQLite file."""
    return Repository(db_path=tmp_path / "test.db")
