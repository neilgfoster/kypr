# ADR-002: Target Repo Layout

**Date:** 2026-06-05
**Status:** Accepted
**Deciders:** neilgfoster

---

## Context

ADR-001 fixed the projection manifest format (`projections.json`, flat array of
`{source, target}` pairs) but not where projected files land in a target repo.
hedl projects to functional, tool-recognized locations — `.github/scripts/` for
CI tooling, `.claude/` for harness config, `.work/` for state (hedl-study.md §2)
— it does not create a private namespace directory for its core.

Kypr's core is different in kind: `kypr.py` and `verify_encryption.py` are
harness-neutral session tooling. None of hedl's functional locations fit:

- `.github/scripts/` is CI-functional; Kypr's core scripts are not CI tooling
  and do not run in workflows.
- `.claude/` is harness-owned; placing agent-agnostic core there would violate
  the adapter boundary (requirements §4 — no harness assumptions outside
  `adapters/`).
- A visible root `scripts/` collides with target repos' own `scripts/`
  directories (Kypr installs into arbitrary personal repos it does not control).

There is no existing functional location for harness-neutral core, so a new
namespace is required. Options considered:

- **`.kypr/` namespace** — core scripts and workspace state under one hidden
  directory; adapter wiring still goes to harness-owned locations (`.claude/`).
  Chosen.
- **Visible root dirs** — `scripts/` and `workspace-state/` at the target root.
  Rejected: concrete collision risk with an existing `scripts/` in the target
  repo; no namespacing of Kypr-owned state.
- **Mirror skill tree** — `kypr/scripts/`, `kypr/workspace-state/`. Rejected:
  same collision class as visible dirs (a visible `kypr/` at root), and hedl
  itself projects to functional locations rather than mirroring its tree.

## Decision

Kypr projects its agent-agnostic core into a `.kypr/` namespace in the target
repo. Harness adapter files project to the harness's own locations.

**This is a documented deviation from hedl's projection model** (requirements
§3: replicate exactly "unless a specific, documented deviation is required and
recorded in an ADR"). It is required because no hedl functional location fits
harness-neutral core (see Context); the specific choice of `.kypr/` over the
alternatives was made by operator decision on 2026-06-05.

```text
target-repo/
├── .kypr/
│   ├── scripts/
│   │   ├── kypr.py
│   │   └── verify_encryption.py
│   └── workspace-state/
│       ├── active            (plaintext metadata — workspace name)
│       ├── personal/         (git-crypt encrypted)
│       └── professional/     (git-crypt encrypted)
├── .claude/
│   ├── settings.json         (adapter, WORK-0011)
│   └── startup.sh            (adapter, WORK-0011)
└── .work/                    (skipped if already present — ADR-001 §5)
```

### Manifest semantics

`projections.json` entries are **plain file copies, overwritten on every
install** (idempotent). The schema stays the flat `{source, target}` array from
ADR-001 — no `on_exists` or type field.

- `source` resolves relative to `skill/kypr/`. `target` resolves relative to
  the target repo root. After resolution, a source must remain inside
  `skill/kypr/` and a target inside the target repo root (containment,
  WORK-0009); entries containing `..` segments are rejected.
- Entries name files only, never directories.
- **Copy-once state is out-of-band by design**, not manifest-driven. Named
  exceptions, both implemented as explicit `install.py` steps (WORK-0009):
  1. `.work/` — skipped entirely if present (ADR-001 §5).
  2. `.kypr/workspace-state/` skeleton — created if absent, never overwritten
     (operator data lives there; structure defined in WORK-0012).
  The manifest is the complete list of *copied files*; it is not the complete
  list of installer actions.

### Encryption gate path is a stable contract

Every adapter invokes the core by hardcoding `.kypr/scripts/` paths (e.g. the
Claude Code SessionStart hook calls `.kypr/scripts/verify_encryption.py`).
That path is load-bearing: it is the mandatory git-crypt gate (requirements
§2). `.kypr/scripts/kypr.py` and `.kypr/scripts/verify_encryption.py` are
therefore **fixed public paths** — renaming or moving them is a breaking
change requiring a superseding ADR and a coordinated update of every adapter.

## Consequences

1. `projections.json` targets use the `.kypr/` prefix for core files and
   `.claude/` for the Claude Code adapter.
2. WORK-0013's `.gitattributes` rules name the encrypted subdirectories
   explicitly (`.kypr/workspace-state/personal/**`,
   `.kypr/workspace-state/professional/**` — one rule per encrypted workspace
   dir). No broad `workspace-state/**` rule with plaintext carve-outs: the
   plaintext `active` file must never depend on a negation pattern to stay
   out of the filter. `active` contains a single workspace identifier token
   and nothing else (no timestamps, no derived data) — anything beyond the
   identifier is personal data per requirements §5 and belongs in an
   encrypted workspace dir.
3. Each work item that adds projectable files (WORK-0011 adapter) extends
   `projections.json` in the same change — the manifest always lists exactly
   the files that exist and must be copied, so `install.py` never references
   a missing source. Consequence: an install run after WORK-0009 but before
   WORK-0011/WORK-0012 is mechanically correct yet not end-to-end functional
   (no adapter wiring, no workspace skeleton). Full-install verification
   belongs to the last structural item, not to WORK-0009's gate.
4. Adding a second harness adds `adapters/<harness>/` sources projecting to
   that harness's own config locations; `.kypr/` paths are untouched, and the
   new adapter wires the same fixed `.kypr/scripts/` entry points.

## References

- docs/adr/ADR-001-distribution-model.md (manifest format, copies, single tier)
- docs/hedl-study.md §2 (hedl's functional-location projection model — the
  pattern this ADR deviates from)
- docs/requirements.md §2 (encryption gate), §3 (distribution; deviation
  clause), §4 (adapter boundary), §5 (workspace isolation, personal data)
- Operator decision 2026-06-05 (structured question, WORK-0007 session)
