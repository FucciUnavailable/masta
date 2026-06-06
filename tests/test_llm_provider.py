"""The fake provider satisfies the protocol, and the LiteLLM adapter builds params correctly
without ever calling the network."""

from __future__ import annotations

from masta.config import ModelProfile
from masta.llm.base import LLMProvider, Message
from masta.llm.litellm_provider import LiteLLMProvider


def test_fake_provider_satisfies_protocol(fake_provider):
    assert isinstance(fake_provider, LLMProvider)


def test_litellm_provider_param_building():
    profile = ModelProfile(model="anthropic/claude-sonnet-4-6", temperature=0.3, max_tokens=512)
    provider = LiteLLMProvider(profile)
    assert provider.model == "anthropic/claude-sonnet-4-6"

    params = provider._params({"temperature": 0.9})
    assert params["model"] == "anthropic/claude-sonnet-4-6"
    assert params["max_tokens"] == 512
    assert params["temperature"] == 0.9  # override wins


def test_litellm_payload_serialization():
    profile = ModelProfile(model="ollama/llama3.1", api_base="http://localhost:11434")
    provider = LiteLLMProvider(profile)
    payload = provider._payload([Message(role="user", content="hi")])
    assert payload == [{"role": "user", "content": "hi"}]
    assert provider._params({})["api_base"] == "http://localhost:11434"
