# ADR-002: Target Repo Layout

**Date:** 2026-06-05
**Status:** Accepted
**Deciders:** neilgfoster

---

## Context

ADR-001 fixed the projection manifest format (`projections.json`, flat array of
`{source, target}` pairs) but not where projected files land in a target repo.
hedl projects to functional locations (`.github/`, `.claude/`, `.work/`) rather
than mirroring its skill tree. Kypr needs an equivalent convention before
projections.json (WORK-0007), the adapter (WORK-0011), the workspace-state
structure (WORK-0012), and the `.gitattributes` rules (WORK-0013) can name paths.

Options considered:

- **`.kypr/` namespace** — core scripts and workspace state under one hidden
  directory; adapter wiring still goes to harness-owned locations (`.claude/`).
- **Visible root dirs** — `scripts/` and `workspace-state/` at the target root.
  Rejected: clutters the root and risks colliding with an existing `scripts/`.
- **Mirror skill tree** — `kypr/scripts/`, `kypr/workspace-state/`. Rejected:
  hedl itself does not mirror its tree; it projects to functional locations.

## Decision

Kypr projects its agent-agnostic core into a `.kypr/` namespace in the target
repo. Harness adapter files project to the harness's own locations.

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

## Consequences

1. `projections.json` targets use the `.kypr/` prefix for core files and
   `.claude/` for the Claude Code adapter.
2. WORK-0013's `.gitattributes` rules cover `.kypr/workspace-state/**` personal
   data paths (the `active` metadata file stays plaintext per requirements §5).
3. Each work item that adds projectable files (WORK-0011 adapter, WORK-0012
   workspace-state) extends `projections.json` in the same change — the manifest
   always lists exactly the files that exist and must be copied, so `install.py`
   never references a missing source.
4. Adding a second harness adds `adapters/<harness>/` sources projecting to that
   harness's own config locations; `.kypr/` paths are untouched.

## References

- docs/adr/ADR-001-distribution-model.md (manifest format, copies, single tier)
- docs/requirements.md §3 (distribution), §5 (workspace isolation)
- Operator decision 2026-06-05 (structured question, WORK-0007 session)
