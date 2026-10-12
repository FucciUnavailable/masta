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


def test_session_history_is_scoped_to_its_chat_session(temp_repo):
    coach = load_coach("backend-engineering")
    other = temp_repo.add_chat_session(coach=coach.name)
    temp_repo.add_message("user", "from another chat", coach=coach.name, session_id=other.id)

    chat = temp_repo.add_chat_session(coach=coach.name)
    provider = FakeProvider()
    session = CoachingSession(coach=coach, provider=provider, repo=temp_repo, session_id=chat.id)
    session.send("first")
    session.send("second")

    sent = [m.content for m in provider.calls[-1] if m.role != "system"]
    assert sent == ["first", "ok", "second"]
    assert len(temp_repo.recent_messages(session_id=chat.id)) == 4


def test_stream_keeps_the_partial_reply_when_cut_short(temp_repo):
    coach = load_coach("backend-engineering")
    provider = FakeProvider(response="one two three")
    session = CoachingSession(coach=coach, provider=provider, repo=temp_repo)

    stream = session.stream("hi")
    assert next(stream) == "one "
    stream.close()  # what happens when the reader goes away

    stored = temp_repo.recent_messages(coach=coach.name)
    assert [(m.role, m.content) for m in stored] == [("user", "hi"), ("assistant", "one ")]
