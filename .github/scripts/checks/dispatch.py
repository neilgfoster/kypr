from __future__ import annotations

import json
import os
import re
from typing import Optional

import checks._util as _u
from checks._util import CheckResult

_DISPATCH_RULES_FILE = os.path.join(_u.REPO_ROOT, ".work", "config", "dispatch-rules.json")


def _load_dispatch_rules() -> tuple[list[tuple[str, list[str]]], list[str]]:
    """Load (mandatory_agents, always_required) from dispatch-rules.json.

    Raises FileNotFoundError or json.JSONDecodeError on failure.
    """
    with open(_DISPATCH_RULES_FILE, encoding="utf-8") as fh:
        data = json.load(fh)
    mandatory = [(r["pattern"], r["agents"]) for r in data.get("mandatory_agents", [])]
    always: list[str] = data.get("always_required", [])
    return mandatory, always


def _get_changed_files() -> tuple[list[str], Optional[str]]:
    """Return (changed_files, error_message).

    error_message is non-None when neither `main` nor `origin/main` exists
    locally — without that, the dispatch floor cannot be enforced and must
    surface as a hard failure (fresh-clone case where _required_agents would
    otherwise silently return [] and skip security-auditor).
    """
    for ref in ("main", "origin/main"):
        code, out, _ = _u.run(["git", "diff", f"{ref}...HEAD", "--name-only"])
        if code == 0:
            return [f.strip() for f in out.splitlines() if f.strip()], None
    return [], (
        "cannot determine changed files — neither `main` nor `origin/main` "
        "exists locally. Run `git fetch origin main:main` and retry."
    )


def _required_agents() -> tuple[dict[str, list[str]], Optional[str]]:
    """Return ({agent: [reasons]}, error_message) for the current diff."""
    files, err = _get_changed_files()
    try:
        mandatory_agents, always_required = _load_dispatch_rules()
    except FileNotFoundError:
        return {}, (
            f"dispatch-rules.json not found at {_DISPATCH_RULES_FILE} — "
            "run `git pull` or recreate .work/config/dispatch-rules.json"
        )
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        return {}, f"dispatch-rules.json malformed: {exc}"
    required: dict[str, list[str]] = {a: ["always required"] for a in always_required}
    for filepath in files:
        for pattern, agents in mandatory_agents:
            try:
                match = re.search(pattern, filepath)
            except re.error as exc:
                return {}, f"dispatch-rules.json contains invalid regex '{pattern}': {exc}"
            if match:
                for agent in agents:
                    required.setdefault(agent, []).append(filepath)
    return required, err


def check_dispatch(panel: list[str]) -> CheckResult:
    required, err = _required_agents()
    if err is not None:
        return CheckResult("dispatch", False, "cannot enforce dispatch floor", err)

    if not panel:
        agent_list = ", ".join(sorted(required))
        detail = "\n".join(
            f"  {a}: {', '.join(files[:2])}"
            for a, files in sorted(required.items())
        )
        return CheckResult(
            "dispatch",
            True,
            f"minimum panel — {len(required)} agent(s): {agent_list}",
            detail,
        )

    missing = {a: f for a, f in required.items() if a not in panel}
    if missing:
        lines = []
        for agent, files in sorted(missing.items()):
            reason = files[0] if files[0] == "always required" else ", ".join(files[:2])
            lines.append(f"  {agent}  (required by: {reason})")
        return CheckResult(
            "dispatch",
            False,
            f"{len(missing)} mandatory agent(s) missing from panel",
            "\n".join(lines),
        )

    return CheckResult(
        "dispatch",
        True,
        f"panel covers all {len(required)} mandatory agent(s)",
    )


# ---------------------------------------------------------------------------
# State backend abstraction
# ---------------------------------------------------------------------------
# The gate reads work items from whichever backend hedl.toml specifies (ADR-022).
# Default is "local-file" (.work/work.json). Set [state] backend = "github-issues"
# in hedl.toml to read from open GitHub Issues instead. install.py migrates any
# legacy .work/context.json "state_backend" value into hedl.toml.
# The GitHub Issues backend expects issues with titles like "WORK-NNNN: ..."
# and treats open issues as live items.

