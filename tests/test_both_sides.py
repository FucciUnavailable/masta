"""Reasoning modules parse structured JSON and degrade gracefully on bad output."""

from __future__ import annotations

from masta.reasoning.both_sides import both_sides
from masta.reasoning.planner import plan_goal
from tests.conftest import FakeProvider


def test_both_sides_parses_json():
    provider = FakeProvider(
        response='{"for": ["fast"], "against": ["risky"], "recommendation": "go slow"}'
    )
    result = both_sides(provider, "Should I use a NoSQL database?")
    assert result.pros == ["fast"]
    assert result.cons == ["risky"]
    assert result.recommendation == "go slow"
    assert "Both sides" in result.to_markdown()


def test_both_sides_handles_prose_fallback():
    provider = FakeProvider(response="I could not produce JSON, sorry.")
    result = both_sides(provider, "anything")
    assert result.pros == []
    assert "could not produce JSON" in result.recommendation


def test_plan_goal_parses_steps():
    provider = FakeProvider(
        response='{"summary": "do it", "steps": [{"title": "step one", "detail": "x"}]}'
    )
    plan = plan_goal(provider, "Learn Rust")
    assert plan.summary == "do it"
    assert plan.steps[0].title == "step one"
    assert "Learn Rust" in plan.to_markdown()
