"""Shared primitives for the am_i_done checks package."""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from typing import Any, Optional

_SCRIPTS_DIR = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
# Navigate up from skill/hedl/scripts/checks/ to the hedl repo root (4 levels)
_HEDL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPTS_DIR))))


def _hedl_version() -> str:
    try:
        pyproject = os.path.join(_HEDL_ROOT, "pyproject.toml")
        with open(pyproject, "rb") as fh:
            data = tomllib.load(fh)
        return str(data.get("project", {}).get("version", "unknown"))
    except Exception:
        return "unknown"

try:
    REPO_ROOT = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True, timeout=10,
    ).strip()
except FileNotFoundError:
    print("Error: git is not installed or not on PATH", file=sys.stderr)
    sys.exit(1)
except subprocess.TimeoutExpired:
    print("Error: git rev-parse timed out", file=sys.stderr)
    sys.exit(1)
except subprocess.CalledProcessError:
    print("Error: not inside a git repository", file=sys.stderr)
    sys.exit(1)

def is_framework_repo(repo_root: str = "") -> bool:
    """Return True iff the current repo is the Hedl framework source tree.

    Uses skill/hedl/plugin.json as the sentinel — it is Hedl-specific and absent
    in adopter repos, monorepos that coincidentally contain a skill/hedl/ path, and
    sparse checkouts that omit skill/hedl/. This single check replaces the scattered
    os.path.isdir(skill/hedl) guards across check modules.
    """
    root = repo_root or REPO_ROOT
    return os.path.isfile(os.path.join(root, "skill", "hedl", "plugin.json"))


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    detail: str = ""


@dataclass
class Report:
    results: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failed(self) -> list[CheckResult]:
        return [r for r in self.results if not r.passed]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "detail": r.detail,
                }
                for r in self.results
            ],
        }

    def print_human(self) -> None:
        width = 60
        print(f"\n{'─' * width}")
        print("  am_i_done?")
        print(f"{'─' * width}")
        for r in self.results:
            status = "PASS" if r.passed else "FAIL"
            icon = "+" if r.passed else "x"
            print(f"  [{icon}] {r.name:<12} {status}  {r.message}")
            if r.detail and not r.passed:
                for line in r.detail.strip().splitlines()[:10]:
                    print(f"           {line}")
        print(f"{'─' * width}")
        if self.passed:
            print("  DONE — all checks pass.\n")
        else:
            failed_names = ", ".join(r.name for r in self.failed)
            print(f"  NOT DONE — failing: {failed_names}\n")
        print(f"{'─' * width}\n")


def run(cmd: list[str], cwd: str = REPO_ROOT, timeout: int = 120) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", f"timed out after {timeout}s: {' '.join(cmd)}"

def _work_item_prefix() -> str:
    """Return work_item_prefix from .work/context.json (default 'WORK')."""
    ctx_path = os.path.join(REPO_ROOT, ".work", "context.json")
    try:
        with open(ctx_path, encoding="utf-8") as fh:
            data = json.load(fh)
        prefix = str(data.get("meta", {}).get("work_item_prefix", "WORK"))
        if re.fullmatch(r"[A-Z][A-Z0-9_-]*", prefix):
            return prefix
        return "WORK"
    except (OSError, json.JSONDecodeError, AttributeError):
        return "WORK"


def _load_hedl_config() -> Optional[dict[str, Any]]:
    """Load hedl.toml from REPO_ROOT. Returns None if absent or unreadable."""
    path = os.path.join(REPO_ROOT, "hedl.toml")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as fh:
            return tomllib.load(fh)
    except Exception:
        return None


def _get_gate_timeout(config: Optional[dict[str, Any]]) -> int:
    if config is None:
        return 120
    gate_section = config.get("gate") or {}
    return int(gate_section.get("timeout", 120))



# WORK-0021: a [verify] command may only invoke an allow-listed executable,
# named bare (no path), with no shell-control metacharacters. This is
# DEFENSE IN DEPTH, not a complete RCE control: hedl.toml is repo-committed and
# the gate runs on PR heads in CI, so a malicious PR could still achieve
# execution through an allowed runner that executes committed repo content
# (pytest loads conftest.py; make runs a committed Makefile; npm/pnpm run
# package.json scripts). What the allow-list DOES close is the trivial inline
# vector — a one-line `python -c '...'` / `bash -c '...'` / `node -e '...'`
# straight from hedl.toml. The real control for untrusted PRs is GitHub's
# "require approval to run workflows for outside/first-time contributors"
# (a CI setting), not this list. See skill/hedl/references/tiers.md.
_VERIFY_DEFAULT_ALLOWLIST: frozenset[str] = frozenset(
    {"pytest", "mypy", "ruff", "npm", "pnpm", "make"}
)
# Never allowed, even if an operator lists them under [gate] allowed_commands:
# interpreters and execution forwarders turn a one-line [verify] entry into
# arbitrary inline code, defeating the allow-list. The set is necessarily
# non-exhaustive (it cannot enumerate every interpreter) — it blocks the obvious
# forwarders so the operator cannot trivially re-open the inline vector.
_VERIFY_DENYLIST: frozenset[str] = frozenset(
    {
        "env", "sh", "bash", "zsh", "dash", "fish", "busybox",
        "python", "python2", "python3", "node", "nodejs", "deno", "bun",
        "ruby", "perl", "php", "lua", "tclsh", "pwsh", "powershell",
        "xargs", "find", "awk", "eval", "exec",
    }
)
_SHELL_METACHARS = re.compile(r"[;&|<>$`\n\r\x00\t]")


def _verify_allowlist(config: Optional[dict[str, Any]]) -> frozenset[str]:
    """Effective [verify] executable allow-list: the built-in default plus any
    bare executable names operators add under hedl.toml [gate] allowed_commands.

    The extension is additive (it can never narrow the default and break the
    standard lint/types/test runners) and itself constrained: an entry is
    ignored unless it is a bare name (no path separator), free of shell
    metacharacters, and not in the interpreter/forwarder denylist — so the
    operator cannot re-open the inline-code vector through config.
    """
    allowed = set(_VERIFY_DEFAULT_ALLOWLIST)
    gate = (config or {}).get("gate") or {}
    extra = gate.get("allowed_commands", [])
    if isinstance(extra, list):
        for name in extra:
            if (
                isinstance(name, str)
                and name
                and "/" not in name
                and "\\" not in name
                and not _SHELL_METACHARS.search(name)
                and name not in _VERIFY_DENYLIST
            ):
                allowed.add(name)
    return frozenset(allowed)


def _run_declared_check(
    name: str, spec: Any, gate_timeout: int, allowed: frozenset[str]
) -> CheckResult:
    """Run a single check declared in hedl.toml [verify].

    spec is either a string (short form) or a dict with 'cmd' and optional
    'timeout'/'cwd' (long form). Commands are parsed with shlex.split and run
    via subprocess list form — no shell=True. The executable (cmd[0]) must be a
    bare name (no path) present in `allowed`; shell metacharacters are rejected;
    a long-form 'cwd' must stay within the repo. WORK-0021.
    """
    if isinstance(spec, str):
        cmd_str, timeout, cwd = spec, gate_timeout, REPO_ROOT
    elif isinstance(spec, dict):
        cmd_str = str(spec.get("cmd", ""))
        timeout = int(spec.get("timeout", gate_timeout))
        rel = str(spec.get("cwd", ""))
        if rel:
            cwd = os.path.realpath(os.path.join(REPO_ROOT, rel))
            root = os.path.realpath(REPO_ROOT)
            if cwd != root and not cwd.startswith(root + os.sep):
                return CheckResult(
                    name, False, f"[verify.{name}] cwd '{rel}' escapes the repo root"
                )
        else:
            cwd = REPO_ROOT
    else:
        return CheckResult(name, False, f"[verify.{name}] must be a string or table")

    if _SHELL_METACHARS.search(cmd_str):
        return CheckResult(
            name, False,
            f"[verify.{name}] contains shell metacharacters — not allowed "
            "(commands run with shell=False). Wrap pipelines in a script.",
        )

    try:
        cmd = shlex.split(cmd_str)
    except ValueError as exc:
        return CheckResult(name, False, f"[verify.{name}] command parse error: {exc}")

    if not cmd:
        return CheckResult(name, False, f"[verify.{name}] has no command")

    exe = cmd[0]
    if "/" in exe or "\\" in exe:
        return CheckResult(
            name, False,
            f"[verify.{name}] executable must be a bare name, not a path: '{exe}'. "
            "Put the tool on PATH and reference it by name.",
        )

    # Defense in depth: reject denied interpreters/forwarders here too, so the
    # denylist holds even if a future caller hands us an allow-list that was not
    # built through _verify_allowlist.
    if exe in _VERIFY_DENYLIST:
        return CheckResult(
            name, False,
            f"[verify.{name}] executable '{exe}' is a denied interpreter/forwarder.",
        )

    if exe not in allowed:
        return CheckResult(
            name, False,
            f"[verify.{name}] executable '{exe}' not in allow-list "
            f"({', '.join(sorted(allowed))}). Add its name to hedl.toml "
            "[gate] allowed_commands if intended.",
        )

    if not shutil.which(exe):
        return CheckResult(name, False, f"{exe} not found (declared in hedl.toml [verify.{name}])")

    code, out, err = run(cmd, cwd=cwd, timeout=timeout)
    if code != 0:
        combined = (out + err).strip()
        lines = combined.splitlines()[-30:]
        return CheckResult(name, False, f"{cmd[0]} failed", "\n".join(lines))
    return CheckResult(name, True, f"{cmd[0]} passed")


