"""Both-sides reasoning: steelman the case for and against a recommendation.

A core differentiator — the sensei never hands you a one-sided answer. This module asks the
LLM for a *structured* pro/con analysis so the result can be rendered or stored, not just
buried in prose.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from masta.llm.base import LLMProvider, Message

_SYSTEM = (
    "You are a rigorous reasoning assistant. Given a recommendation or decision, produce the "
    "STRONGEST honest case for it and the STRONGEST honest case against it, then a balanced "
    "recommendation. Steelman both sides; do not strawman the weaker one. "
    'Respond ONLY with JSON of the form: {"for": [".."], "against": [".."], "recommendation": ".."}'
)


@dataclass
class BothSides:
    """Structured result of a both-sides analysis."""

    topic: str
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    recommendation: str = ""

    def to_markdown(self) -> str:
        pros = "\n".join(f"- {p}" for p in self.pros) or "- (none)"
        cons = "\n".join(f"- {c}" for c in self.cons) or "- (none)"
        return (
            f"**Both sides — {self.topic}**\n\n"
            f"_For:_\n{pros}\n\n_Against:_\n{cons}\n\n"
            f"_Recommendation:_ {self.recommendation}"
        )


def both_sides(provider: LLMProvider, topic: str, context: str = "") -> BothSides:
    """Run a both-sides analysis on ``topic`` using ``provider``.

    Falls back to an empty-but-valid result if the model returns unparseable output, so callers
    never crash on a bad response.
    """
    user = topic if not context else f"{topic}\n\nContext:\n{context}"
    result = provider.complete(
        [Message(role="system", content=_SYSTEM), Message(role="user", content=user)]
    )
    try:
        data = json.loads(_extract_json(result.text))
    except (ValueError, json.JSONDecodeError):
        return BothSides(topic=topic, recommendation=result.text.strip())

    return BothSides(
        topic=topic,
        pros=[str(x) for x in data.get("for", [])],
        cons=[str(x) for x in data.get("against", [])],
        recommendation=str(data.get("recommendation", "")),
    )


def _extract_json(text: str) -> str:
    """Pull the first {...} block out of a model response, tolerating code fences/prose."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON object found")
    return text[start : end + 1]
