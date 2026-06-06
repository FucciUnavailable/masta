"""Discover and load coaches from disk (and, later, entry points).

Search order (later sources override earlier ones by coach name):
1. Bundled examples shipped with the repo (``examples/coaches/``).
2. The user's coach directory (``~/.config/masta/coaches/``).
3. Python entry points in the ``masta.coaches`` group (community packages).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from masta.coaches.model import Coach, CoachManifest
from masta.config import get_settings


def _bundled_coaches_dir() -> Path:
    # src/masta/coaches/loader.py -> repo root -> examples/coaches
    return Path(__file__).resolve().parents[3] / "examples" / "coaches"


def _coach_search_dirs() -> list[Path]:
    settings = get_settings()
    return [_bundled_coaches_dir(), settings.user_coaches_dir]


def _load_from_dir(path: Path) -> Coach:
    """Load a single coach from a directory containing coach.yaml + persona.md."""
    manifest_file = path / "coach.yaml"
    persona_file = path / "persona.md"
    if not manifest_file.is_file():
        raise FileNotFoundError(f"No coach.yaml in {path}")

    data = yaml.safe_load(manifest_file.read_text(encoding="utf-8")) or {}
    data.setdefault("name", path.name)
    manifest = CoachManifest(**data)

    persona = persona_file.read_text(encoding="utf-8") if persona_file.is_file() else ""
    knowledge_dir = path / "knowledge"
    knowledge = (
        sorted(p for p in knowledge_dir.glob("**/*") if p.is_file())
        if knowledge_dir.is_dir()
        else []
    )
    return Coach(manifest=manifest, persona=persona, path=path, knowledge_files=knowledge)


def _load_entry_point_coaches() -> dict[str, Coach]:
    """Load coaches advertised by installed packages via the ``masta.coaches`` group.

    Each entry point should resolve to a directory path (str/Path) or a callable returning one.
    """
    coaches: dict[str, Coach] = {}
    try:
        from importlib.metadata import entry_points

        eps = entry_points(group="masta.coaches")
    except Exception:  # pragma: no cover - defensive; varies by Python/packaging
        return coaches

    for ep in eps:
        try:
            target = ep.load()
            directory = Path(target() if callable(target) else target)
            if directory.is_dir():
                coach = _load_from_dir(directory)
                coaches[coach.name] = coach
        except Exception:  # pragma: no cover - never let a bad plugin break startup
            continue
    return coaches


def load_coaches() -> dict[str, Coach]:
    """Return all discoverable coaches keyed by name."""
    coaches: dict[str, Coach] = {}
    for base in _coach_search_dirs():
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir()):
            if child.is_dir() and (child / "coach.yaml").is_file():
                coach = _load_from_dir(child)
                coaches[coach.name] = coach
    coaches.update(_load_entry_point_coaches())
    return coaches


def load_coach(name: str) -> Coach:
    """Load one coach by name, raising ``KeyError`` if it isn't found."""
    coaches = load_coaches()
    if name not in coaches:
        raise KeyError(
            f"Unknown coach {name!r}. Available: {', '.join(sorted(coaches)) or '(none)'}"
        )
    return coaches[name]
