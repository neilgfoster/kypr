# Phase 0 Retrospective — Seed

Date: 2026-06-05
Duration: 2026-06-05 → 2026-06-05

## What we built

- **SEED-0001**: Repo-specific PR template check — added `check_checklist()` to
  `.github/scripts/check_pr_template.py`, completing validation of all six sections
  in `.github/PULL_REQUEST_TEMPLATE.md`. The `am_i_done.py` template gate now runs
  on all PRs rather than skipping.

## Definition of Done — final status

| Criterion | Status | Notes |
|-----------|--------|-------|
| skill/kypr/ exists with all required files | UNVERIFIED | Never started |
| skill/kypr/scripts/verify_encryption.py works | UNVERIFIED | Never started |
| skill/kypr/scripts/install.py --tier standard works | UNVERIFIED | Never started |
| skill/kypr/scripts/kypr.py --status works | UNVERIFIED | Never started |
| CLAUDE.md and README.md present and accurate | UNVERIFIED | Neither file exists |
| am_i_done.py passes | UNVERIFIED | Blocked by above |

Phase 0 DoD was **not met**. The phase is being closed by operator direction change,
not by DoD completion. The skill/kypr/ skeleton — the primary phase 0 deliverable —
was never started.

## Direction change

**Operator direction (2026-06-05):** Close phase 0 (Seeding) and start phase 1
(Project Initiation). Phase 1 is scope-setting only — no building.

**Rationale:** Phase 0's DoD was written assuming the skill skeleton would be the
first output. In practice, the first useful work was gate and process infrastructure
(hedl install, PR template check). The original DoD belonged to a building phase,
not a seed phase. Rather than backfill the missing work under a misaligned goal,
the operator chose to reframe: phase 1 will establish requirements, study hedl, and
define the build scope before any skill code is written.

## Learning goals — what we learned

- **hedl's symlink distribution model**: Not validated. CI compatibility fix
  (symlinks → copies) was already present in the repo at start, indicating symlinks
  are a known problem. Phase 1 hedl study will document this properly.
- **Agent-agnostic skill design**: Not validated. No adapters were designed.
  Phase 1 will define the requirement; phase 2 will prove it.

## What surprised us

- The phase 0 DoD was entirely building work with no requirements phase before it.
  A requirements/study phase is more appropriate as the first deliverable.
- The only phase 0 backlog item (SEED-0001) was gate infrastructure, not skill
  skeleton work. The skill skeleton had no work items at all.
- The adversarial phase review panel unanimously found 5 blocking DoD failures
  before any DoD checks were run — the gap was obvious.

## What we'd do differently

- Write a requirements document before defining DoD criteria.
- Do not merge gate infrastructure under a "Seed" phase that expects a product
  deliverable. Gate infrastructure is phase 0 work; product skeleton is phase 1+.

## Adversarial phase review verdict

**FAIL** — 5 blocking findings, unanimous across scope-auditor, historian,
existential-challenger, evidence-checker, assumption-challenger. Phase closed by
operator direction change rather than DoD completion. Findings recorded, not fixed.

## Impact on next phase

- Phase 1 must produce `docs/requirements.md` grounded in the operator-provided
  requirements before any design decisions are made.
- Phase 1 must produce `docs/hedl-study.md` before ADR-001 can be written.
- H1 (CONDITIONAL from SEED-0001): `check_checklist()` does not handle
  "(or N/A with reason)" — carry forward, fix in first PR of phase 1.
- No version bump was made for phase 0.
