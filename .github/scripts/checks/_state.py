from __future__ import annotations

import json
import os
import re
import shutil
from typing import Optional

import checks._util as _u


def _work_item_id_re() -> re.Pattern[str]:
    prefix = re.escape(_u._work_item_prefix())
    return re.compile(rf"^({prefix}-\d+):")


def _state_backend() -> str:
    """Return the configured state backend name (default 'local-file').

    Read from hedl.toml [state] backend (ADR-022).
    """
    config = _u._load_hedl_config()
    if config is None:
        return "local-file"
    state_section = config.get("state") or {}
    return str(state_section.get("backend", "local-file"))


def _load_work_items() -> tuple[set[str], Optional[str]]:
    """Return (live_item_ids, error_or_None).

    live_item_ids contains WORK-XXXX strings for all active/backlog items.
    error_or_None is set when the backend could not be read; callers should
    propagate it as a FAIL rather than silently using an empty set.
    """
    backend = _state_backend()
    if backend == "github-issues":
        return _load_work_items_github()
    return _load_work_items_local()


def _load_work_items_local() -> tuple[set[str], Optional[str]]:
    work_path = os.path.join(_u.REPO_ROOT, ".work", "work.json")
    if not os.path.exists(work_path):
        return set(), None
    try:
        with open(work_path, encoding="utf-8") as fh:
            work = json.load(fh)
        live_ids: set[str] = set()
        for section in ("active", "backlog"):
            for item in work.get(section, []):
                live_ids.add(item.get("id", ""))
        return live_ids, None
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        return set(), f"work.json malformed: {exc}"


# Upper bound on open issues the github-issues backend reads in one pass. A repo
# at this many open WORK-issues is well beyond Hedl's design point; hitting the
# cap is surfaced as a loud error rather than silently dropping live IDs from the
# stale-WORK-ID check (which would weaken the gate).
_GITHUB_ISSUE_READ_LIMIT = 1000


def _load_work_items_github() -> tuple[set[str], Optional[str]]:
    if not shutil.which("gh"):
        return set(), "gh CLI not available — cannot read GitHub Issues backend"
    code, out, err = _u.run([
        "gh", "issue", "list", "--state", "open",
        "--json", "number,title", "--limit", str(_GITHUB_ISSUE_READ_LIMIT),
    ])
    if code != 0:
        return set(), f"gh issue list failed: {(err or '').strip()[:200]}"
    try:
        issues = json.loads(out) if out.strip() else []
    except json.JSONDecodeError as exc:
        return set(), f"could not parse gh issue list output: {exc}"
    if len(issues) >= _GITHUB_ISSUE_READ_LIMIT:
        # The read is unfiltered (counts ALL open issues, not just WORK-issues),
        # so hitting the cap means the gate cannot guarantee it saw every open
        # WORK-issue — a missed one would let a stale WORK-ID past the check.
        # Failing loudly is the safe choice for a gate; the real fix (a
        # hedl:work label-scoped, paginated read) is WORK-0032. See backends.md.
        return set(), (
            f"github-issues backend hit the read cap ({_GITHUB_ISSUE_READ_LIMIT} open "
            "issues); the unfiltered read cannot guarantee completeness — scope by "
            "the hedl:work label / paginate (WORK-0032) before trusting the gate"
        )
    live_ids: set[str] = set()
    for issue in issues:
        # `title` can be present-but-null in the gh JSON; coerce to "" so a null
        # title is ignored rather than crashing the gate with a TypeError.
        m = _work_item_id_re().match(issue.get("title") or "")
        if m:
            live_ids.add(m.group(1))
    return live_ids, None


