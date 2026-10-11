# masta 🥋

> An AI **sensei** for your goals — not a chatbot that spits out a plan in a table.

`masta` is an open-source, **AI-provider-agnostic** coaching system. It helps you turn a
goal into a real plan, tracks your progress over time, searches actual evidence, argues
**both sides** of every suggestion, keeps you motivated when you fail — and reminds you to
**rest**. Coaching, not just prompting.

It is built around pluggable **coaches** — domain experts (e.g. *backend engineering*,
*safe weight loss*) that each carry their own persona, knowledge, tools, and safety
guardrails.

## Why it's different

This is a **system**, not a prompt:

- 🔌 **Provider-agnostic** — Claude, OpenAI, Azure/AI Foundry, DeepSeek, or a **local model**
  (Ollama). Switch with config, not code. Powered by [LiteLLM](https://github.com/BerriAI/litellm)
  behind a thin adapter so we're never locked in.
- 🧠 **Persistent memory** — your goals, milestones, check-ins, and reflections live in a
  local SQLite database, so the sensei has continuity and can actually track you.
- 🧩 **Pluggable coaches** — a coach is *data*, not code: a folder with a persona, knowledge,
  declared tools, and guardrails. Ship your own.
- ⚖️ **Both-sides reasoning** — every recommendation comes with a steelmanned pro/con view,
  as a first-class step rather than an afterthought.
- 🛟 **Safety guardrails** — sensitive coaches (health, weight loss) enforce disclaimers,
  safe ranges, and "talk to a professional" triggers.
- 😴 **Rest matters** — break/rest reminders and check-ins are part of the design, not bolted on.

## Status

Early alpha. **MVP scope:** the coach engine + persistent memory + both-sides reasoning,
driven from a terminal chat, with provider swapping. Evidence search, scheduling/notifications,
failure-recovery, and rest enforcement are scaffolded and arriving next (see
[ARCHITECTURE.md](ARCHITECTURE.md)).

## Quickstart

```bash
# 1. Install (uv recommended)
uv sync

# 2. Configure at least one provider
cp .env.example .env
$EDITOR .env

# 3. See what's wired up
uv run masta providers

# 4. Talk to a coach
uv run masta coach list
uv run masta chat --coach backend-engineering
```

## CLI overview

| Command | What it does |
| --- | --- |
| `masta chat --coach <name>` | Start an interactive coaching session |
| `masta coach list` / `masta coach use <name>` | List / select coaches |
| `masta goals` | View and manage tracked goals |
| `masta checkin` | Log progress / how you're doing |
| `masta serve` | Run the HTTP API (and built web UI) for the frontend |
| `masta providers` | List configured LLM providers & profiles |
| `masta config` | Show resolved configuration |

## Web UI (early)

A React frontend lives in [`web/`](web/), backed by an HTTP API over the same engine and
memory as the CLI. Today it is an app shell: it lists coaches, goals, and check-ins; chat in
the browser is next.

```bash
uv sync --extra web          # FastAPI + uvicorn
uv run masta serve           # API on http://127.0.0.1:8000

cd web && pnpm install
pnpm dev                     # UI on http://localhost:5173, proxying /api to the API
```

For a single-process setup, run `pnpm build` and `masta serve` will host the built UI too.

## Writing your own coach

A coach is a directory with a `coach.yaml`, a `persona.md`, and optional `knowledge/`.
See [docs/writing-a-coach.md](docs/writing-a-coach.md) and the examples in
[`examples/coaches/`](examples/coaches/).

## Contributing

PRs welcome — especially new coaches. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
