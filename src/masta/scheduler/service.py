"""Scheduler service (stub).

Post-MVP: an APScheduler-backed service (optional ``schedule`` extra) that fires recurring
check-in prompts and break/rest reminders, dispatching through :mod:`masta.tools.notify`.
"""

from __future__ import annotations


class SchedulerService:  # pragma: no cover - stub
    def start(self) -> None:
        raise NotImplementedError(
            "The scheduler is planned for a post-MVP milestone (install the 'schedule' extra)."
        )

    def schedule_checkin(self, cron: str) -> None:
        raise NotImplementedError("Planned for a post-MVP milestone.")
