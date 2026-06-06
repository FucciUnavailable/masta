"""Goal planning: decompose a goal into ordered, concrete milestones.

Produces structured steps so they can be persisted as :class:`~masta.memory.models.Milestone`
rows and tracked over time.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from masta.llm.base import LLMProvider, Message

_SYSTEM = (
    "You are a coaching planner. Decompose the user's goal into 3-7 concrete, ordered "
    "milestones. Each milestone should be a tangible, verifiable outcome (an artifact, a "
    "measurable skill, or a habit), not a vague topic. Be realistic and consider the user's "
    "stated constraints. "
    'Respond ONLY with JSON: {"summary": "..", "steps": [{"title": "..", "detail": ".."}]}'
)


@dataclass
class PlanStep:
    title: str
    detail: str = ""


@dataclass
class GoalPlan:
    goal: str
    summary: str = ""
    steps: list[PlanStep] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [f"**Plan for: {self.goal}**"]
        if self.summary:
            lines.append(f"\n{self.summary}\n")
        for i, step in enumerate(self.steps, 1):
            lines.append(f"{i}. **{step.title}**" + (f" — {step.detail}" if step.detail else ""))
        return "\n".join(lines)


def plan_goal(provider: LLMProvider, goal: str, context: str = "") -> GoalPlan:
    """Generate a structured milestone plan for ``goal``."""
    user = goal if not context else f"Goal: {goal}\n\nContext:\n{context}"
    result = provider.complete(
        [Message(role="system", content=_SYSTEM), Message(role="user", content=user)]
    )
    try:
        start, end = result.text.find("{"), result.text.rfind("}")
        data = json.loads(result.text[start : end + 1])
    except (ValueError, json.JSONDecodeError):
        return GoalPlan(goal=goal, summary=result.text.strip())

    steps = [
        PlanStep(title=str(s.get("title", "")), detail=str(s.get("detail", "")))
        for s in data.get("steps", [])
        if s.get("title")
    ]
    return GoalPlan(goal=goal, summary=str(data.get("summary", "")), steps=steps)
