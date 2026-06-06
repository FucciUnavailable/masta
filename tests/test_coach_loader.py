"""The bundled example coaches load and assemble sensible system prompts with guardrails."""

from __future__ import annotations

from masta.coaches.loader import load_coach, load_coaches
from masta.coaches.registry import CoachRegistry


def test_bundled_coaches_load():
    coaches = load_coaches()
    assert "backend-engineering" in coaches
    assert "weight-loss-safe" in coaches


def test_registry_lists_coaches():
    registry = CoachRegistry()
    assert "backend-engineering" in registry
    assert len(registry) >= 2


def test_system_prompt_includes_behavior_and_guardrails():
    coach = load_coach("weight-loss-safe")
    prompt = coach.system_prompt()
    # Persona text is present.
    assert "Weight-Loss" in prompt or "weight" in prompt.lower()
    # Both-sides behavior is injected.
    assert "BOTH sides" in prompt
    # Rest reminders are injected.
    assert "rest" in prompt.lower()
    # Safety guardrails surface escalation triggers.
    assert "professional" in prompt.lower()


def test_unknown_coach_raises():
    import pytest

    with pytest.raises(KeyError):
        load_coach("does-not-exist")
