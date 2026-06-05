# ADR-001: Distribution Model

**Date:** 2026-06-05
**Status:** Accepted
**Deciders:** neilgfoster

---

## Context

Kypr's requirements state that the skill follows hedl's delivery pattern — hedl being a
reference example for how a skill can be distributed across multiple agent tools. Before
building anything, the pattern was studied (see `docs/hedl-study.md`).

hedl's pattern:
- A skill directory (`skill/<name>/`) is the single source of truth for all skill files
- An installer reads a manifest (`tiers.json`) and projects files into a target repo
- Three tiers with inheritance: gate, lightweight, team
- Default projection on Unix: symlinks pointing back to the skill directory
- Adapter boundary defined by `adapters.json` + `integrations/<harness>/` subdirectories

Three questions were deferred from the study to this ADR:
1. Symlinks or copies as the default projection mode?
2. Single tier or multiple tiers?
3. `adapters.json` manifest or directory-convention adapter boundary?

---

## Decisions

### 1. Projection mode: copies always

**Decision:** Kypr's installer always copies files from `skill/kypr/` into the target
repo. Symlinks are not used.

**Rationale:** Kypr is installed into a single personal repo with one operator. The
primary benefit of symlinks — automatic propagation of updates — is marginal when the
operator controls both the skill source and the target. Copies are simpler to read, avoid
"symlink pointing outside repo" confusion, and are already proven compatible with CI
(hedl's own CI enforced copies for the same reason).

**Divergence from hedl:** hedl defaults to symlinks on Unix. Kypr diverges here. This
is acceptable because Kypr is not a hedl deployment; hedl is a reference pattern, not
a constraint.

### 2. Tier structure: single tier

**Decision:** Kypr has one tier. The installer projects all skill files in a single
operation with no tier selection, upgrade, or downgrade logic.

**Rationale:** hedl's three-tier model exists to serve incremental adoption across teams
with different needs. Kypr is a personal tool for one operator. A single tier eliminates
manifest inheritance, downgrade delta computation, and tier marker state — all complexity
that serves a use case Kypr does not have.

**Divergence from hedl:** hedl has three tiers. Kypr uses one. If Kypr is later shared
or adapted for team use, tiers can be introduced at that point; adding them later is
straightforward, removing premature tier machinery is not.

### 3. Adapter boundary: directory convention, no JSON manifest

**Decision:** Kypr's adapter boundary is defined by directory structure:
`skill/kypr/adapters/<harness>/`. Each harness adapter is a directory containing the
files that wire Kypr's interface into that harness. There is no `adapters.json` manifest.

**Rationale:** hedl's `adapters.json` is a capability matrix that serves multi-harness
documentation and the install logic that selects which integration files to project.
Kypr's MVP targets Claude Code only. A directory convention (`adapters/claude-code/`)
is sufficient to enforce the adapter boundary required by the requirements (agent-agnostic
core, thin wiring isolated in `adapters/`). Adding a JSON manifest when there is one
harness and one operator would be ceremony without function.

**Constraint preserved:** The agent-agnostic core constraint from requirements.md is
enforced by the directory boundary alone. No harness-specific code may appear outside
`skill/kypr/adapters/`. This is a structural rule, not a manifest-enforced one.

---

## Consequences

### What this means for Phase 2 build items

1. **`skill/kypr/install.py`** — copies files from `skill/kypr/` to the target repo.
   No symlink logic. No tier selection. Reads a single manifest file `projections.json`
   (a flat JSON array of `{ "source", "target" }` pairs). Security guardrails (path
   containment checks) from hedl's pattern should be adopted.
   **install.py must verify git-crypt is correctly configured before projecting any
   files.** If git-crypt is not configured, install.py exits non-zero. This is not
   optional and cannot be bypassed (requirements.md §2).

2. **`skill/kypr/adapters/claude-code/`** — first and only adapter directory in phase 2.
   Contains harness wiring files only (e.g. `settings.json`, `startup.sh`, hook scripts).

3. **No `tiers.json`, no `adapters.json`** at the top level of `skill/kypr/` in phase 2.
   The installer manifest is `projections.json` (see §1 above). Adapter discovery is
   by directory presence under `adapters/`, not by a JSON manifest.

4. **`plugin.json`** — retain for metadata (name, version, description). hedl's pattern
   for this is straightforward and adds no complexity.

5. **`.work/` handling** — follows hedl's pattern exactly: init directory, copied once
   on fresh install, never overwritten. (Kypr already has `.work/` in the repo; the
   installer must detect this and skip.)

### What remains aligned with hedl

- Skill lives under `skill/kypr/` — same structure
- `plugin.json` for metadata — same
- `verify_encryption.py` at session start — Kypr-specific addition (hedl has no
  git-crypt awareness); wired from the adapter layer
- `am_i_done.py` gate pattern — already in place from phase 0

### Open questions resolved

| Question | Decision |
|----------|----------|
| Symlinks vs copies | Copies always |
| Single vs multiple tiers | Single tier |
| adapters.json vs directory convention | Directory convention (`adapters/<harness>/`) |
| Installer manifest format | `projections.json` — flat JSON array of source/target pairs |
| git-crypt check in install.py | Yes — install.py exits non-zero if git-crypt not configured |

---

## References

- `docs/hedl-study.md` — hedl distribution pattern study
- `docs/requirements.md` §3 (Distribution Model), §4 (Agent Compatibility)
- hedl study §7 — Observations for ADR-001
