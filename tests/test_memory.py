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
