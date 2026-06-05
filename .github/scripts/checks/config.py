from __future__ import annotations

import json
import os
import re
from typing import Optional

import checks._util as _u
from checks._state import _load_work_items, _state_backend
from checks._util import (
    CheckResult,
)
from checks.dispatch import _DISPATCH_RULES_FILE, _load_dispatch_rules


def check_config() -> Optional[CheckResult]:
    """Validate dispatch-rules.json against actual agent files on disk.

    Returns None (skip) when .work/ does not exist — gate-only tier installs
    have no dispatch config and the check is not applicable. Returns FAIL when
    .work/ exists but dispatch-rules.json is missing, because that indicates
    a partial / broken configuration.
    """
    work_dir = os.path.join(_u.REPO_ROOT, ".work")
    if not os.path.isdir(work_dir):
        return None  # gate-only install — no .work/ directory

    if not os.path.exists(_DISPATCH_RULES_FILE):
        return CheckResult(
            "config", False,
            "dispatch-rules.json not found",
            f"Expected at {_DISPATCH_RULES_FILE}",
        )

    try:
        mandatory_agents, always_required = _load_dispatch_rules()
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        return CheckResult("config", False, f"dispatch-rules.json malformed: {exc}")

    agents_dir = os.path.join(_u.REPO_ROOT, ".claude", "agents")
    if not os.path.isdir(agents_dir):
        return CheckResult("config", False, ".claude/agents/ directory not found")

    on_disk = {
        os.path.splitext(f)[0]
        for f in os.listdir(agents_dir)
        if f.endswith(".md")
    }

    referenced = set(always_required)
    for _, agents in mandatory_agents:
        referenced.update(agents)

    stale = sorted(referenced - on_disk)
    issues = []
    if stale:
        issues.append("dispatch-rules.json references agents with no file:")
        issues.extend(f"  missing file: .claude/agents/{a}.md" for a in stale)

    if issues:
        return CheckResult("config", False, f"{len(stale)} stale rule(s)", "\n".join(issues))

    return CheckResult(
        "config",
        True,
        f"dispatch rules consistent ({len(referenced)} agents, {len(on_disk)} on disk)",
    )


# State-template sync (WORK-0025)
# ---------------------------------------------------------------------------
# `skill/hedl/work-state/` is the installable template (projection source per
# tiers.json: {source: work-state, target: .work, on_exists: skip}); `.work/`
# is live state (the projection target). Most of the tree diverges by design:
# work.json, context.json, session.json and phases/* are seed-vs-live, and
# config/project-registry.json is scout-populated per project. A small subset
# is framework config / boilerplate that must stay byte-identical so the
# defaults shipped to adopters never drift from what Hedl itself runs
# (dogfooding fidelity). This check guards exactly that subset.
#
# Scoped to the framework source repo, detected by skill/hedl/ existing at the
# repo root. In an adopter repo the skill lives under .claude/skills/hedl/, so
# the check is a no-op and never nags an operator who has customised their own
# .work/config. Once the framework repo is identified, a missing state tree is a
# FAIL (a broken/half-moved checkout), not a silent skip.
#
# The check is read-only and never emits file contents — it only reports drift by
# path name — so it is not a content-disclosure surface. The byte-comparison is
# intentional (line endings included). It cannot defend against a PR that edits
# both copies in lockstep; that boundary is owned by branch protection / fork
# approval, as recorded for the gate's executable allow-list (WORK-0021).

_STATE_SYNC_GUARDED = (
    "config/dispatch-rules.json",
    "config/markdown-schemas.json",
    "decisions/README.md",
    "reviews/README.md",
)

# Guarded files are small configs / READMEs; anything larger is treated as a
# fault rather than read into memory (defends against a symlinked large file or
# device node resolved at a guarded path).
_STATE_SYNC_MAX_BYTES = 1_048_576  # 1 MiB


def _read_guarded(
    path: str, root: str, label: str, rel: str, problems: list[str],
) -> Optional[bytes]:
    """Read a file only if it is a regular file contained within root.

    Appends a human-readable message to problems and returns None on any
    error (path-escape, absent, non-regular-file, oversized, unreadable).
    Never raises — gate no-traceback discipline.
    """
    real = os.path.realpath(path)
    if real != root and not real.startswith(root + os.sep):
        problems.append(f"  escapes tree ({label}): {rel}")
        return None
    if not os.path.isfile(path):
        kind = "not a regular file" if os.path.lexists(path) else "missing"
        problems.append(f"  {kind} ({label}): {rel}")
        return None
    try:
        if os.path.getsize(path) > _STATE_SYNC_MAX_BYTES:
            problems.append(f"  too large to compare ({label}): {rel}")
            return None
        with open(path, "rb") as fh:
            return fh.read()
    except OSError as exc:
        reason = exc.strerror or type(exc).__name__
        problems.append(f"  unreadable ({label}): {rel} ({reason})")
        return None


def check_state_template_sync() -> Optional[CheckResult]:
    """Fail if guarded framework-config files drift between the live .work/ tree
    and the skill/hedl/work-state/ template they are projected from.

    Returns None (skip) unless this is the framework source repo (skill/hedl/ at
    the repo root). Adopter installs (skill under .claude/skills/) skip it.
    """
    if not _u.is_framework_repo():
        return None  # adopter repo layout — check not applicable

    if not _STATE_SYNC_GUARDED:
        # A misconfiguration (e.g. the tuple emptied during a merge) must FAIL,
        # not vacuously pass with zero comparisons performed.
        return CheckResult(
            "state-sync", False,
            "no guarded files configured",
            "  _STATE_SYNC_GUARDED is empty — the guard would compare nothing",
        )

    # realpath both roots once: canonicalising here (rather than relying on the
    # raw _u.REPO_ROOT) keeps the containment check below correct even when the repo
    # is reached through a symlinked path.
    live_root = os.path.realpath(os.path.join(_u.REPO_ROOT, ".work"))
    template_root = os.path.realpath(os.path.join(_u.REPO_ROOT, "skill", "hedl", "work-state"))

    # In the framework repo both trees must exist; a missing one is a broken
    # checkout, not a reason to silently stop guarding.
    missing_trees = [
        rel for rel, path in (
            (".work/", live_root),
            ("skill/hedl/work-state/", template_root),
        )
        if not os.path.isdir(path)
    ]
    if missing_trees:
        return CheckResult(
            "state-sync", False,
            "state tree missing in framework repo",
            "  expected present: " + ", ".join(missing_trees),
        )

    drifted: list[str] = []
    problems: list[str] = []  # escaped / missing / non-file / oversized / unreadable

    for rel in _STATE_SYNC_GUARDED:
        live_bytes = _read_guarded(
            os.path.join(live_root, rel), live_root, "live .work", rel, problems,
        )
        template_bytes = _read_guarded(
            os.path.join(template_root, rel), template_root, "template", rel, problems,
        )
        if (
            live_bytes is not None
            and template_bytes is not None
            and live_bytes != template_bytes
        ):
            drifted.append(rel)

    if drifted or problems:
        issues = list(problems)
        issues += [
            f"  drifted: .work/{rel} != skill/hedl/work-state/{rel}" for rel in drifted
        ]
        issues.append(
            "  Update both copies in lockstep — the seed is what ships to adopters."
        )
        return CheckResult(
            "state-sync",
            False,
            f"{len(drifted)} drifted, {len(problems)} unresolved in guarded state template",
            "\n".join(issues),
        )

    return CheckResult(
        "state-sync",
        True,
        f"live .work/ matches work-state template ({len(_STATE_SYNC_GUARDED)} guarded files)",
    )


# Files in skill/hedl/workflows/ that are shipped to adopters as real copies of
# the corresponding .github/workflows/ file and must stay byte-identical.
# am-i-done.yml is intentionally excluded: the framework copy uses `uv sync`
# (the lockfile ships with the framework repo) while the template copy uses
# `pip install --require-hashes -r requirements-ci.txt` (adopters get only the
# pinned requirements manifest). This divergence is documented in both files.
_WORKFLOW_TEMPLATE_GUARDED = (
    "codeql.yml",
)


def check_workflow_template_sync() -> Optional[CheckResult]:
    """Fail if guarded workflow templates in skill/hedl/workflows/ drift from
    the live copies in .github/workflows/.

    Scoped to the framework source repo (skill/hedl/ at repo root). Adopter
    repos skip this check.
    """
    if not _u.is_framework_repo():
        return None  # adopter repo — not applicable

    skill_wf = os.path.realpath(os.path.join(_u.REPO_ROOT, "skill", "hedl", "workflows"))
    live_wf = os.path.realpath(os.path.join(_u.REPO_ROOT, ".github", "workflows"))

    missing = [
        p for p in (skill_wf, live_wf)
        if not os.path.isdir(p)
    ]
    if missing:
        return CheckResult(
            "wf-sync", False,
            "workflow directory missing",
            "  expected: " + ", ".join(missing),
        )

    drifted: list[str] = []
    problems: list[str] = []

    for name in _WORKFLOW_TEMPLATE_GUARDED:
        skill_path = os.path.join(skill_wf, name)
        live_path = os.path.join(live_wf, name)
        for path, label in ((skill_path, f"skill/hedl/workflows/{name}"),
                            (live_path, f".github/workflows/{name}")):
            real = os.path.realpath(path)
            if not os.path.isfile(real):
                problems.append(f"  missing or not a file: {label}")
                break
        else:
            try:
                skill_bytes = open(skill_path, "rb").read()
                live_bytes = open(live_path, "rb").read()
            except OSError as exc:
                problems.append(f"  unreadable: {exc}")
                continue
            if skill_bytes != live_bytes:
                drifted.append(name)

    if drifted or problems:
        detail = "\n".join(
            [f"  drifted: skill/hedl/workflows/{n} != .github/workflows/{n}" for n in drifted]
            + problems
        )
        return CheckResult(
            "wf-sync", False,
            f"{len(drifted)} drifted, {len(problems)} problem(s) in guarded workflow templates",
            detail,
        )

    return CheckResult(
        "wf-sync",
        True,
        f"guarded workflow templates in sync ({len(_WORKFLOW_TEMPLATE_GUARDED)} checked)",
    )


def check_commands() -> Optional[CheckResult]:
    """Detect stale hardcoded work-item IDs in .claude/commands/.

    An ID is stale if it does not appear in the configured backend's active or
    backlog items. Reads from local-file (work.json) or github-issues backend
    per context.json. Skips when no backend data is available.
    """
    commands_dir = os.path.join(_u.REPO_ROOT, ".claude", "commands")
    if not os.path.isdir(commands_dir):
        return None

    live_ids, load_err = _load_work_items()
    if load_err is not None:
        return CheckResult(
            "commands",
            False,
            f"cannot load work items: {load_err}",
        )
    if not live_ids and _state_backend() == "local-file":
        # local-file with no work.json — cannot validate; skip
        work_path = os.path.join(_u.REPO_ROOT, ".work", "work.json")
        if not os.path.exists(work_path):
            return None

    stale: list[str] = []
    id_pattern = re.compile(rf"\b{re.escape(_u._work_item_prefix())}-\d+\b")
    for fname in sorted(os.listdir(commands_dir)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(commands_dir, fname)
        with open(fpath, encoding="utf-8", errors="replace") as fh:
            for lineno, line in enumerate(fh, 1):
                for m in id_pattern.finditer(line):
                    item_id = m.group(0)
                    if item_id not in live_ids:
                        stale.append(f"  {fname}:{lineno}: {item_id} (not in backend)")

    if stale:
        return CheckResult(
            "commands",
            False,
            f"{len(stale)} stale work-item ID(s) in .claude/commands/",
            "\n".join(stale[:20]),
        )
    return CheckResult("commands", True, ".claude/commands/ has no stale work-item IDs")


_SEED_PLACEHOLDER = "EDIT ME"

# State files that contain EDIT ME placeholders in the seed template and must
# be fully resolved before an adopter's gate can pass.
_SEED_CHECKED_FILES = (
    "context.json",
    "work.json",
    "session.json",
    "phases/phase-0.json",
)


def check_seed_placeholders() -> Optional[CheckResult]:
    """Fail if any seeded .work/ state file still contains an EDIT ME placeholder.

    Returns None (skip) when .work/ does not exist (gate-only tier installs)
    or when running in the framework source repo (skill/hedl/ at repo root) —
    the framework's own .work/ legitimately references the placeholder token
    in prose descriptions of this very check.
    """
    work_dir = os.path.join(_u.REPO_ROOT, ".work")
    if not os.path.isdir(work_dir):
        return None
    if _u.is_framework_repo():
        return None  # framework source repo — skip

    real_work_dir = os.path.realpath(work_dir)
    hits: list[str] = []
    problems: list[str] = []
    for rel in _SEED_CHECKED_FILES:
        path = os.path.join(work_dir, rel)
        if not os.path.lexists(path):
            continue  # absent files are not a problem — adopter may not use them
        raw = _read_guarded(path, real_work_dir, ".work", rel, problems)
        if raw is None:
            continue
        if _SEED_PLACEHOLDER in raw.decode("utf-8", errors="replace"):
            hits.append(f"  .work/{rel} still contains '{_SEED_PLACEHOLDER}'")

    if hits or problems:
        lines = list(problems) + hits
        if hits:
            lines.append(
                "  Edit each file to replace all placeholder values, then re-run the gate.",
            )
        summary = []
        if hits:
            summary.append(f"{len(hits)} file(s) with unresolved placeholders")
        if problems:
            summary.append(f"{len(problems)} file(s) unreadable or escaped tree")
        return CheckResult(
            "seed",
            False,
            ", ".join(summary),
            "\n".join(lines),
        )
    return CheckResult("seed", True, f"no '{_SEED_PLACEHOLDER}' placeholders in seeded state files")


