# OpenCode — Hedl workflow

This repo uses **Hedl**: a deterministic completion gate, adversarial review,
and phase-based work tracking. You are the coding agent; follow Hedl's discipline.

## The gate decides "done" — not you

Before declaring any task complete, run:

```sh
python3 .github/scripts/am_i_done.py
```

For PR checks: `python3 .github/scripts/am_i_done.py --pr <PR_NUMBER>`

Gate exits `0` = done. Fix what it reports; never claim done on a red gate.

## One item at a time

Check `.work/work.json` → `meta.active_item` for what is being worked on.
Read its `acceptance_criteria` before implementing anything.

## Adversarial review

Before raising a PR, convene the review panel. OpenCode's built-in agents
(General, Explore, Scout) can be used as independent reviewers. See
`skill/hedl/references/review-library.md` for agent prompts.

Use OpenCode commands (available via `/`):
- `/hedl-start` — orient and load the active work item
- `/hedl-iterate` — run the full work loop
- `/hedl-review` — convene adversarial review panel
- `/hedl-pr` — drive branch to an operator-ready PR

---

Hedl's core — the gate, `.work/` state, `hedl.toml` — is tool-agnostic.
This file routes OpenCode to the gate and workflow. Running Hedl reviews
with OpenCode's models alongside Claude Code and Copilot is deliberate:
**model diversity across harnesses catches failure modes a single model misses.**
