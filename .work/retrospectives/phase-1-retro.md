# Phase 1 Retrospective — Project Initiation

Date: 2026-06-05
Duration: 2026-06-05 → 2026-06-05

## What we built

- **WORK-0001** — `docs/requirements.md`: six-section requirements document covering what Kypr is,
  security model, distribution, agent compatibility, workspace isolation, and session model
- **WORK-0002** — `docs/hedl-study.md`: thorough study of neilgfoster/hedl covering directory
  structure, projection mechanism, tier model, adapters, install.py behaviours, and open questions
- **WORK-0003** — `docs/adr/ADR-001-distribution-model.md`: architecture decision recording
  copies-always, single-tier, directory-convention adapters, projections.json manifest, and
  git-crypt check in install.py
- **WORK-0004** — `CLAUDE.md` updated: stale placeholders replaced, hedl framing corrected,
  known issues cleared
- **WORK-0005** — Phase 2 backlog (WORK-0006 through WORK-0014): full `skill/kypr/` build
  planned with source references to requirements.md and ADR-001

## Definition of Done — final status

1. **VERIFIED** — `docs/requirements.md` exists covering all six areas; confirmed by file
   presence and content check
2. **VERIFIED** — `docs/hedl-study.md` exists covering structure, install mechanism, projection
   model, constraints, open questions
3. **VERIFIED** — `docs/adr/ADR-001-distribution-model.md` exists, references hedl-study.md,
   decisions are explicit
4. **VERIFIED** — Phase 2 work items exist in `.work/work.json` (WORK-0006 through WORK-0014,
   9 items); each references requirements.md or ADR-001
5. **VERIFIED** — `CLAUDE.md` exists at repo root with current phase and project context
6. **VERIFIED** — `am_i_done.py` passes on feature branch (confirmed on all phase 1 PRs)

## Learning goals — what we learned

Phase 1 had no explicit learning goals defined in phase-1.json (unlike phase 0). Implicit
learning goals based on the phase:

- **Can requirements drive a backlog?** Yes, but with friction: the hedl framing needed two
  corrections, and "git-crypt correctly configured" and "personal data" both needed explicit
  definitions before the phase 2 backlog was fully buildable.
- **Does hedl's pattern apply to Kypr cleanly?** Mostly yes, with three deliberate divergences
  (copies not symlinks, single tier, no adapters.json). Caught and recorded in ADR-001.
- **Is adversarial review useful at phase boundaries?** Yes — the phase completion review caught
  a requirements/ADR contradiction (tiers.json/adapters.json) and two under-defined terms that
  task-level reviews had missed.

## What surprised us

- The hedl characterisation in requirements.md required two rounds of correction: first the
  install-mechanism framing, then the tiers.json/adapters.json contradiction introduced by
  ADR-001 decisions. Requirements documents are not static — they need updating as ADRs narrow
  the design.
- Phase adversarial review was substantially more productive than task-level reviews for catching
  inter-document contradictions. Task reviews look at one output; phase review looks across all
  outputs and finds gaps between them.
- Two terms in WORK-0008 and WORK-0012 ("correctly configured", "personal data") were undefined
  until the phase completion review forced the question. Both needed decisions that should have
  been made earlier.

## What we'd do differently

- Define operational terms in requirements.md before writing work items that depend on them.
- After each ADR is written, do a pass over existing requirements to find contradictions
  introduced by the ADR decisions.
- Run a lighter cross-document consistency check after every major deliverable rather than
  accumulating contradictions until phase-complete.

## Direction changes made during this phase

None in phase 1. (Phase 0 had the direction change that opened phase 1.)

## Phase adversarial review verdict

**CONDITIONAL** — 2 blocking findings and 5 significant findings. All fixed in this commit:

- requirements.md §3 corrected (tiers.json/adapters.json removed)
- "git-crypt correctly configured" defined (requirements.md §2)
- "personal data" defined (requirements.md §5)
- WORK-0010 clarified (kypr.py does not discover adapters)
- WORK-0013 added (.gitattributes work item)
- WORK-0014 added (ReDoS fix)
- requirements-review F1 resolved (load-bearing language accepted in requirements)

## Impact on next phase

- Phase 2 starts with 9 well-specified work items. Dependencies are explicit. No open design
  decisions remain unresolved.
- verify_encryption.py (WORK-0008) now has a precise, testable definition of "correctly
  configured" — the three checks are enumerated.
- workspace-state/ (WORK-0012) now has a precise definition of what requires encryption vs
  what is plaintext metadata.
- The agent-agnostic boundary is explicit: kypr.py does not load adapters; adapters are
  harness-level configuration only.
- ReDoS in check_pr_template.py is tracked (WORK-0014, low priority) and will not be silently
  carried forward again.
