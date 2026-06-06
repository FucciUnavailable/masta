"""Configuration: layered settings from defaults, a TOML config file, and the environment.

Precedence (low → high): built-in defaults < ``config.toml`` < environment variables
(prefixed ``MASTA_``). Provider API keys are read by LiteLLM straight from the environment
(see ``docs/providers.md``); we never store secrets in the config file.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

try:  # Python 3.11+ has tomllib; fall back for 3.10.
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - exercised only on 3.10
    import tomli as tomllib  # type: ignore[no-redef]

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelProfile(BaseModel):
    """A named, swappable set of LLM parameters.

    ``model`` is a LiteLLM model string, e.g. ``anthropic/claude-sonnet-4-6`` or
    ``ollama/llama3.1`` — that single field is what makes masta provider-agnostic.
    """

    model: str
    temperature: float = 0.7
    max_tokens: int | None = None
    api_base: str | None = None
    extra: dict[str, object] = Field(default_factory=dict)


# Sensible starter profiles so a fresh install can run against whatever the user has keys for.
DEFAULT_PROFILES: dict[str, ModelProfile] = {
    "claude": ModelProfile(model="anthropic/claude-sonnet-4-6"),
    "openai": ModelProfile(model="openai/gpt-4o"),
    "deepseek": ModelProfile(model="deepseek/deepseek-chat"),
    "local": ModelProfile(model="ollama/llama3.1", api_base="http://localhost:11434"),
}


def _default_config_dir() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "masta"


def _default_data_dir() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "masta"


class Settings(BaseSettings):
    """Resolved application settings.

    Environment overrides use the ``MASTA_`` prefix, e.g. ``MASTA_DEFAULT_PROFILE=local``.
    """

    model_config = SettingsConfigDict(env_prefix="MASTA_", extra="ignore")

    config_dir: Path = Field(default_factory=_default_config_dir)
    data_dir: Path = Field(default_factory=_default_data_dir)
    default_profile: str = "claude"
    profiles: dict[str, ModelProfile] = Field(default_factory=lambda: dict(DEFAULT_PROFILES))

    # Where user-authored coaches live (in addition to the bundled examples + entry points).
    @property
    def user_coaches_dir(self) -> Path:
        return self.config_dir / "coaches"

    @property
    def config_file(self) -> Path:
        return self.config_dir / "config.toml"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "masta.db"

    def profile(self, name: str | None = None) -> ModelProfile:
        """Return a profile by name, falling back to the default profile."""
        key = name or self.default_profile
        if key not in self.profiles:
            raise KeyError(
                f"Unknown model profile {key!r}. Known profiles: {', '.join(sorted(self.profiles))}"
            )
        return self.profiles[key]


def _load_toml(path: Path) -> dict:
    if not path.is_file():
        return {}
    with path.open("rb") as fh:
        return tomllib.load(fh)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Build settings from the TOML config file, then apply environment overrides.

    Cached so the rest of the app shares one instance. Call ``get_settings.cache_clear()``
    in tests that need a fresh load.
    """
    base = Settings()  # picks up env + defaults
    raw = _load_toml(base.config_file)

    profiles = dict(DEFAULT_PROFILES)
    for name, data in (raw.get("profiles") or {}).items():
        profiles[name] = ModelProfile(**data)

    return Settings(
        config_dir=base.config_dir,
        data_dir=Path(raw.get("data_dir", base.data_dir)).expanduser(),
        default_profile=os.environ.get(
            "MASTA_DEFAULT_PROFILE", raw.get("default_profile", base.default_profile)
        ),
        profiles=profiles,
    )
