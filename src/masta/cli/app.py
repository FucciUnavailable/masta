"""The ``masta`` command-line entrypoint.

Commands: chat, coach (list/use), goals, checkin, providers, config. Designed so the read-only
commands (coach list, providers, config, goals) work without any API keys configured.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from masta.config import get_settings
from masta.memory.repository import Repository

app = typer.Typer(
    name="masta",
    help="An AI sensei for your goals — coaching, not just prompting.",
    no_args_is_help=True,
    add_completion=False,
)
coach_app = typer.Typer(help="List and select coaches.", no_args_is_help=True)
app.add_typer(coach_app, name="coach")

console = Console()


# --- chat -------------------------------------------------------------------
@app.command()
def chat(
    coach: str = typer.Option(..., "--coach", "-c", help="Coach to talk to."),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Override the model profile."),
) -> None:
    """Start an interactive coaching session."""
    from masta.cli.repl import run_repl

    run_repl(coach_name=coach, profile=profile)


# --- coach ------------------------------------------------------------------
@coach_app.command("list")
def coach_list() -> None:
    """List available coaches."""
    from masta.coaches.registry import CoachRegistry

    registry = CoachRegistry()
    if not len(registry):
        console.print(
            "[yellow]No coaches found.[/] Add one under examples/coaches/ "
            "or ~/.config/masta/coaches/."
        )
        raise typer.Exit()

    table = Table(title="Coaches")
    table.add_column("name", style="cyan")
    table.add_column("display name")
    table.add_column("tags", style="dim")
    table.add_column("description")
    for c in registry.all():
        m = c.manifest
        table.add_row(m.name, m.resolved_display_name(), ", ".join(m.tags), m.description.strip())
    console.print(table)


@coach_app.command("use")
def coach_use(name: str = typer.Argument(..., help="Coach name to inspect.")) -> None:
    """Show a coach's resolved system prompt (handy for debugging personas)."""
    from masta.coaches.loader import load_coach

    try:
        c = load_coach(name)
    except KeyError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=1) from exc
    console.rule(f"[bold]{c.manifest.resolved_display_name()}")
    console.print(c.system_prompt())


# --- goals ------------------------------------------------------------------
@app.command()
def goals(
    add: str | None = typer.Option(None, "--add", help="Add a new goal with this title."),
    coach: str | None = typer.Option(None, "--coach", help="Associate the new goal with a coach."),
) -> None:
    """List goals, or add one with --add."""
    repo = Repository()
    if add:
        g = repo.add_goal(title=add, coach=coach)
        console.print(f"[green]Added goal #{g.id}:[/] {g.title}")
        return

    rows = repo.list_goals()
    if not rows:
        console.print('No goals yet. Add one: [cyan]masta goals --add "Learn X"[/]')
        return
    table = Table(title="Your goals")
    table.add_column("#", justify="right")
    table.add_column("title")
    table.add_column("status")
    table.add_column("coach", style="dim")
    status_colors = {
        "active": "green",
        "achieved": "bold green",
        "paused": "yellow",
        "abandoned": "red",
    }
    for g in rows:
        color = status_colors.get(g.status.value, "white")
        table.add_row(str(g.id), g.title, f"[{color}]{g.status.value}[/]", g.coach or "")
    console.print(table)


@app.command()
def checkin(
    note: str = typer.Option("", "--note", "-n", help="How are things going?"),
    energy: int | None = typer.Option(None, "--energy", help="Energy 1-5 (feeds rest reminders)."),
    mood: int | None = typer.Option(None, "--mood", help="Mood 1-5."),
    goal_id: int | None = typer.Option(None, "--goal", help="Goal id this check-in relates to."),
) -> None:
    """Log a progress check-in."""
    repo = Repository()
    c = repo.add_checkin(note=note, goal_id=goal_id, mood=mood, energy=energy)
    console.print(f"[green]Logged check-in #{c.id}.[/]")
    if energy is not None and energy <= 2:
        console.print("[yellow]Low energy noted — consider a real break or rest day. 😴[/]")


# --- providers / config -----------------------------------------------------
@app.command()
def providers() -> None:
    """List configured model profiles and whether each provider looks usable."""
    from masta.llm.profiles import list_profiles

    table = Table(title="Model profiles")
    table.add_column("profile", style="cyan")
    table.add_column("model")
    table.add_column("provider")
    table.add_column("configured")
    table.add_column("default")
    for s in list_profiles():
        table.add_row(
            s.name,
            s.profile.model,
            s.provider,
            "[green]yes[/]" if s.configured else "[red]no[/]",
            "★" if s.is_default else "",
        )
    console.print(table)
    console.print("[dim]Set keys in .env; edit profiles in ~/.config/masta/config.toml[/]")


@app.command()
def config() -> None:
    """Show resolved configuration paths and defaults."""
    s = get_settings()
    table = Table(title="masta config")
    table.add_column("key", style="cyan")
    table.add_column("value")
    table.add_row("config_dir", str(s.config_dir))
    table.add_row("config_file", str(s.config_file))
    table.add_row("data_dir", str(s.data_dir))
    table.add_row("db_path", str(s.db_path))
    table.add_row("default_profile", s.default_profile)
    table.add_row("user_coaches_dir", str(s.user_coaches_dir))
    console.print(table)


if __name__ == "__main__":  # pragma: no cover
    app()
