from __future__ import annotations

import os
import shutil
from typing import Optional

import checks._util as _u
from checks._util import (
    CheckResult,
)


def check_lint() -> Optional[CheckResult]:
    config = _u._load_hedl_config()
    if config is not None and "verify" in config:
        spec = config["verify"].get("lint")
        if spec is None:
            return None  # [verify] present but lint not declared — skip
        return _u._run_declared_check("lint", spec, _u._get_gate_timeout(config), _u._verify_allowlist(config))
    # No [verify] — built-in Python default profile
    pyproject = os.path.join(_u.REPO_ROOT, "pyproject.toml")
    ruff_toml = os.path.join(_u.REPO_ROOT, "ruff.toml")
    if not os.path.exists(pyproject) and not os.path.exists(ruff_toml):
        return None  # no ruff config — check not applicable
    if not shutil.which("ruff"):
        return CheckResult("lint", False, "ruff not found — uv sync  or  pip install ruff")

    code, out, err = _u.run(["ruff", "check", "."])
    if code != 0:
        return CheckResult("lint", False, "ruff check failed", (out + err).strip())
    return CheckResult("lint", True, "ruff clean")


def check_types() -> Optional[CheckResult]:
    config = _u._load_hedl_config()
    if config is not None and "verify" in config:
        spec = config["verify"].get("types")
        if spec is None:
            return None  # [verify] present but types not declared — skip
        return _u._run_declared_check("types", spec, _u._get_gate_timeout(config), _u._verify_allowlist(config))
    # No [verify] — built-in Python default profile
    src_candidates = ["src", "lib", "app", "skill/hedl/scripts", "tests", "skill/hedl/tests"]
    # Skip dirs with no .py files (avoids mypy exit-code 2 on empty/cache-only dirs).
    targets = [
        d for d in src_candidates
        if os.path.isdir(os.path.join(_u.REPO_ROOT, d))
        and any(f.endswith(".py") for f in os.listdir(os.path.join(_u.REPO_ROOT, d)))
    ]
    if not targets:
        return None  # no source directories — check not applicable
    if not shutil.which("mypy"):
        return CheckResult("types", False, "mypy not found — uv sync  or  pip install mypy")

    code, out, err = _u.run(["mypy", "--strict"] + targets)
    if code != 0:
        combined = (out + err).strip()
        # show only error lines, cap at 20
        lines = [ln for ln in combined.splitlines() if ": error:" in ln][:20]
        return CheckResult("types", False, "mypy errors", "\n".join(lines))
    return CheckResult("types", True, "mypy clean")


def check_tests() -> Optional[CheckResult]:
    config = _u._load_hedl_config()
    if config is not None and "verify" in config:
        spec = config["verify"].get("test")  # hedl.toml key is "test"; display name stays "tests"
        if spec is None:
            return None  # [verify] present but test not declared — skip
        return _u._run_declared_check("tests", spec, _u._get_gate_timeout(config), _u._verify_allowlist(config))
    # No [verify] — built-in Python default profile
    tests_candidates = ["tests", "skill/hedl/tests"]
    has_tests = any(
        os.path.isdir(os.path.join(_u.REPO_ROOT, d))
        and any(f.endswith(".py") for f in os.listdir(os.path.join(_u.REPO_ROOT, d)))
        for d in tests_candidates
    )
    if not has_tests:
        return None  # no tests directory — check not applicable
    if not shutil.which("pytest"):
        return CheckResult("tests", False, "pytest not found — uv sync  or  pip install pytest")

    code, out, err = _u.run(["pytest", "--tb=short", "-q"])
    if code != 0:
        combined = (out + err).strip()
        lines = combined.splitlines()[-30:]
        return CheckResult("tests", False, "pytest failures", "\n".join(lines))
    # extract summary line
    summary_lines = [ln for ln in out.splitlines() if "passed" in ln or "failed" in ln]
    summary = summary_lines[-1] if summary_lines else "passed"
    return CheckResult("tests", True, summary)


