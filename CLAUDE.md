# Kypr — Project Context

## What is Kypr?

Kypr (from "Keeper") is a personal assistant framework delivered as an agent skill.
It gives any AI agent tool a persistent, context-aware personal assistant with
isolated workspaces for personal and professional life. It works within agent
sessions interactively — no background processes, no servers.

## Current phase

**Phase 1: Project Initiation** — requirements, hedl study, scope definition.
No `skill/kypr/` code is written in this phase.

Active work: see `.work/work.json` backlog.

## Key constraints

- **git-crypt is mandatory.** Verify encryption at every session start. Refuse to
  proceed if not correctly configured. This check is not optional and cannot be bypassed.
- **No skill code in phase 1.** All building happens in phase 2+.
- **hedl distribution model.** Study `neilgfoster/hedl` before designing anything.
  See `docs/hedl-study.md` when available.
- **Agent-agnostic core.** Kypr must work with any agent tool. Harness-specific
  wiring is thin and isolated in `adapters/`.

## Structure

```
.work/            — backlog, phases, decisions, reviews
docs/             — requirements, hedl study, ADRs
.github/scripts/  — gate (am_i_done.py) and PR template check
.claude/          — commands, agents, settings
skill/kypr/       — NOT YET CREATED (phase 2)
```

## Key files

- `.work/work.json` — active and backlog items
- `.work/phases/phase-1.json` — current phase DoD and constraints
- `.work/decisions/` — ADRs and phase retrospectives
- `docs/requirements.md` — NOT YET CREATED (WORK-0001)
- `docs/hedl-study.md` — NOT YET CREATED (WORK-0002)

## Known open issues

- **H1** (CONDITIONAL from SEED-0001): `check_checklist()` in
  `.github/scripts/check_pr_template.py` does not handle unchecked items
  accompanied by "(or N/A with reason)". Fix in WORK-0004.
