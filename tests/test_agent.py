"""The coaching session wires coach + provider + memory and persists exchanges."""

from __future__ import annotations

from masta.agent import CoachingSession
from masta.coaches.loader import load_coach
from tests.conftest import FakeProvider


def test_session_send_persists_exchange(temp_repo):
    coach = load_coach("backend-engineering")
    provider = FakeProvider(response="Let's start with data modeling.")
    session = CoachingSession(coach=coach, provider=provider, repo=temp_repo)

    reply = session.send("How do I get better at system design?")
    assert reply == "Let's start with data modeling."

    # System prompt was sent, plus the user turn was stored.
    assert provider.calls[0][0].role == "system"
    stored = temp_repo.recent_messages(coach="backend-engineering")
    assert [m.role for m in stored] == ["user", "assistant"]


def test_session_injects_active_goals_into_context(temp_repo):
    temp_repo.add_goal("Master Postgres", coach="backend-engineering")
    coach = load_coach("backend-engineering")
    provider = FakeProvider()
    session = CoachingSession(coach=coach, provider=provider, repo=temp_repo)

    session.send("hi")
    system_blocks = "\n".join(m.content for m in provider.calls[0] if m.role == "system")
    assert "Master Postgres" in system_blocks
