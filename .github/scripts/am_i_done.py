#!/usr/bin/env python3
"""
am_i_done.py — deterministic completion gate.

Runs every applicable check locally and against CI. Exits 0 only when
all checks pass. Designed to be called by both humans and agents.

Usage:
  python3 .github/scripts/am_i_done.py                  # local checks only
  python3 .github/scripts/am_i_done.py --check git      # single check
  python3 .github/scripts/am_i_done.py --json           # machine-readable output
  python3 .github/scripts/am_i_done.py --pr 42          # + template, threads, dependabot
  python3 .github/scripts/am_i_done.py --pr 42 --check ci  # poll CI check status

Checks without --pr (mirrors CI jobs where possible — run these locally first):
  git       - working tree clean, not on main
  branch    - branch name follows naming convention (feat/, fix/, refactor/, docs/, chore/, spike/)
  config    - validate MANDATORY_AGENTS table is consistent with actual agent files on disk
  commands  - detect stale work-item IDs in .claude/commands/ (reads from configured backend)
  dispatch  - enforce mandatory agent floor for a review panel (requires --panel; not run by default)
  streams   - validate no file overlap across parallel worktree streams (requires --streams; not run by default)
  schemas   - validate markdown files against .work/config/markdown-schemas.json
  markdown  - pymarkdown lint (if pymarkdown available)
  lint      - ruff check (if ruff available)
  types     - mypy --strict (if mypy available and src/, lib/, or app/ exists)
  tests     - pytest (if tests/ exists)

Additional checks enabled by --pr N (require gh CLI + GitHub auth):
  template  - PR body matches .github/PULL_REQUEST_TEMPLATE.md
  threads   - no unresolved PR review threads (deterministic via GitHub GraphQL)
  dependabot - no open Dependabot security alerts (graceful skip if not configured)
  ci        - poll GitHub CI check status (requires --check ci --pr N; not run by default)

Note: CodeQL analysis (python, actions) runs in CI only and cannot be replicated locally.
"""


from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Optional

# Ensure checks/ package is resolvable regardless of how this script is invoked.
_HERE = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import checks._util as _cu  # noqa: E402,I001

# Re-export everything so existing callers work unchanged.
# noqa comments suppress E402 (not at top — sys.path setup required) and
# F401 (imported but unused — these are intentional re-exports).
from checks import (  # noqa: E402,I001,F401
    CheckResult, Report, REPO_ROOT, _hedl_version,  # noqa: F401
    _work_item_prefix, _load_hedl_config, _get_gate_timeout,  # noqa: F401
    _VERIFY_DEFAULT_ALLOWLIST, _VERIFY_DENYLIST, _SHELL_METACHARS,  # noqa: F401
    _verify_allowlist, _run_declared_check,  # noqa: F401
    _work_item_id_re, _state_backend, _load_work_items,  # noqa: F401
    _load_work_items_local, _load_work_items_github, _GITHUB_ISSUE_READ_LIMIT,  # noqa: F401
    check_git, check_branch, BRANCH_PATTERN, VALID_PREFIXES,  # noqa: F401
    check_dispatch, _load_dispatch_rules, _get_changed_files, _required_agents,  # noqa: F401
    _DISPATCH_RULES_FILE,  # noqa: F401
    check_config, check_state_template_sync, check_workflow_template_sync, check_commands,  # noqa: F401
    check_seed_placeholders,  # noqa: F401
    check_markdown_schemas, check_markdown, _pymarkdown_cmd, _SCHEMA_VALIDATOR, _SCHEMAS_FILE,  # noqa: F401
    check_lint, check_types, check_tests,  # noqa: F401
    check_dependabot, check_pr_threads, check_template, check_ci,  # noqa: F401
    _should_poll_ci, _DEPENDABOT_LOGINS, _GH_AUTH_HINTS, _GH_RATE_HINTS,  # noqa: F401
    check_streams, check_skill_metadata, check_docs_index, check_doc_generated_facts,  # noqa: F401
    _word_or_int, _count_command_behaviours,  # noqa: F401
)

run = _cu.run  # noqa: F401


CLI_SPEC: dict[str, Any] = {
    "name": "am_i_done",
    "script": "am_i_done.py",
    "description": "Deterministic completion gate — runs all applicable checks and exits 0 only when all pass.",
    "invocation": "python3 .github/scripts/am_i_done.py",
    "commands": [
        {
            "name": "default",
            "description": "Run applicable checks (all, or one with --check)",
            "args": [
                {
                    "flag": "--check",
                    "type": "str",
                    "required": False,
                    "choices": [
                        "git", "branch", "dispatch", "config", "state-sync", "seed", "commands",
                        "schemas", "markdown", "lint", "types", "tests",
                        "template", "dependabot", "threads", "ci",
                        "streams", "skill-meta", "docs-index", "doc-facts",
                    ],
                    "help": "Run only this check",
                },
                {
                    "flag": "--pr",
                    "type": "int",
                    "required": False,
                    "help": "PR number for template, dependabot, threads, and ci checks",
                },
                {
                    "flag": "--panel",
                    "type": "str",
                    "required": False,
                    "help": "Comma-separated list of agents dispatched (for dispatch check)",
                },
                {
                    "flag": "--streams",
                    "type": "str",
                    "required": False,
                    "help": "Comma-separated branch names for parallel worktree file-scoping check",
                },
                {
                    "flag": "--json",
                    "type": "bool",
                    "required": False,
                    "help": "Machine-readable JSON output of check results",
                },
            ],
            "output": (
                "Exits 0 if all checks pass, 1 if any fail, 2 if no checks apply. "
                "--json emits {passed, checks:[{name, passed, message, detail}]}."
            ),
        },
    ],
}



def main() -> int:
    if "--schema" in sys.argv:
        print(json.dumps(CLI_SPEC, indent=2))
        return 0

    if "--version" in sys.argv:
        print(_hedl_version())
        return 0

    parser = argparse.ArgumentParser(description="Deterministic completion gate")
    _check_spec = next(a for a in CLI_SPEC["commands"][0]["args"] if a["flag"] == "--check")
    parser.add_argument(
        "--check",
        choices=_check_spec["choices"],
        help=_check_spec["help"],
    )
    parser.add_argument("--pr", type=int, help="PR number for template and CI checks")
    parser.add_argument(
        "--panel",
        help="Comma-separated list of agents dispatched for this review (for dispatch check)",
    )
    parser.add_argument(
        "--streams",
        help="Comma-separated branch names for parallel worktree file-scoping check",
    )
    parser.add_argument("--json", action="store_true", dest="as_json", help="JSON output")
    args = parser.parse_args()

    report = Report()

    def maybe_add(result: Optional[CheckResult]) -> None:
        if result is not None:
            report.results.append(result)

    only = args.check

    panel = [a.strip() for a in args.panel.split(",") if a.strip()] if args.panel else []
    streams = [s.strip() for s in args.streams.split(",") if s.strip()] if args.streams else []

    if not only or only == "git":
        maybe_add(check_git())
    if not only or only == "branch":
        maybe_add(check_branch(pr_number=args.pr))
    if only == "dispatch" or (args.panel and not only):
        maybe_add(check_dispatch(panel))
    if not only or only == "config":
        maybe_add(check_config())
    if not only or only == "state-sync":
        maybe_add(check_state_template_sync())
    if not only or only == "seed":
        maybe_add(check_seed_placeholders())
    if not only or only == "wf-sync":
        maybe_add(check_workflow_template_sync())
    if not only or only == "commands":
        maybe_add(check_commands())
    if not only or only == "schemas":
        maybe_add(check_markdown_schemas())
    if not only or only == "markdown":
        maybe_add(check_markdown())
    if not only or only == "lint":
        maybe_add(check_lint())
    if not only or only == "types":
        maybe_add(check_types())
    if not only or only == "tests":
        maybe_add(check_tests())
    if not only or only == "skill-meta":
        maybe_add(check_skill_metadata())
    if not only or only == "docs-index":
        maybe_add(check_docs_index())
    if not only or only == "doc-facts":
        maybe_add(check_doc_generated_facts())
    # Extra declared checks: any [verify] key that is not a standard check name.
    # These only run in the default (no --check filter) mode.
    if not only:
        _cfg = _load_hedl_config()
        if _cfg and "verify" in _cfg:
            _gate_to = _get_gate_timeout(_cfg)
            _allowed = _verify_allowlist(_cfg)
            _STANDARD_VERIFY_KEYS = {"lint", "types", "test"}
            for _name, _spec in _cfg["verify"].items():
                if _name not in _STANDARD_VERIFY_KEYS:
                    maybe_add(_run_declared_check(_name, _spec, _gate_to, _allowed))
    if (not only or only == "template") and args.pr:
        maybe_add(check_template(args.pr))
    if (not only or only == "dependabot") and args.pr:
        maybe_add(check_dependabot())
    if (not only or only == "threads") and args.pr:
        maybe_add(check_pr_threads(args.pr))
    if _should_poll_ci(only, args.pr):
        maybe_add(check_ci(args.pr))
    if only == "streams" or (streams and not only):
        maybe_add(check_streams(streams))

    if not report.results:
        # Distinct exit code so callers can tell "verified clean" from
        # "nothing to verify".
        print("No applicable checks found. Nothing to validate.", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        report.print_human()

    _append_gate_insight(report)

    return 0 if report.passed else 1


def _append_gate_insight(report: Report) -> None:
    """Append a gate_run event to .work/insights/events.jsonl if insights are enabled."""
    config = _load_hedl_config()
    if config is None:
        return
    if not config.get("insights", {}).get("enabled", False):
        return
    # No lock-in (WORK-0076): never CREATE .work/ in a gate-only repo that ships
    # none — only record if the .work/ layer already exists (cf. WORK-0002).
    if not os.path.isdir(os.path.join(REPO_ROOT, ".work")):
        return

    import datetime as _dt
    insights_dir = os.path.join(REPO_ROOT, ".work", "insights")
    events_file = os.path.join(insights_dir, "events.jsonl")
    try:
        os.makedirs(insights_dir, exist_ok=True)
        tier = "unknown"
        marker = os.path.join(REPO_ROOT, ".hedl-tier")
        if os.path.exists(marker):
            try:
                tier = json.loads(open(marker).read()).get("tier", "unknown")
            except Exception:
                pass
        checks: dict[str, str] = {}
        overridden: list[str] = []
        for r in report.results:
            checks[r.name] = "pass" if r.passed else "fail"
        event = {
            "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "type": "gate_run",
            "tier": tier,
            "checks": checks,
            "overridden": overridden,
        }
        with open(events_file, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event) + "\n")
    except Exception:
        pass  # insights are best-effort; never block the gate


if __name__ == "__main__":
    sys.exit(main())
