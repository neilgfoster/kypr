# Hedl Distribution Model Study

Phase 1 document. Source: neilgfoster/hedl repository, studied 2026-06-05.
Informs ADR-001 (distribution model decision).

---

## 1. What Hedl Is

Hedl is a skill that ships a disciplined development workflow (gate, commands, agents,
hooks) into any target repository. It is a reference example for how a skill can be
delivered across multiple agent tools — not a framework or library that Kypr would
depend on or call into.

The unit of distribution is the **skill directory**: `skill/hedl/`. Everything hedl
ships lives under that subtree. The installer (`install.py`) reads a manifest
(`tiers.json`) and projects files from `skill/hedl/` into the target repo.

---

## 2. Directory Structure

```
skill/hedl/
├── plugin.json           — metadata (name, version, description)
├── tiers.json            — canonical projection manifest
├── adapters.json         — per-harness capability matrix
├── SKILL.md              — natural-language routing table (non-Claude-Code harnesses)
├── scripts/
│   ├── install.py        — installer (~1370 lines)
│   ├── am_i_done.py      — deterministic completion gate
│   ├── check_pr_template.py
│   ├── check_markdown_schema.py
│   ├── release.py, reflect.py, contribute.py, hedl.py
├── commands/             — 5 Claude Code slash command files
├── agents/               — 8 adversarial reviewer agent files
├── integrations/
│   ├── claude-code/      — hooks, scripts/, settings.json, startup.sh, claudeignore
│   ├── copilot/          — copilot-instructions.md + path-scoped instructions
│   ├── cursor/           — .mdc rule files
│   ├── opencode/         — AGENTS.md + command files
│   └── codex/            — AGENTS.md
├── templates/            — epic, PRD, task templates
├── references/           — internal documentation
├── workflows/            — GitHub Actions templates
└── work-state/           — template state files (.work/ seed content)
```

After install, files land in the target repo at paths defined by `tiers.json`. Example:

```
target-repo/
├── .github/scripts/am_i_done.py     ← projected (symlink or copy)
├── .github/workflows/am-i-done.yml  ← projected (forced copy; GitHub parses directly)
├── .claude/commands/*.md            ← projected (lightweight tier+)
├── .claude/agents/*.md              ← projected (lightweight tier+)
├── .claude/settings.json            ← projected (team tier only)
├── .work/                           ← init dir (copied once on fresh install)
└── docs/spec/*.md                   ← projected (lightweight tier+)
```

---

## 3. Projection Mechanism

`install.py` is the only tool that modifies projections. It reads `tiers.json` and
either creates symlinks (default on Unix) or copies files (Windows, or `--copy` flag).

### 3.1 tiers.json

Single source of truth for all projections. Three tiers with inheritance:

| Tier | Includes | Setup | Purpose |
|------|----------|-------|---------|
| `gate` | (base) | ~2 min | Gate + CI only; no state, no commands |
| `lightweight` | gate | ~5 min | Full workflow; commands, agents, .work/ |
| `team` | lightweight | ~5 min | Adds Claude Code hooks (settings.json, startup.sh, hook scripts) |

Tier inheritance is resolved by `install.py` at install time: it flattens the
`includes` chain (with cycle detection, max depth 32) and deduplicates projections.
The resolved list, not the raw tier entry, is what gets applied.

Each tier entry specifies:
- `projections`: `{ source, target, on_exists }` — file mappings; `on_exists: overwrite` or `skip`
- `init`: `{ source, target, on_exists: skip }` — directories copied once, never overwritten (e.g. `.work/`)

### 3.2 Symlinks vs copies

- **Default (Unix):** symlinks using `os.path.relpath()` so the link target is
  relative to the link location — the symlink survives repo moves and CI checkouts
- **Windows:** auto-copy (symlinks not portable)
- **`--copy` flag:** force copies everywhere
- **GitHub-parsed files:** always forced to real copies regardless of mode:
  - `.github/workflows/*.yml`
  - `.github/instructions/*`
  - `.github/PULL_REQUEST_TEMPLATE.md`
  - `.github/copilot-instructions.md`
  - `.github/dependabot.yml`
  - `.github/CODEOWNERS`

This distinction is load-bearing: symlinks allow updates to flow automatically when
the skill is upgraded; copies require a re-run of install.py.

### 3.3 Idempotency

`install.py` is idempotent. Running it again on an already-installed repo:
- Repairs broken/missing symlinks
- Respects `on_exists: skip` for init dirs
- Re-applies projections for the current tier

### 3.4 Tier upgrades and downgrades

- **Upgrade:** adds new projections and inits
- **Downgrade:** removes projections for tiers above the target; archives init dirs
  with a timestamp suffix (never deletes)

---

## 4. adapters.json

Declares what each supported harness can natively do and how hedl wires into it.

Supported harnesses: Claude Code, Copilot, Cursor, OpenCode, Codex.

Per-harness entry:
```json
{
  "description": "...",
  "native_capabilities": {
    "multi_agent": bool,
    "hooks": bool,
    "commands": bool,
    "nl_routing": bool
  },
  "instructions": { ... },
  "delegation": { ... }
}
```

Key capability summary:

| Harness | Multi-agent | Hooks | Commands | NL routing |
|---------|-------------|-------|----------|------------|
| Claude Code | yes | yes | yes | yes |
| Copilot | yes | yes | yes | yes |
| Cursor | yes | yes | no | no |
| OpenCode | yes (5 built-in) | no | yes | no |
| Codex | no | no | no | no |

Kypr's initial target is Claude Code. adapters.json establishes the pattern for
adding further harnesses without modifying the core.

---

## 5. Install.py Key Behaviours

- **Path containment checks:** projections whose source or target escapes the skill
  root are rejected (security guardrail)
- **Cycle detection:** tier inheritance loops are caught with a max depth of 32
- **Invisible mode:** adds a hedl-managed block to `.git/info/exclude` so skill
  artifacts are git-ignored on shared repos where committing them is not appropriate
- **`.gitignore` management:** appends a delimited block guarding local-only insight
  files (`.work/insights/`)
- **Seed work items:** on fresh install only, injects SEED- items into `.work/work.json`
- **`.hedl-tier` marker:** JSON file recording installed tier; git-ignored, regenerated
  on every install

---

## 6. State Management

`.work/` is an init directory — copied once on first install, never overwritten.
All subsequent writes are by the operator (via slash commands).

`context.json` carries a `schema_version` field. `install.py` runs migrations when
the installed version is behind the current schema. Migration ordering is crash-safe:
hedl.toml is updated before context.json schema version is bumped.

---

## 7. Constraints and Open Questions for Kypr

### Constraints Kypr must respect if following hedl's pattern

1. `install.py` (or Kypr's equivalent) is the only tool that creates or modifies
   projections. Manual symlink or file edits break installer state.
2. `tiers.json` is the single source of truth for what gets projected and where.
3. GitHub-parsed files (workflows, PR template) must be real copies, not symlinks.
4. Init dirs (like `.work/`) are copied once and never overwritten by the installer.
5. `.hedl-tier` (or Kypr's equivalent marker) is ephemeral and git-ignored.

### Observations for ADR-001

These are observations about hedl's design choices that ADR-001 will need to evaluate
for Kypr. They are not decisions.

- Kypr is its own skill, not a hedl deployment. Its manifest (if it follows the
  tiers.json pattern) would list `skill/kypr/` files, not hedl's.
- Hedl's three-tier model serves adoption flexibility across teams with different
  needs. Kypr's initial audience and use case may warrant fewer tiers.
- hedl's `install.py` handles multi-harness projection, invisible mode, migrations,
  and security guardrails accumulated over many iterations. A Kypr-equivalent
  installer could be scoped more narrowly in phase 2.
- Invisible mode (`.git/info/exclude`) is designed for shared team repos where
  committing skill artifacts is not appropriate. Kypr is a personal tool in its own
  repo; this feature may not apply.

### Open questions

1. **Symlinks vs copies as default:** hedl defaults to symlinks on Unix. For a
   personal tool committed to a single repo, copies may be simpler and avoid
   "symlink points outside repo" confusion for casual readers. Decision needed in
   ADR-001.
2. **Single tier or multiple:** hedl's three tiers serve adoption flexibility across
   teams. Kypr's initial audience is one operator. A single tier with all files
   projected is simpler. Decision needed in ADR-001.
3. **Harness adapter scope:** hedl supports five harnesses. Kypr's requirement is
   "agent-agnostic core, thin wiring in adapters/". MVP is Claude Code only. The
   adapter boundary must be defined before writing the core so it does not leak.
4. **`.work/` as init vs tracked state:** hedl seeds `.work/` once and then it is
   operator-owned. Kypr uses the same pattern (`.work/` is already in the repo).
   The installer should not touch `.work/` on re-install.
5. **Encryption integration:** hedl has no git-crypt awareness. Kypr's installer
   must verify git-crypt configuration before projecting any encrypted files. This
   is a Kypr-specific addition to the pattern, not something hedl models.
