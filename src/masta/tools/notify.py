"""Desktop notifications (stub).

Post-MVP: send cross-platform notifications (via the optional ``desktop-notifier`` extra) for
check-in reminders, break/rest nudges, and milestone celebrations.
"""

from __future__ import annotations


def notify(title: str, message: str) -> None:  # pragma: no cover - stub
    raise NotImplementedError(
        "Notifications are planned for a post-MVP milestone (install the 'notify' extra)."
    )
