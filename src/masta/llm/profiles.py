"""Helpers for listing and resolving model profiles.

Profiles are defined in config (see :mod:`masta.config`). These helpers back the
``masta providers`` command and the in-chat ``/model`` switch.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from masta.config import ModelProfile, get_settings

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


def _provider_of(model: str) -> str:
    return model.split("/", 1)[0] if "/" in model else model


def _is_configured(model: str) -> bool:
    provider = _provider_of(model)
    required = _PROVIDER_ENV.get(provider)
    if required is None:
        return False  # unknown provider — can't verify
    if not required:
        return True  # local / keyless
    return all(os.environ.get(var) for var in required)


def list_profiles() -> list[ProfileStatus]:
    """Return every configured profile with whether its provider looks usable."""
    settings = get_settings()
    statuses: list[ProfileStatus] = []
    for name, profile in sorted(settings.profiles.items()):
        statuses.append(
            ProfileStatus(
                name=name,
                profile=profile,
                is_default=(name == settings.default_profile),
                configured=_is_configured(profile.model),
                provider=_provider_of(profile.model),
            )
        )
    return statuses
