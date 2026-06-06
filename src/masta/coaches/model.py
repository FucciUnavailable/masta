"""Coach data model.

A coach is described by a ``coach.yaml`` manifest plus a ``persona.md`` system prompt and
optional ``knowledge/`` directory. These pydantic models validate the manifest and carry the
loaded persona.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class CoachStyle(BaseModel):
    """Behavioral knobs that the agent honors when running this coach."""

    both_sides: bool = True  # present pros/cons for recommendations
    socratic: bool = False  # ask before telling
    rest_reminders: bool = True  # nudge breaks/rest during long sessions


class Guardrails(BaseModel):
    """Safety policy. Mandatory in spirit for health/finance/wellbeing coaches.

    The agent enforces these around the model output.
    """

    disclaimers: list[str] = Field(default_factory=list)
    refuse_topics: list[str] = Field(default_factory=list)
    escalate_to_professional: list[str] = Field(default_factory=list)
    safe_ranges: dict[str, list[float]] = Field(default_factory=dict)


class CoachManifest(BaseModel):
    """Validated contents of ``coach.yaml``."""

    name: str
    display_name: str | None = None
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    model_profile: str | None = None  # default LLM profile for this coach
    tools: list[str] = Field(default_factory=list)
    style: CoachStyle = Field(default_factory=CoachStyle)
    guardrails: Guardrails = Field(default_factory=Guardrails)

    def resolved_display_name(self) -> str:
        return self.display_name or self.name.replace("-", " ").title()


class Coach(BaseModel):
    """A fully-loaded coach: manifest + persona text + source location."""

    manifest: CoachManifest
    persona: str
    path: Path | None = None
    knowledge_files: list[Path] = Field(default_factory=list)

    @property
    def name(self) -> str:
        return self.manifest.name

    def system_prompt(self) -> str:
        """Compose the coach persona with shared coaching behavior + guardrails.

        This is what the agent sends as the ``system`` message.
        """
        parts: list[str] = [self.persona.strip()]

        behavior: list[str] = []
        if self.manifest.style.both_sides:
            behavior.append(
                "- For every meaningful recommendation, present BOTH sides: the strongest case "
                "for it and the strongest case against, then give your reasoned take."
            )
        if self.manifest.style.socratic:
            behavior.append(
                "- Prefer asking a clarifying question before prescribing a plan."
            )
        if self.manifest.style.rest_reminders:
            behavior.append(
                "- Watch for signs of overwork or fatigue and proactively encourage breaks "
                "and rest. Rest is part of progress, not a reward for it."
            )
        behavior.append(
            "- Ground advice in evidence where possible; be honest about uncertainty."
        )
        if behavior:
            parts.append("## How you coach\n" + "\n".join(behavior))

        g = self.manifest.guardrails
        if g.disclaimers or g.refuse_topics or g.escalate_to_professional:
            lines = ["## Safety guardrails (non-negotiable)"]
            for d in g.disclaimers:
                lines.append(f"- State when relevant: {d}")
            if g.refuse_topics:
                lines.append(
                    "- Do not give advice on: " + ", ".join(g.refuse_topics) + "."
                )
            if g.escalate_to_professional:
                lines.append(
                    "- If the user raises any of the following, urge them to seek a qualified "
                    "professional immediately: " + ", ".join(g.escalate_to_professional) + "."
                )
            parts.append("\n".join(lines))

        return "\n\n".join(parts)
