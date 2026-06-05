from __future__ import annotations

import json
import re
from typing import Optional

import checks._util as _u
from checks._util import CheckResult


def check_git() -> CheckResult:
    _, out, _ = _u.run(["git", "status", "--porcelain"])
    if out.strip():
        return CheckResult(
            "git",
            False,
            "uncommitted changes",
            out.strip(),
        )

    _, branch, _ = _u.run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    branch = branch.strip()
    if not branch:
        return CheckResult("git", False, "could not determine current branch")
    if branch == "main":
        return CheckResult(
            "git",
            False,
            "on main branch — create a feature branch first",
        )

    return CheckResult("git", True, f"clean, on {branch}")


BRANCH_PATTERN = re.compile(
    r"^(feat|fix|refactor|docs|chore|spike)/[a-z0-9][a-z0-9-]*$"
)
VALID_PREFIXES = ("feat/", "fix/", "refactor/", "docs/", "chore/", "spike/")


def check_branch(pr_number: Optional[int] = None) -> Optional[CheckResult]:
    _, branch, _ = _u.run(["git", "branch", "--show-current"])
    branch = branch.strip()

    if not branch:
        # Detached HEAD — common in CI merge-ref checkouts.
        if pr_number is None:
            return None  # no PR context; skip cleanly
        # In --pr mode, derive the head branch name from the PR and validate it.
        code, out, err = _u.run(["gh", "pr", "view", str(pr_number), "--json", "headRefName"])
        if code != 0:
            return CheckResult(
                "branch",
                False,
                f"detached HEAD and could not fetch PR #{pr_number} head ref",
                (err or out).strip()[:200],
            )
        try:
            branch = json.loads(out).get("headRefName", "").strip()
        except (json.JSONDecodeError, AttributeError):
            return CheckResult(
                "branch",
                False,
                f"could not parse headRefName for PR #{pr_number}",
                out.strip()[:200],
            )
        if not branch:
            return CheckResult("branch", False, f"PR #{pr_number} has no headRefName")

    if branch == "main":
        return CheckResult(
            "branch",
            False,
            "on main — create a feature branch first",
        )

    if not BRANCH_PATTERN.match(branch):
        prefixes = ", ".join(f"{p}<description>" for p in VALID_PREFIXES)
        return CheckResult(
            "branch",
            False,
            f"'{branch}' does not follow naming convention",
            f"Expected: {prefixes}\n"
            "Rules: prefix/ followed by lowercase letters, digits, hyphens only.",
        )

    return CheckResult("branch", True, branch)


# Dispatch rules are loaded from .work/config/dispatch-rules.json at runtime.
# Edit that file to add or modify mandatory agent requirements without changing
# this script. Patterns are matched with re.search — anchor with (^|/) or ^ to
# prevent false matches in subdirectories or vendored copies.
