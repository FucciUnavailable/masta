"""LLM provider layer.

The *only* place in masta that knows about concrete LLM backends. Everything else depends on
the :class:`~masta.llm.base.LLMProvider` protocol, so swapping providers — or replacing
LiteLLM entirely — never ripples outward.
"""

from __future__ import annotations

from masta.config import ModelProfile, get_settings
from masta.llm.base import CompletionResult, LLMProvider, Message, Role
from masta.llm.litellm_provider import LiteLLMProvider

__all__ = [
    "CompletionResult",
    "LLMProvider",
    "Message",
    "Role",
    "LiteLLMProvider",
    "get_provider",
]


def get_provider(profile: str | ModelProfile | None = None) -> LLMProvider:
    """Return a provider bound to a model profile.

    ``profile`` may be a profile name, a :class:`ModelProfile`, or ``None`` for the default.
    """
    if isinstance(profile, ModelProfile):
        resolved = profile
    else:
        resolved = get_settings().profile(profile)
    return LiteLLMProvider(resolved)
