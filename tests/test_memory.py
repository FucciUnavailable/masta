"""Memory persistence: goals, milestones, check-ins, and conversation history round-trip."""

from __future__ import annotations

from masta.memory.models import GoalStatus


def test_goal_lifecycle(temp_repo):
    g = temp_repo.add_goal("Learn distributed systems", coach="backend-engineering")
    assert g.id is not None

    goals = temp_repo.list_goals()
    assert [x.title for x in goals] == ["Learn distributed systems"]

    temp_repo.set_goal_status(g.id, GoalStatus.achieved)
    assert temp_repo.list_goals(status=GoalStatus.achieved)[0].id == g.id
    assert temp_repo.list_goals(status=GoalStatus.active) == []


def test_milestones(temp_repo):
    g = temp_repo.add_goal("Ship a service")
    m = temp_repo.add_milestone(g.id, "Design the schema", order=0)
    assert m.done is False
    done = temp_repo.complete_milestone(m.id)
    assert done.done is True


def test_checkins_and_messages(temp_repo):
    temp_repo.add_checkin(note="tired but progressing", energy=2)
    recent = temp_repo.recent_checkins()
    assert recent[0].energy == 2

    temp_repo.add_message("user", "hello", coach="backend-engineering")
    temp_repo.add_message("assistant", "hi there", coach="backend-engineering")
    msgs = temp_repo.recent_messages(coach="backend-engineering")
    # Chronological order for prompt construction.
    assert [m.role for m in msgs] == ["user", "assistant"]


def test_chat_sessions_group_messages(temp_repo):
    first = temp_repo.add_chat_session(coach="backend-engineering")
    second = temp_repo.add_chat_session(coach="backend-engineering")
    assert first.title == ""

    temp_repo.add_message(
        "user", "How do I   learn Postgres?", coach=first.coach, session_id=first.id
    )
    temp_repo.add_message("assistant", "Start small.", coach=first.coach, session_id=first.id)
    temp_repo.add_message("user", "x" * 200, coach=second.coach, session_id=second.id)

    # The first user message names the session; later messages leave the title alone.
    assert temp_repo.get_chat_session(first.id).title == "How do I learn Postgres?"
    assert len(temp_repo.get_chat_session(second.id).title) == 60

    assert [m.content for m in temp_repo.recent_messages(session_id=first.id)] == [
        "How do I   learn Postgres?",
        "Start small.",
    ]
    # Most recently active first.
    assert [s.id for s in temp_repo.list_chat_sessions()] == [second.id, first.id]
    assert temp_repo.list_chat_sessions(coach="someone-else") == []


def test_delete_chat_session_removes_its_messages(temp_repo):
    chat = temp_repo.add_chat_session(coach="backend-engineering")
    temp_repo.add_message("user", "hi", coach=chat.coach, session_id=chat.id)
    temp_repo.add_message("user", "terminal chat", coach=chat.coach)

    assert temp_repo.delete_chat_session(chat.id) is True
    assert temp_repo.delete_chat_session(chat.id) is False
    assert temp_repo.get_chat_session(chat.id) is None
    assert [m.content for m in temp_repo.recent_messages()] == ["terminal chat"]


def test_database_from_before_sessions_is_upgraded(tmp_path):
    import sqlite3

    from masta.memory.repository import Repository

    db_path = tmp_path / "old.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE message (id INTEGER PRIMARY KEY, coach VARCHAR, role VARCHAR NOT NULL,"
            " content VARCHAR NOT NULL, created_at DATETIME NOT NULL)"
        )
        conn.execute(
            "INSERT INTO message (coach, role, content, created_at)"
            " VALUES ('backend-engineering', 'user', 'old', '2026-01-01 00:00:00')"
        )

    repo = Repository(db_path=db_path)
    chat = repo.add_chat_session(coach="backend-engineering")
    repo.add_message("user", "new", coach=chat.coach, session_id=chat.id)

    assert [m.content for m in repo.recent_messages()] == ["old", "new"]
    assert [m.session_id for m in repo.recent_messages()] == [None, chat.id]
