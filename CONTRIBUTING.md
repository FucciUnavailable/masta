# Contributing to masta

Thanks for helping build an open-source sensei! 🥋

## Dev setup

```bash
uv sync --extra dev
uv run pytest        # tests mock the LLM — no API keys needed
uv run ruff check .
uv run ruff format .
```

## Project layout

See [ARCHITECTURE.md](ARCHITECTURE.md). The short version: keep the layers honest — nothing
outside `masta/llm/` should import a provider SDK or LiteLLM directly; talk to the
`LLMProvider` interface instead.

## The best first contribution: a new coach

Coaches are **data, not code**, so you can add one without touching the engine. See
[docs/writing-a-coach.md](docs/writing-a-coach.md). In short:

1. Create `examples/coaches/<your-coach>/coach.yaml` + `persona.md` (+ optional `knowledge/`).
2. For any health/safety-sensitive domain, fill in the `guardrails` section thoughtfully —
   disclaimers, safe ranges, and "see a professional" triggers are mandatory there.
3. Run `uv run masta coach list` to confirm it loads.

## Guidelines

- Add or update tests for behavior changes (`tests/`, LLM mocked).
- Run `ruff` before pushing.
- Keep PRs focused. Describe the *why*.
- Be excellent to each other — see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Safety note

masta can be used for sensitive domains (health, fitness, mental wellbeing). When in doubt,
err toward caution, cite evidence, present both sides, and defer to qualified professionals.
We will not merge coaches that encourage unsafe behavior.
