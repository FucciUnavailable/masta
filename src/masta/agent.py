"""The orchestrator — ties a coach, the LLM, memory, and reasoning into a turn loop.

Responsibilities per turn:
1. Build the prompt: coach system prompt + recent conversation from memory + the new input.
2. Call the provider (streaming or not).
3. Persist the exchange so future sessions have continuity.

Tool execution and the deeper reasoning modules (evidence, recovery, rest) plug in here as
they come online; ``both_sides``/``plan`` are exposed as explicit helpers the CLI can call.
"""

from __future__ import annotations

from collections.abc import Iterator

from masta.coaches.model import Coach
from masta.llm import get_provider
from masta.llm.base import LLMProvider, Message
from masta.memory.repository import Repository
from masta.reasoning.both_sides import BothSides, both_sides
from masta.reasoning.planner import GoalPlan, plan_goal


class CoachingSession:
    """A live coaching session with one coach, backed by persistent memory."""

    def __init__(
        self,
        coach: Coach,
        provider: LLMProvider | None = None,
        repo: Repository | None = None,
        history_limit: int = 20,
    ) -> None:
        self.coach = coach
        self.repo = repo or Repository()
        self.history_limit = history_limit
        # Resolve the provider from the coach's profile (or the global default).
        self.provider = provider or get_provider(coach.manifest.model_profile)

    def set_provider(self, profile: str) -> None:
        """Swap the LLM provider mid-session (the ``/model`` command)."""
        self.provider = get_provider(profile)

    def _build_messages(self, user_input: str) -> list[Message]:
        messages: list[Message] = [
            Message(role="system", content=self.coach.system_prompt())
        ]
        # Inject a compact memory snapshot so the coach has continuity.
        snapshot = self._memory_snapshot()
        if snapshot:
            messages.append(Message(role="system", content=snapshot))
        for m in self.repo.recent_messages(limit=self.history_limit, coach=self.coach.name):
            if m.role in ("user", "assistant"):
                messages.append(Message(role=m.role, content=m.content))
        messages.append(Message(role="user", content=user_input))
        return messages

    def _memory_snapshot(self) -> str:
        """A short context block of active goals + the latest check-in."""
        from masta.memory.models import GoalStatus

        goals = self.repo.list_goals(status=GoalStatus.active)
        checkins = self.repo.recent_checkins(limit=1)
        if not goals and not checkins:
            return ""
        lines = ["Context the coach should remember:"]
        if goals:
            lines.append("Active goals:")
            lines += [f"- {g.title}" for g in goals]
        if checkins:
            c = checkins[0]
            lines.append(f"Latest check-in: {c.note or '(no note)'}")
        return "\n".join(lines)

    def send(self, user_input: str) -> str:
        """Send a message, persist both sides, and return the reply."""
        messages = self._build_messages(user_input)
        result = self.provider.complete(messages)
        self.repo.add_message("user", user_input, coach=self.coach.name)
        self.repo.add_message("assistant", result.text, coach=self.coach.name)
        return result.text

    def stream(self, user_input: str) -> Iterator[str]:
        """Stream the reply, persisting the full exchange once complete."""
        messages = self._build_messages(user_input)
        self.repo.add_message("user", user_input, coach=self.coach.name)
        chunks: list[str] = []
        for piece in self.provider.stream(messages):
            chunks.append(piece)
            yield piece
        self.repo.add_message("assistant", "".join(chunks), coach=self.coach.name)

    # --- explicit reasoning helpers -----------------------------------------
    def both_sides(self, topic: str, context: str = "") -> BothSides:
        return both_sides(self.provider, topic, context)

    def plan(self, goal: str, context: str = "") -> GoalPlan:
        return plan_goal(self.provider, goal, context)
