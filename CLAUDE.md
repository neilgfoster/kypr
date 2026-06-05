# Kypr — Project Context

## What is Kypr?

Kypr (from "Keeper") is a personal assistant framework delivered as an agent skill.
It gives any AI agent tool a persistent, context-aware personal assistant with
isolated workspaces for personal and professional life. It works within agent
sessions interactively — no background processes, no servers.

## Current phase

**Phase 2: Build** — implement `skill/kypr/` skeleton per requirements and ADR-001.

Active work: see `.work/work.json` backlog (WORK-0006 through WORK-0014).

## Key constraints

- **git-crypt is mandatory.** Verify encryption at every session start. Refuse to
  proceed if not correctly configured. This check is not optional and cannot be bypassed.
- **agent-agnostic core.** `kypr.py` must contain no harness-specific code. Adapters
  live in `adapters/<harness>/` only. Adding a second harness requires no changes
  outside `adapters/`.
- **hedl distribution model.** Kypr follows hedl's structural pattern (copies, single
  tier, `projections.json`, `install.py`). See `docs/adr/ADR-001-distribution-model.md`.
- **No personal data before .gitattributes.** WORK-0013 (.gitattributes) must be
  complete before any personal-data files are committed.

## Structure

```
.work/            — backlog, phases, decisions, reviews
docs/             — requirements, hedl study, ADRs
docs/adr/         — architecture decision records
.github/scripts/  — gate (am_i_done.py) and PR template check
.claude/          — commands, agents, settings
skill/kypr/       — phase 2 build target
```

## Key files

- `.work/work.json` — active and backlog items
- `.work/phases/phase-2.json` — current phase DoD and constraints
- `.work/retrospectives/` — phase retrospectives
- `docs/requirements.md` — project requirements (complete)
- `docs/hedl-study.md` — hedl distribution pattern study (complete)
- `docs/adr/ADR-001-distribution-model.md` — distribution model decision (complete)

## Known open issues

None.
