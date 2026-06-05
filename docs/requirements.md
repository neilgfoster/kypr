# Kypr — Requirements

Phase 1 document. Source: operator-provided requirements, 2026-06-05.

---

## 1. What Kypr Is

Kypr (from "Keeper") is a personal assistant framework delivered as an agent skill.
It gives any AI agent tool a persistent, context-aware personal assistant with
isolated workspaces for personal and professional life.

- Delivered as a hedl-compatible skill (installable into any target repo via hedl's
  install mechanism).
- Operates entirely within agent sessions — no background processes, no servers, no
  daemons.
- Maintains persistent state across sessions through files committed in the target
  repo (encrypted where personal data is involved).

## 2. Security Model

**git-crypt is mandatory.** There are no exceptions and no bypass paths.

- Kypr must verify that git-crypt is correctly configured at every session start.
- If encryption is not correctly configured, Kypr must refuse to proceed.
- Personal data must never be persisted unencrypted.
- The encryption check is not optional and cannot be weakened, made conditional, or
  bypassed by any configuration, flag, or operator instruction.

This constraint is load-bearing: it is the only barrier between Kypr's persistent
workspace state and an unencrypted commit. Any design that weakens it is rejected.

## 3. Distribution Model

Kypr follows hedl's distribution model.

- The skill is packaged and installed using hedl's install mechanism
  (`install.py`, `tiers.json`, `adapters.json`, `plugin.json`).
- The full hedl model must be studied before any distribution design decisions are
  made (see WORK-0002 in the backlog).
- Kypr must replicate hedl's projection model (how files land in target repos)
  exactly unless a specific, documented deviation is required and recorded in an ADR.

## 4. Agent Compatibility

Kypr must work with any agent tool.

- The core skill is agent-agnostic. No agent-specific APIs or harness assumptions
  are allowed in `skill/kypr/` outside of `adapters/`.
- Harness-specific wiring is thin and isolated in `adapters/`. Each adapter maps
  Kypr's interface to a specific agent harness (e.g. Claude Code).
- The first supported harness is Claude Code. Others must be addable without
  modifying the core.

## 5. Workspace Isolation

Kypr maintains isolated workspaces for different life contexts.

- At minimum: personal workspace and professional workspace.
- Workspaces are isolated from each other — state, references, and context from one
  workspace must not leak into another.
- The workspace in use at any time is explicit and operator-controlled (not inferred).

## 6. Session Model

Kypr is interactive only.

- No background processes.
- No servers.
- No scheduled tasks or daemons.
- All Kypr activity happens within an active agent session initiated by the operator.
- Session state may be persisted to disk (encrypted) at session end and restored at
  session start, but persistence is passive — nothing runs between sessions.
