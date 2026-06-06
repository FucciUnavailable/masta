# Architecture

`masta` is layered so each concern is swappable and independently testable. The golden rule:
**the rest of the app never talks to a provider SDK directly** — only to our own interfaces.

```
            CLI / TUI  (Typer + Rich)
                  │
        Orchestrator / agent loop          (agent.py)
        prompt → reason → tool calls → memory write
                  │
 ┌────────┬───────┴────────┬──────────────┬───────────────────┐
 Coach     Reasoning        Memory          Tools               Scheduler/Notifier
 engine    modules          (SQLite)        (search, notify)    (check-ins, rest)
 │         │                │
 │         │                └─ repository over SQLModel
 │         └─ both_sides, planner, evidence*, recovery*, rest*
 └─ declarative coach manifests + guardrails
                  │
        LLM provider layer        (llm/)
        LLMProvider protocol → LiteLLM → any backend
```
\* scaffolded as stubs in the MVP.

## Layers

### LLM provider layer (`masta/llm/`)
- `base.py` — `LLMProvider` Protocol: `complete()`, `stream()`, `embed()`, plus the small
  `Message` / `CompletionResult` data types. **This is the only LLM contract the app sees.**
- `litellm_provider.py` — the single implementation, delegating to LiteLLM. Backends are
  selected purely by model string: `anthropic/claude-...`, `openai/gpt-...`, `azure/...`,
  `deepseek/...`, `ollama/llama3...`.
- `profiles.py` — named, swappable model profiles (e.g. `claude`, `local`) so you can switch
  provider mid-session. The thin wrapper means LiteLLM could be replaced without touching
  callers.

### Coach engine (`masta/coaches/`)
A coach is **data, not code**:
```
examples/coaches/<name>/
├── coach.yaml     # CoachManifest: metadata, model profile, allowed tools, guardrails
├── persona.md     # the system prompt / teaching philosophy
└── knowledge/     # optional reference docs (used by retrieval, post-MVP)
```
- `model.py` — `CoachManifest`, `Coach`, `Guardrails` (pydantic).
- `loader.py` — discovers coaches from the bundled `examples/coaches/`, the user dir
  (`~/.config/masta/coaches/`), and Python entry points (`masta.coaches`) so coaches can ship
  as pip packages.
- `registry.py` — list/select the active coach.

### Memory (`masta/memory/`)
The thing that makes this a *system* and not a chatbot.
- `models.py` — `UserProfile`, `Goal`, `Milestone`, `CheckIn`, `Message`, `Reflection`.
- `db.py` — SQLite engine/session via SQLModel; DB lives under the data dir.
- `repository.py` — typed CRUD/query layer used by the CLI and agent.
- `semantic.py` — stub for embedding-based recall (post-MVP).

### Reasoning (`masta/reasoning/`)
- `both_sides.py` — structured steelman of pros & cons for any recommendation.
- `planner.py` — decompose a goal into milestones/tasks.
- `evidence.py`*, `recovery.py`*, `rest.py`* — evidence search + citations, failure handling /
  motivation, and break/rest heuristics.

### Tools (`masta/tools/`)
- `base.py` — `Tool` interface + a registry. Coaches declare which tools they may use.
- `web_search.py`*, `notify.py`* — evidence search and desktop notifications.

### Scheduler / notifier (`masta/scheduler/`)
- `service.py`* — APScheduler-based check-ins and break/rest reminders.

### Orchestrator (`masta/agent.py`)
The turn loop: builds the prompt from the coach persona + memory context, calls the LLM,
executes any requested tools, applies guardrails and both-sides reasoning, and persists the
exchange to memory.

### CLI (`masta/cli/`)
- `app.py` — Typer entrypoint and commands.
- `repl.py` — the Rich interactive chat loop.

## Extension points
- **New provider** → already covered by LiteLLM model strings; add a profile in config.
- **New coach** → drop a folder in `~/.config/masta/coaches/` or ship a package exposing a
  `masta.coaches` entry point.
- **New tool** → implement `Tool` and register it; reference it from a coach's `coach.yaml`.
- **New reasoning module** → add to `reasoning/` and wire into `agent.py`.

\* = stub in the current MVP.
