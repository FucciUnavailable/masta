# Writing a coach

A **coach** is the heart of masta — a domain expert with its own voice, knowledge, tools, and
safety rules. Coaches are **data, not code**: you create one by adding a directory, no Python
required.

## Anatomy

```
my-coach/
├── coach.yaml     # required — the manifest
├── persona.md     # required — system prompt / teaching philosophy
└── knowledge/     # optional — reference docs (retrieval, post-MVP)
    └── *.md
```

Drop the directory in any of these locations (later ones override earlier):

1. Bundled: `examples/coaches/` (shipped with the repo)
2. User: `~/.config/masta/coaches/`
3. A pip package exposing a `masta.coaches` entry point

Then check it loads:

```bash
uv run masta coach list
uv run masta chat --coach my-coach
```

## `coach.yaml`

```yaml
# Identity
name: backend-engineering          # unique slug (matches the folder)
display_name: Backend Engineering Sensei
description: Helps you grow as a backend engineer with deliberate practice.
tags: [engineering, career, software]

# Which LLM profile to use by default (see config.toml / `masta providers`).
# Omit to use the global default profile.
model_profile: claude

# Tools this coach is allowed to use. Only declared tools are available.
tools:
  - web_search

# Teaching behavior knobs (optional)
style:
  both_sides: true        # always present pros/cons for recommendations
  socratic: true          # ask before telling
  rest_reminders: true    # nudge breaks/rest during long sessions

# Guardrails — REQUIRED for any health/safety-sensitive domain.
guardrails:
  disclaimers:
    - "I'm a coach, not a substitute for a qualified professional."
  refuse_topics: []                 # topics this coach must not advise on
  escalate_to_professional:         # phrases/intents that trigger a referral
    - "chest pain"
  safe_ranges: {}                   # domain-specific numeric guardrails
```

See [`CoachManifest`](../src/masta/coaches/model.py) for the full schema.

## `persona.md`

Plain Markdown. This becomes the coach's system prompt. Describe:

- **Who the coach is** and the philosophy it teaches from.
- **How it coaches** — deliberate practice, accountability, evidence over hype.
- **Its boundaries** — when to defer to a professional.

The engine automatically appends shared behavior (memory context, both-sides instructions,
guardrails) around your persona, so focus on the domain voice.

## Guardrails & safety

For anything touching health, fitness, finance, or mental wellbeing, treat `guardrails` as
mandatory. The engine enforces disclaimers, can refuse out-of-scope topics, and routes
escalation triggers toward professional help. The shipped
[`weight-loss-safe`](../examples/coaches/weight-loss-safe/) coach is a worked example.
