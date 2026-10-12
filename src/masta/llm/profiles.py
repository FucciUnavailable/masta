"""Helpers for listing and resolving model profiles.

Profiles are defined in config (see :mod:`masta.config`). These helpers back the
``masta providers`` command, the in-chat ``/model`` switch, and the web UI's settings page.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from masta.config import (
    DEFAULT_PROFILES,
    ModelProfile,
    get_settings,
    read_config_file,
    update_config_file,
)

# Heuristic: which env var indicates a backend is configured, keyed by model-string prefix.
_PROVIDER_ENV: dict[str, tuple[str, ...]] = {
    "anthropic": ("ANTHROPIC_API_KEY",),
    "openai": ("OPENAI_API_KEY",),
    "azure": ("AZURE_API_KEY",),
    "deepseek": ("DEEPSEEK_API_KEY",),
    "ollama": (),  # local; assumed available
}


@dataclass
class ProfileStatus:
    name: str
    profile: ModelProfile
    is_default: bool
    configured: bool
    provider: str
    missing_env: list[str] = field(default_factory=list)  # what to set to make it usable
    builtin: bool = False  # ships with masta
    customized: bool = False  # defined or overridden in config.toml


def _provider_of(model: str) -> str:
    return model.split("/", 1)[0] if "/" in model else model


def _missing_env(model: str) -> list[str]:
    required = _PROVIDER_ENV.get(_provider_of(model), ())
    return [var for var in required if not os.environ.get(var)]


def _is_configured(model: str) -> bool:
    if _provider_of(model) not in _PROVIDER_ENV:
        return False  # unknown provider — can't verify
    return not _missing_env(model)  # nothing required means local / keyless


def list_profiles() -> list[ProfileStatus]:
    """Return every configured profile with whether its provider looks usable."""
    settings = get_settings()
    in_file = read_config_file().get("profiles") or {}
    statuses: list[ProfileStatus] = []
    for name, profile in sorted(settings.profiles.items()):
        statuses.append(
            ProfileStatus(
                name=name,
                profile=profile,
                is_default=(name == settings.default_profile),
                configured=_is_configured(profile.model),
                provider=_provider_of(profile.model),
                missing_env=_missing_env(profile.model),
                builtin=name in DEFAULT_PROFILES,
                customized=name in in_file,
            )
        )
    return statuses


def save_profile(name: str, profile: ModelProfile) -> None:
    """Create or replace a profile in ``config.toml``."""
    data = profile.model_dump(exclude_none=True)
    if not data["extra"]:
        del data["extra"]

    def mutate(raw: dict) -> None:
        raw.setdefault("profiles", {})[name] = data

    update_config_file(mutate)


def remove_profile(name: str) -> None:
    """Drop a profile from ``config.toml``; a built-in one reverts to its shipped values.

    Raises ``KeyError`` if the file doesn't define it, and ``ValueError`` if removing it would
    leave the default profile pointing at nothing.
    """
    if name not in (read_config_file().get("profiles") or {}):
        raise KeyError(f"Profile {name!r} is not defined in config.toml.")
    if name == get_settings().default_profile and name not in DEFAULT_PROFILES:
        raise ValueError(f"{name!r} is the default profile; pick another default first.")

    def mutate(raw: dict) -> None:
        del raw["profiles"][name]

    update_config_file(mutate)


def default_profile_from_env() -> bool:
    """Whether ``MASTA_DEFAULT_PROFILE`` is set, which overrides ``config.toml``."""
    return bool(os.environ.get("MASTA_DEFAULT_PROFILE"))


def set_default_profile(name: str) -> None:
    """Make ``name`` the default profile. Raises ``KeyError`` if it isn't a known profile."""
    get_settings().profile(name)

    def mutate(raw: dict) -> None:
        raw["default_profile"] = name

    update_config_file(mutate)
