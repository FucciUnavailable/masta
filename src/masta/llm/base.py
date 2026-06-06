"""The LLM contract the rest of masta depends on.

Keep this provider-neutral. No backend-specific concepts leak through here — that is the whole
point of the adapter boundary.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable

Role = Literal["system", "user", "assistant", "tool"]


@dataclass
class Message:
    """A single chat message in provider-neutral form."""

    role: Role
    content: str
    name: str | None = None
    # Provider-agnostic slot for tool-call metadata; populated post-MVP.
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        out: dict[str, object] = {"role": self.role, "content": self.content}
        if self.name:
            out["name"] = self.name
        return out


@dataclass
class CompletionResult:
    """The result of a (non-streaming) completion."""

    text: str
    model: str
    raw: object | None = None
    usage: dict[str, int] = field(default_factory=dict)


@runtime_checkable
class LLMProvider(Protocol):
    """Minimal interface every provider implementation must satisfy.

    Implementations live behind :func:`masta.llm.get_provider`. The MVP only needs
    ``complete``/``stream``; ``embed`` exists for the semantic-memory work.
    """

    @property
    def model(self) -> str:
        """The fully-qualified model string in use (e.g. ``anthropic/claude-...``)."""
        ...

    def complete(self, messages: Iterable[Message], **overrides: object) -> CompletionResult:
        """Return a single completion for the given conversation."""
        ...

    def stream(self, messages: Iterable[Message], **overrides: object) -> Iterator[str]:
        """Yield text chunks as they arrive."""
        ...

    def embed(self, texts: Iterable[str]) -> list[list[float]]:
        """Return an embedding vector per input text."""
        ...
