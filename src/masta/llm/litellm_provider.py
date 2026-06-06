"""The one concrete :class:`LLMProvider`, delegating to LiteLLM.

LiteLLM normalizes 100+ backends behind one ``completion()`` call, selected by model string.
We wrap it thinly so the rest of masta never imports ``litellm`` directly and we could swap
the router later without touching callers.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from masta.config import ModelProfile
from masta.llm.base import CompletionResult, Message


class LiteLLMProvider:
    """Adapter from masta's :class:`LLMProvider` protocol onto LiteLLM."""

    def __init__(self, profile: ModelProfile) -> None:
        self._profile = profile

    @property
    def model(self) -> str:
        return self._profile.model

    def _params(self, overrides: dict[str, object]) -> dict[str, object]:
        params: dict[str, object] = {
            "model": self._profile.model,
            "temperature": self._profile.temperature,
        }
        if self._profile.max_tokens is not None:
            params["max_tokens"] = self._profile.max_tokens
        if self._profile.api_base:
            params["api_base"] = self._profile.api_base
        params.update(self._profile.extra)
        params.update(overrides)
        return params

    @staticmethod
    def _payload(messages: Iterable[Message]) -> list[dict[str, object]]:
        return [m.to_dict() for m in messages]

    def complete(self, messages: Iterable[Message], **overrides: object) -> CompletionResult:
        # Imported lazily so importing masta doesn't pull in the heavy LiteLLM stack and so
        # tests can run without the dependency installed.
        from litellm import completion

        params = self._params(overrides)
        response = completion(messages=self._payload(messages), **params)
        choice = response.choices[0]
        usage = getattr(response, "usage", None)
        return CompletionResult(
            text=choice.message.content or "",
            model=getattr(response, "model", self._profile.model),
            raw=response,
            usage=dict(usage) if usage else {},
        )

    def stream(self, messages: Iterable[Message], **overrides: object) -> Iterator[str]:
        from litellm import completion

        params = self._params(overrides)
        params["stream"] = True
        for chunk in completion(messages=self._payload(messages), **params):
            delta = chunk.choices[0].delta
            piece = getattr(delta, "content", None)
            if piece:
                yield piece

    def embed(self, texts: Iterable[str]) -> list[list[float]]:
        from litellm import embedding

        # Reuse the chat model string's provider where possible; callers can override the
        # model via a profile dedicated to embeddings.
        response = embedding(model=self._profile.model, input=list(texts))
        return [item["embedding"] for item in response.data]
