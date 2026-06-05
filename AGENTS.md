# OpenAI Codex CLI — Hedl workflow

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

Check `.work/work.json` → `meta.active_item`. Read its `acceptance_criteria`
before implementing anything. Do not start a new item until the active one
is committed and its PR is open.

## Adversarial review before PR

Codex has no native multi-agent orchestration. Run the review panel manually:

**Step 1 — select the panel.** Ask yourself acting as review-dispatcher:
"Given this diff, which agents should review? Choose from: scope-auditor,
edge-case-hunter, security-auditor, determinism-auditor, historian,
simplicity-enforcer, existential-challenger."

**Step 2 — run each agent in sequence.** For each selected agent, apply
the corresponding prompt from `skill/hedl/references/review-library.md`.
Each agent outputs findings as BLOCKING / SIGNIFICANT / MINOR.

**Step 3 — synthesise.** If any BLOCKING findings exist, fix them before
raising a PR. SIGNIFICANT findings may proceed but should be noted.

## Drive to PR

```sh
gh pr create --title "TYPE: description" --body "..."
python3 .github/scripts/am_i_done.py --pr <PR_NUMBER>
```

---

Hedl's core — the gate, `.work/` state, `hedl.toml` — is tool-agnostic.
Running Hedl's review steps with Codex's model alongside other tools is
deliberate: **model diversity across harnesses catches failure modes a
single model family misses** (ADR-038).
