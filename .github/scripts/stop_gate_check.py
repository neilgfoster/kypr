#!/usr/bin/env python3
"""Hedl Stop/SubagentStop hook — gate check before agent signs off.

Runs am_i_done.py when the agent attempts to stop. If the gate is red
the hook returns exit 2, which blocks the stop and feeds the gate output
back to the agent as an error message so it can attempt a fix.

Guards against infinite loops via the stop_hook_active field in the JSON
input: if Claude is already in a stop-hook cycle, the hook returns exit 0
to allow the stop rather than looping forever.

Wiring (in .claude/settings.json hooks array):
  {
    "type": "stop",
    "command": "python3 .claude/scripts/stop_gate_check.py"
  }

The same script works for SubagentStop — add a second hooks entry with
"type": "subagent_stop".

Exit codes (per Claude Code hook contract):
  0 — allow the stop (gate green, or loop guard active)
  2 — block the stop; stderr fed back to the agent as an error message
"""

from __future__ import annotations

import json
import os
import subprocess
import sys


def main() -> int:
    # Read the hook input (JSON on stdin).
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        payload = {}

    # Infinite-loop guard: if stop_hook_active is set, a previous invocation of
    # this hook already blocked the stop. Allow the stop this time to prevent
    # the agent from getting permanently stuck.
    if payload.get("stop_hook_active"):
        return 0

    # CLAUDE_PROJECT_DIR is set by Claude Code and is the most authoritative
    # source for the project root; REPO_ROOT is a legacy operator override.
    # Strip to guard against whitespace-only values that are truthy but invalid.
    repo_root = (
        (os.environ.get("CLAUDE_PROJECT_DIR") or "").strip()
        or (os.environ.get("REPO_ROOT") or "").strip()
        or _find_repo_root()
    )
    # Cross-validate: env-var-derived paths must contain a .git marker.
    if not os.path.exists(os.path.join(repo_root, ".git")):
        repo_root = _find_repo_root()

    gate = os.path.join(repo_root, ".github", "scripts", "am_i_done.py")
    if not os.path.isfile(gate):
        # Gate not found — don't block (adopter may be in gate-only install
        # without the script projected, or running outside a Hedl repo).
        return 0

    result = subprocess.run(
        [sys.executable, gate],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    if result.returncode == 0:
        return 0

    # Gate is red — block the stop and feed back the gate output.
    output = (result.stdout + result.stderr).strip()
    print(output, file=sys.stderr)
    return 2


def _find_repo_root() -> str:
    """Walk up from this script to find the repo root (.git present)."""
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        for _ in range(10):
            # os.path.exists covers both .git directories and worktree .git files.
            if os.path.exists(os.path.join(here, ".git")):
                return here
            parent = os.path.dirname(here)
            if parent == here:
                break
            here = parent
    except OSError:
        pass
    return os.getcwd()


if __name__ == "__main__":
    sys.exit(main())
