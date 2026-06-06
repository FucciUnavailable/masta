# Providers & model profiles

masta is **provider-agnostic**. The rest of the app only talks to the `LLMProvider`
interface; under the hood we use [LiteLLM](https://github.com/BerriAI/litellm), which speaks
to 100+ backends. You choose a backend with a **model string** and group settings into named
**profiles** you can switch between at runtime.

## Configuring credentials

Put API keys in `.env` (copy from `.env.example`). LiteLLM reads the standard env vars:

| Provider | Env var(s) | Example model string |
| --- | --- | --- |
| Anthropic (Claude) | `ANTHROPIC_API_KEY` | `anthropic/claude-sonnet-4-6` |
| OpenAI | `OPENAI_API_KEY` | `openai/gpt-4o` |
| Azure / AI Foundry | `AZURE_API_KEY`, `AZURE_API_BASE`, `AZURE_API_VERSION` | `azure/<deployment>` |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek/deepseek-chat` |
| Local (Ollama) | none (`OLLAMA_API_BASE`) | `ollama/llama3.1` |

## Profiles

Profiles live in `~/.config/masta/config.toml` (auto-created with sensible defaults). Each
profile names a model and optional parameters:

```toml
default_profile = "claude"

[profiles.claude]
model = "anthropic/claude-sonnet-4-6"
temperature = 0.7

[profiles.local]
model = "ollama/llama3.1"
api_base = "http://localhost:11434"

[profiles.deepseek]
model = "deepseek/deepseek-chat"
```

## Switching providers

- **Globally:** set `default_profile`, or `MASTA_DEFAULT_PROFILE` in the environment.
- **Per coach:** set `model_profile:` in the coach's `coach.yaml`.
- **Mid-session:** type `/model <profile>` in the chat REPL to swap on the fly — the
  conversation continues seamlessly because history is provider-independent.

Inspect what's wired up:

```bash
uv run masta providers
```
