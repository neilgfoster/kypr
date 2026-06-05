from __future__ import annotations

import json
import os
import shutil
import sys
from typing import Optional

import checks._util as _u
from checks._util import CheckResult


def _pymarkdown_cmd() -> Optional[list[str]]:
    """Return the command prefix for pymarkdown, or None if not available."""
    for name in ("pymarkdown", "pymarkdownlnt"):
        if shutil.which(name):
            return [name]
    # Check the active virtual environment's bin directory when not on PATH
    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        for name in ("pymarkdown", "pymarkdownlnt"):
            candidate = os.path.join(venv, "bin", name)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return [candidate]
    # Try as a Python module with the current interpreter
    code, _, _ = _u.run([sys.executable, "-m", "pymarkdown", "version"])
    if code == 0:
        return [sys.executable, "-m", "pymarkdown"]
    return None


_SCHEMA_VALIDATOR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "check_markdown_schema.py")
_SCHEMAS_FILE = os.path.join(_u.REPO_ROOT, ".work", "config", "markdown-schemas.json")


def check_markdown_schemas() -> Optional[CheckResult]:
    """Validate markdown files against .work/config/markdown-schemas.json."""
    if not os.path.exists(_SCHEMA_VALIDATOR):
        return None
    if not os.path.exists(_SCHEMAS_FILE):
        return None

    code, out, err = _u.run([sys.executable, _SCHEMA_VALIDATOR, "--json"])

    try:
        result = json.loads(out)
    except (json.JSONDecodeError, ValueError):
        combined = (out + err).strip()
        return CheckResult("schemas", False, "schema validator produced unexpected output", combined[:500])

    if "error" in result:
        return CheckResult("schemas", False, result["error"])

    count = result.get("violation_count", 0)
    if not result.get("passed", True):
        violations = result.get("violations") or []
        lines = [
            f"  {v.get('file', '?')}: [{v.get('schema', '?')}] {v.get('message', '?')}"
            for v in violations[:20]
            if isinstance(v, dict)
        ]
        return CheckResult(
            "schemas",
            False,
            f"{count} schema violation(s)",
            "\n".join(lines),
        )

    return CheckResult("schemas", True, "all markdown files pass schema validation")


def check_markdown() -> Optional[CheckResult]:
    cmd = _pymarkdown_cmd()
    if cmd is None:
        return None
    config = os.path.join(_u.REPO_ROOT, ".pymarkdown.json")
    config_args = ["--config", config] if os.path.exists(config) else []
    # Use relative paths — pymarkdown's -e exclusion only works with relative paths.
    _targets = [
        "docs", ".claude", ".work", "config",
        "README.md", "CLAUDE.md",
        os.path.join(".github", "PULL_REQUEST_TEMPLATE.md"),
    ]
    scan_targets = [t for t in _targets if os.path.exists(os.path.join(_u.REPO_ROOT, t))]
    if not scan_targets:
        return None

    # Always exclude .work/reviews and .work/audits — generated review/audit artifacts (coverage
    # matrices, panel reports) with intentionally long table lines. pymarkdown handles non-existent
    # exclusion paths gracefully (exit 0).
    exclude_args = ["-e", ".work/reviews", "-e", ".work/audits"]
    code, out, err = _u.run(cmd + config_args + ["scan", "--recurse"] + exclude_args + scan_targets)
    if code != 0:
        combined = (out + err).strip()
        lines = combined.splitlines()[:30]
        return CheckResult("markdown", False, "pymarkdown violations found", "\n".join(lines))
    return CheckResult("markdown", True, "pymarkdown clean")


