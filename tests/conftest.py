"""Shared test fixtures.

Tests never hit a real LLM or the user's real database or config — a fake provider, a temp DB,
and a throwaway config dir keep them fast, deterministic, and runnable without API keys.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

import pytest

from masta.config import get_settings
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


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Point config and user coaches at a temp dir, so tests can't read or write the real one."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    for var in ("MASTA_CONFIG_DIR", "MASTA_DATA_DIR", "MASTA_DEFAULT_PROFILE"):
        monkeypatch.delenv(var, raising=False)
    get_settings.cache_clear()
    yield tmp_path / "config" / "masta"
    get_settings.cache_clear()


@pytest.fixture
def fake_provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def temp_repo(tmp_path) -> Repository:
    """A repository backed by a throwaway SQLite file."""
    return Repository(db_path=tmp_path / "test.db")
