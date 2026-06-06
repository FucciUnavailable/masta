"""The interactive chat loop (Rich).

Slash commands inside the chat:
  /model <profile>   swap the LLM provider mid-session
  /both <topic>      run an explicit both-sides analysis
  /plan <goal>       generate a milestone plan and offer to save it as a goal
  /help              show commands
  /exit              leave
"""

from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from masta.agent import CoachingSession
from masta.coaches.loader import load_coach
from masta.memory.repository import Repository

console = Console()

_HELP = """\
[bold]Commands[/]
  /model <profile>   switch LLM provider (e.g. /model local)
  /both <topic>      steelman both sides of a question
  /plan <goal>       break a goal into milestones (offers to save it)
  /help              this help
  /exit              end the session
"""


def run_repl(coach_name: str, profile: str | None = None) -> None:
    try:
        coach = load_coach(coach_name)
    except KeyError as exc:
        console.print(f"[red]{exc}[/]")
        return

    repo = Repository()
    session = CoachingSession(coach=coach, repo=repo)
    if profile:
        session.set_provider(profile)

    title = coach.manifest.resolved_display_name()
    console.print(
        Panel.fit(
            f"[bold cyan]{title}[/]\n[dim]model: {session.provider.model}[/]\n"
            "Type /help for commands, /exit to leave.",
            title="🥋 masta",
        )
    )

    while True:
        try:
            user_input = console.input("[bold green]you ›[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Take care. Rest counts too. 😴[/]")
            return

        if not user_input:
            continue
        if user_input in ("/exit", "/quit"):
            console.print("[dim]Session saved. See you next time.[/]")
            return
        if user_input == "/help":
            console.print(_HELP)
            continue
        if _handle_slash(session, user_input):
            continue

        # Normal turn — stream the reply.
        console.print(f"[bold cyan]{title} ›[/] ", end="")
        try:
            chunks: list[str] = []
            for piece in session.stream(user_input):
                console.print(piece, end="")
                chunks.append(piece)
            console.print()  # newline after stream
        except Exception as exc:  # surface provider/setup errors without crashing the REPL
            console.print(f"\n[red]LLM error:[/] {exc}")
            console.print("[dim]Check your API keys (.env) and `masta providers`.[/]")


def _handle_slash(session: CoachingSession, text: str) -> bool:
    """Handle in-chat slash commands. Returns True if the input was a command."""
    if text.startswith("/model"):
        _, _, profile = text.partition(" ")
        profile = profile.strip()
        if not profile:
            console.print("[yellow]Usage: /model <profile>[/]")
            return True
        try:
            session.set_provider(profile)
            console.print(f"[green]Switched to[/] {session.provider.model}")
        except KeyError as exc:
            console.print(f"[red]{exc}[/]")
        return True

    if text.startswith("/both"):
        _, _, topic = text.partition(" ")
        if not topic.strip():
            console.print("[yellow]Usage: /both <topic>[/]")
            return True
        try:
            result = session.both_sides(topic.strip())
            console.print(Markdown(result.to_markdown()))
        except Exception as exc:
            console.print(f"[red]LLM error:[/] {exc}")
        return True

    if text.startswith("/plan"):
        _, _, goal = text.partition(" ")
        if not goal.strip():
            console.print("[yellow]Usage: /plan <goal>[/]")
            return True
        try:
            plan = session.plan(goal.strip())
            console.print(Markdown(plan.to_markdown()))
            if console.input("[dim]Save as a goal? [y/N] [/]").strip().lower() == "y":
                g = session.repo.add_goal(title=plan.goal, coach=session.coach.name)
                for i, step in enumerate(plan.steps):
                    session.repo.add_milestone(g.id, step.title, order=i)
                console.print(f"[green]Saved goal #{g.id} with {len(plan.steps)} milestones.[/]")
        except Exception as exc:
            console.print(f"[red]LLM error:[/] {exc}")
        return True

    return False
