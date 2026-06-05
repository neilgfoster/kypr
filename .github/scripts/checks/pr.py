from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from typing import Optional

import checks._util as _u
from checks._util import CheckResult


def check_dependabot() -> CheckResult:
    """Check for open Dependabot security alerts. Skips gracefully if not configured."""
    if not shutil.which("gh"):
        return CheckResult("dependabot", True, "gh CLI not available — skipping")

    code, repo_out, _ = _u.run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]
    )
    if code != 0:
        return CheckResult("dependabot", True, "could not determine repo — skipping")

    repo = repo_out.strip()
    if not re.match(r"^[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+$", repo):
        return CheckResult("dependabot", False, f"unexpected repo name format '{repo}' — cannot validate Dependabot alerts")
    code, out, err = _u.run([
        "gh", "api", f"/repos/{repo}/dependabot/alerts",
        "--paginate",
        "--jq", '.[] | select(.state == "open") | .number',
    ])
    if code != 0:
        err_text = (err or "").strip()
        err_low = err_text.lower()
        # Any 403 on the Dependabot API means the token cannot access it (either
        # GitHub App limitation or org-level restriction). Caller can't fix with
        # `gh auth login` — skip rather than fail. Run locally with full auth.
        if "403" in err_low:
            return CheckResult("dependabot", True, "Dependabot check skipped — token lacks access (run locally with gh auth)")
        if any(h.lower() in err_low for h in _GH_AUTH_HINTS):
            return CheckResult(
                "dependabot", False,
                "gh CLI not authenticated — run `gh auth login`",
                err_text[:200],
            )
        # 404 = Dependabot not configured; treat as no alerts
        if "404" in err_text or "not found" in err_low:
            return CheckResult("dependabot", True, "Dependabot not configured — no alerts")
        return CheckResult("dependabot", False, "Dependabot check failed", err_text[:200])

    open_lines = [ln for ln in out.splitlines() if ln.strip()]
    count = len(open_lines)

    if count > 0:
        code2, detail_out, _ = _u.run([
            "gh", "api", f"/repos/{repo}/dependabot/alerts",
            "--paginate",
            "--jq",
            '.[] | select(.state == "open") | .dependency.package.name + " (" + .security_advisory.severity + ")"',
        ])
        detail_lines = (detail_out.strip().splitlines() if code2 == 0 else [])[:5]
        detail = "\n".join(detail_lines)
        return CheckResult(
            "dependabot", False,
            f"{count} open Dependabot alert(s) — bump affected dependencies",
            detail,
        )

    return CheckResult("dependabot", True, "no open Dependabot alerts")


_THREADS_QUERY = (
    "query($owner:String!,$repo:String!,$pr:Int!){"
    "repository(owner:$owner,name:$repo){"
    "pullRequest(number:$pr){"
    "reviewThreads(first:100){nodes{id isResolved}}}}}"
)


def check_pr_threads(pr_number: int) -> CheckResult:
    """Check for unresolved PR review threads via GitHub GraphQL."""
    if not shutil.which("gh"):
        return CheckResult("threads", True, "gh CLI not available — skipping")

    code, out, _ = _u.run(
        ["gh", "repo", "view", "--json", "owner,name",
         "--jq", ".owner.login + \"/\" + .name"]
    )
    if code != 0:
        return CheckResult("threads", True, "could not determine repo — skipping")

    owner, _, repo_name = out.strip().partition("/")
    if not owner or not repo_name:
        return CheckResult("threads", True, "could not parse repo owner/name — skipping")

    code, out, err = _u.run([
        "gh", "api", "graphql",
        "-f", f"query={_THREADS_QUERY}",
        "-f", f"owner={owner}",
        "-f", f"repo={repo_name}",
        "-F", f"pr={pr_number}",
        "--jq",
        "[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length",
    ])
    if code != 0:
        err_text = (err or "").strip()
        err_low = err_text.lower()
        # Any 403 means the token cannot access the GraphQL API — skip rather
        # than fail so CI is not permanently blocked by a permission restriction.
        if "403" in err_low:
            return CheckResult("threads", True, "threads check skipped — token lacks access (run locally with gh auth)")
        if any(h.lower() in err_low for h in _GH_AUTH_HINTS):
            return CheckResult(
                "threads", False,
                "gh CLI not authenticated — run `gh auth login`",
                err_text[:200],
            )
        return CheckResult("threads", False, "could not check PR threads — failing closed", err_text[:200])

    try:
        count = int(out.strip())
    except ValueError:
        return CheckResult("threads", False, "could not parse thread response — failing closed")

    if count > 0:
        return CheckResult(
            "threads", False,
            f"{count} unresolved PR review thread(s) — fix or rebut each before merge",
        )

    return CheckResult("threads", True, f"no unresolved threads on PR #{pr_number}")


# Dependabot's GitHub-verified author identity. `gh pr view --json author` returns
# is_bot=true and one of these logins for Dependabot-raised PRs (observed:
# "app/dependabot"; "dependabot[bot]" on other gh versions). The exemption keys
# off this verified identity plus is_bot — never the PR body or branch name, both
# of which a malicious PR could spoof to skip template enforcement (WORK-0041).
# Safe identity basis: GitHub App slugs are globally unique (the "dependabot" app
# is owned by GitHub, so no other app can present this slug) and is_bot reflects
# the GitHub-verified account type, which a human/forked contributor cannot set.
# `is True` is deliberate: a non-bool truthy is_bot must not grant the exemption.
_DEPENDABOT_LOGINS = frozenset({"app/dependabot", "dependabot[bot]"})


def check_template(pr_number: int) -> CheckResult:
    code, out, err = _u.run(
        ["gh", "pr", "view", str(pr_number), "--json", "author,body"]
    )
    if code != 0:
        return CheckResult(
            "template",
            False,
            f"could not fetch PR #{pr_number}",
            err.strip(),
        )
    try:
        data = json.loads(out) if out.strip() else {}
    except json.JSONDecodeError as exc:
        return CheckResult(
            "template", False, f"could not parse PR #{pr_number} metadata", str(exc)
        )

    # Exempt Dependabot-authored PRs: the bot's body never matches the template,
    # and forcing a hand-rewrite on every dependency bump is pure friction. Gated
    # on the verified author (is_bot AND the Dependabot app login), so a
    # human/forked PR cannot spoof its way past the template check.
    author = data.get("author") or {}
    if author.get("is_bot") is True and author.get("login") in _DEPENDABOT_LOGINS:
        return CheckResult(
            "template", True,
            f"PR #{pr_number} authored by Dependabot ({author.get('login')}) — template check exempt",
        )

    checker = os.path.join(_u.REPO_ROOT, ".github", "scripts", "check_pr_template.py")
    if not os.path.isfile(checker):
        return CheckResult(
            "template", True,
            "skip (no check_pr_template.py — run SEED-0001 to build the repo-specific check)",
        )

    body = data.get("body") or ""
    # Truncate at 64 KiB before passing through the subprocess env (WORK-0063).
    body = body.encode("utf-8")[:65_536].decode("utf-8", errors="ignore")
    env = os.environ.copy()
    env["PR_BODY"] = body.strip().replace("\x00", "")
    result = subprocess.run(
        ["python3", checker],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return CheckResult(
            "template", False, "PR template incomplete", result.stdout.strip()
        )
    return CheckResult("template", True, f"PR #{pr_number} template valid")


_GH_AUTH_HINTS = ("authentication", "authenticate", "HTTP 401", "HTTP 403", "gh auth login")
_GH_RATE_HINTS = ("API rate limit", "secondary rate limit", "rate limit exceeded")


def _should_poll_ci(only: Optional[str], pr: Optional[int]) -> bool:
    """Whether to run the ci check. It polls the PR's own check-runs, which
    include this gate's matrix jobs — so running it as part of the gate
    (default mode) is self-referential and can never pass. Per the documented
    contract it runs only on an explicit ``--check ci`` and requires ``--pr``.
    """
    return only == "ci" and pr is not None


def check_ci(pr_number: int) -> CheckResult:
    """Inspect PR CI checks.

    Uses the structured JSON output instead of parsing tab-delimited text
    (the `gh pr checks` text format was treating CANCELLED / TIMED_OUT /
    STARTUP_FAILURE as PASS).

    Distinguishes auth/rate-limit failure from "no checks found".
    """
    if not shutil.which("gh"):
        return CheckResult("ci", False, "gh CLI not available")

    code, out, err = _u.run([
        "gh", "pr", "checks", str(pr_number),
        "--json", "name,state,bucket",
    ])
    if code != 0:
        err_text = (err or "").strip()
        err_low = err_text.lower()
        if any(h.lower() in err_low for h in _GH_AUTH_HINTS):
            return CheckResult(
                "ci", False,
                "gh CLI not authenticated — run `gh auth login`",
                err_text[:500],
            )
        if any(h.lower() in err_low for h in _GH_RATE_HINTS):
            return CheckResult(
                "ci", False,
                "GitHub API rate-limited — retry later",
                err_text[:500],
            )
        return CheckResult("ci", False, "gh pr checks failed", err_text[:500])

    try:
        checks = json.loads(out) if out.strip() else []
    except json.JSONDecodeError as exc:
        return CheckResult("ci", False, "could not parse gh JSON", str(exc))

    if not checks:
        return CheckResult(
            "ci", False,
            "no CI checks found — PR may not exist or checks haven't started",
        )

    # gh's `bucket` field collapses {COMPLETED.SUCCESS, COMPLETED.NEUTRAL,
    # COMPLETED.SKIPPED} -> "pass"; COMPLETED.{FAILURE, CANCELLED, TIMED_OUT,
    # ACTION_REQUIRED, STARTUP_FAILURE} -> "fail"; everything in-flight -> "pending".
    failing = [c for c in checks if c.get("bucket") == "fail"]
    pending = [c for c in checks if c.get("bucket") == "pending"]

    if failing:
        names = ", ".join(f"{c.get('name', '?')}[{c.get('state', '?')}]" for c in failing[:5])
        return CheckResult(
            "ci", False, f"{len(failing)} check(s) failing", names,
        )
    if pending:
        names = ", ".join(c.get("name", "?") for c in pending[:5])
        return CheckResult(
            "ci", False, f"{len(pending)} check(s) still running", names,
        )

    return CheckResult("ci", True, f"all {len(checks)} checks green for PR #{pr_number}")


