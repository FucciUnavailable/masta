"""Tool interface + a global registry.

A tool is a named, callable capability with a JSON-schema-ish parameter description, so it can
later be exposed to the LLM for tool-calling. Coaches reference tools by name in ``coach.yaml``;
the agent only exposes the intersection of registered tools and a coach's allowlist.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class Tool(Protocol):
    name: str
    description: str
    parameters: dict[str, object]

    def __call__(self, **kwargs: object) -> object: ...


@dataclass
class FunctionTool:
    """Wrap a plain function as a :class:`Tool`."""

    name: str
    description: str
    func: Callable[..., object]
    parameters: dict[str, object] = field(default_factory=dict)

    def __call__(self, **kwargs: object) -> object:
        return self.func(**kwargs)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> Tool:
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def names(self) -> list[str]:
        return sorted(self._tools)

    def for_coach(self, allowed: list[str]) -> list[Tool]:
        """Return registered tools whose names appear in the coach's allowlist."""
        return [self._tools[n] for n in allowed if n in self._tools]


# Process-wide default registry. Concrete tools self-register on import (post-MVP).
registry = ToolRegistry()
