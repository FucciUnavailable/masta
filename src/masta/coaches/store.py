"""Create, update, and delete coaches in the user's coach directory.

Only coaches under ``~/.config/masta/coaches/`` are writable. Bundled examples and coaches
shipped by packages are read-only; copy one under a new name to customise it.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import yaml

from masta.coaches.loader import _load_from_dir
from masta.coaches.model import Coach, CoachManifest
from masta.config import get_settings

# The name becomes a directory, so keep it to a plain slug.
NAME_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


def _coach_dir(name: str) -> Path:
    if not re.fullmatch(NAME_PATTERN, name):
        raise ValueError(
            f"Invalid coach name {name!r}: use lowercase letters, digits, and single hyphens."
        )
    return get_settings().user_coaches_dir / name


def is_user_coach(coach: Coach) -> bool:
    """Whether this coach lives in the user's coach directory, and so can be edited."""
    if coach.path is None:
        return False
    return coach.path.resolve().parent == get_settings().user_coaches_dir.resolve()


def save_coach(manifest: CoachManifest, persona: str) -> Coach:
    """Write ``coach.yaml`` and ``persona.md`` for a user coach, creating it if needed."""
    directory = _coach_dir(manifest.name)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "coach.yaml").write_text(
        yaml.safe_dump(manifest.model_dump(exclude_none=True), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    (directory / "persona.md").write_text(persona.strip() + "\n", encoding="utf-8")
    return _load_from_dir(directory)


def delete_coach(name: str) -> None:
    """Remove a user coach's directory, including any ``knowledge/`` files in it."""
    directory = _coach_dir(name)
    if not (directory / "coach.yaml").is_file():
        raise KeyError(f"No user coach named {name!r}.")
    shutil.rmtree(directory)
