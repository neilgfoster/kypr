# GitHub Copilot — Hedl workflow

This repo uses **Hedl**: a deterministic completion gate, adversarial review,
and phase-based work tracking. You are the coding agent; follow Hedl's discipline.

Detailed instructions are in the path-scoped files that Copilot loads automatically:

- `.github/instructions/hedl-gate.instructions.md` — when and how to run the gate
- `.github/instructions/hedl-panel.instructions.md` — adversarial review using
  Copilot's native multi-agent orchestration (Mission Control)
- `.github/instructions/hedl-session.instructions.md` — one item at a time,
  surgical changes, orient before acting

## Recommended hook configuration

Configure these Copilot Agent hooks to enforce Hedl's discipline automatically.
Hook configuration lives in your Copilot workspace settings or
`.github/copilot/config.json` per your organisation's setup.

| Hook | Command | Purpose |
|---|---|---|
| `agentStop` | `python3 .github/scripts/stop_gate_check.py` | Gate check before agent signs off — blocks on red gate, feeds back error |
| `subagentStop` | `python3 .github/scripts/stop_gate_check.py` | Same gate check for subagent completions |
| `sessionStart` | Read `.work/work.json` active item | Orient at session start |
| `postToolUse` (file edits) | `ruff check --fix <file>` | Keep lint clean after edits |

`stop_gate_check.py` is the same gate-check script used by Claude Code's Stop hook —
it runs `am_i_done.py`, returns exit 2 to block sign-off on red, and guards against
infinite loops via the `stop_hook_active` field.

---

Hedl's core — gate, `.work/` state, `hedl.toml` — is tool-agnostic.
This adapter adds no logic; it routes Copilot to the gate and the workflow.
Running Hedl's review panel with Copilot's model alongside other tools is
deliberate: **model diversity across harnesses catches failure modes a single
model family misses** (ADR-038).
