from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Optional

import checks._util as _u
from checks._util import CheckResult

_DOCS_SCRIPTS_DIR = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
_GEN_METADATA = os.path.join(os.path.dirname(_DOCS_SCRIPTS_DIR), "gen_skill_metadata.py")


def check_streams(streams: list[str]) -> CheckResult:
    """Validate no file overlap across parallel worktree streams.

    Each stream is a branch name. The check diffs each branch against main
    (three-dot ``main...branch`` — the branch's own changes since its
    merge-base; falling back to ``origin/main`` when local ``main`` is absent,
    e.g. a fresh CI checkout) and REFUSES — exit code 1 — if any file is
    touched by more than one stream.

    Refusal behaviour (intentionally conservative, pre-merge):

    - Overlap is detected at FILE granularity, not line granularity: two
      streams editing different lines of the same file still refuse. This is a
      merge-safety floor — it stops two parallel operators silently racing the
      same file — not a textual-conflict predictor.
    - A branch that cannot be diffed against either ``main`` or ``origin/main``
      FAILS the check (a missing or mistyped stream is surfaced, not skipped).
    - Duplicate branch names are de-duplicated up front, so passing the same
      stream twice is one stream (no self-overlap, no redundant diff).

    Gate-only installs that don't use parallel worktrees never pass --streams,
    so this check never runs for them.
    """
    if not streams:
        return CheckResult("streams", True, "no parallel streams specified")

    # Dedupe up front (order-preserving): a branch listed twice is one stream,
    # so this avoids a redundant git diff per duplicate and prevents any
    # false self-overlap regardless of how owners are later tallied.
    streams = list(dict.fromkeys(streams))

    stream_files: dict[str, list[str]] = {}
    for branch in streams:
        code, out, err = _u.run(["git", "diff", f"main...{branch}", "--name-only"])
        if code != 0:
            code, out, _ = _u.run(["git", "diff", f"origin/main...{branch}", "--name-only"])
            if code != 0:
                return CheckResult(
                    "streams", False,
                    f"could not diff stream '{branch}' against main",
                    (err or "").strip()[:200],
                )
        stream_files[branch] = [f.strip() for f in out.splitlines() if f.strip()]

    file_owners: dict[str, list[str]] = {}
    for branch, files in stream_files.items():
        for f in files:
            file_owners.setdefault(f, []).append(branch)

    conflicts = {f: owners for f, owners in file_owners.items() if len(owners) > 1}
    if conflicts:
        lines = [
            f"  {f}: {', '.join(sorted(owners))}"
            for f, owners in sorted(conflicts.items())[:20]
        ]
        return CheckResult(
            "streams", False,
            f"{len(conflicts)} file(s) touched by multiple streams — parallel writes not allowed",
            "\n".join(lines),
        )

    total = sum(len(fs) for fs in stream_files.values())
    return CheckResult(
        "streams", True,
        f"{len(streams)} stream(s) clean, {total} total file(s) changed, no overlap",
    )


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
                        "git", "branch", "dispatch", "config", "state-sync", "commands",
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


def check_skill_metadata() -> Optional[CheckResult]:
    """Check that SKILL.md's generated section matches script --schema output."""
    if not os.path.exists(_GEN_METADATA):
        return None  # not in skill dev context — skip gracefully

    code, out, err = _u.run([sys.executable, _GEN_METADATA, "--check"])
    if code == 0:
        return CheckResult("skill-meta", True, "SKILL.md deterministic section is up to date")

    combined = (out + err).strip()
    lines = combined.splitlines()[:20]
    return CheckResult(
        "skill-meta",
        False,
        "SKILL.md deterministic section is stale or has invalid references",
        "\n".join(lines),
    )


def check_docs_index() -> Optional[CheckResult]:
    """Fail if any human-facing markdown doc is not reachable by link from README.md.

    Scope: docs/**/*.md, skill/hedl/references/*.md, skill/hedl/SKILL.md, CHANGELOG.md.
    Symlinks are resolved (os.path.realpath) so a docs/ symlink covering a references/
    file counts as one entry -- linking either path satisfies both.
    Operational trees (.github/, .claude/, .work/, skill/hedl/agents|commands|templates|
    workflows|scripts|integrations) are excluded.

    Returns None (skip) in adopter repos (skill under .claude/skills/, no skill/hedl/
    at the repo root) — the docs-reachability invariant is framework-self only. The
    lightweight tier projects docs/spec/*-template.md into an adopter's docs/, which
    their README does not link; enforcing reachability there would red-light a fresh
    adopter's first gate run (WORK-0061). Same framework-repo guard as
    check_state_template_sync.
    """
    if not _u.is_framework_repo():
        return None  # adopter repo layout — docs-index is a framework-self invariant

    readme_path = os.path.join(_u.REPO_ROOT, "README.md")
    if not os.path.exists(readme_path):
        return CheckResult("docs-index", False, "README.md not found")

    with open(readme_path, encoding="utf-8") as fh:
        readme_text = fh.read()

    _link_re = re.compile(r"\[(?:[^\]]*)\]\(([^)]+)\)")
    linked_real: set[str] = set()
    for m in _link_re.finditer(readme_text):
        href = m.group(1).split("#")[0].strip()
        if not href or href.startswith(("http://", "https://", "mailto:")):
            continue
        abs_path = os.path.normpath(os.path.join(_u.REPO_ROOT, href))
        if os.path.exists(abs_path):
            linked_real.add(os.path.realpath(abs_path))

    in_scope: list[str] = []
    docs_dir = os.path.join(_u.REPO_ROOT, "docs")
    if os.path.isdir(docs_dir):
        for dirpath, _dirs, filenames in os.walk(docs_dir):
            for fn in sorted(filenames):
                if fn.endswith(".md"):
                    in_scope.append(os.path.join(dirpath, fn))
    refs_dir = os.path.join(_u.REPO_ROOT, "skill", "hedl", "references")
    if os.path.isdir(refs_dir):
        for fn in sorted(os.listdir(refs_dir)):
            if fn.endswith(".md"):
                in_scope.append(os.path.join(refs_dir, fn))
    skill_md = os.path.join(_u.REPO_ROOT, "skill", "hedl", "SKILL.md")
    if os.path.exists(skill_md):
        in_scope.append(skill_md)
    changelog = os.path.join(_u.REPO_ROOT, "CHANGELOG.md")
    if os.path.exists(changelog):
        in_scope.append(changelog)

    orphans: list[str] = []
    seen_real: set[str] = set()
    for doc in in_scope:
        real = os.path.realpath(doc)
        if real in seen_real:
            continue
        seen_real.add(real)
        if real not in linked_real:
            orphans.append("  " + os.path.relpath(doc, _u.REPO_ROOT))

    if orphans:
        return CheckResult(
            "docs-index",
            False,
            f"{len(orphans)} doc(s) not linked from README.md",
            "\n".join(orphans),
        )
    return CheckResult("docs-index", True, "all human-facing docs reachable from README.md")


# Source-derived documentation facts (WORK-0028)
# ---------------------------------------------------------------------------
# Counts and names that docs assert must derive from the filesystem / config,
# not be hand-maintained. This is the standing drift-detector: any doc fact with
# a deterministic source is enumerated here and checked verbatim — no inference
# (ADR-003). Modelled on check_skill_metadata (a single source of truth governs
# what shipped docs may claim). Skips when the source tree is absent (gate-only
# adopter installs ship am_i_done.py but not skill/hedl/).

_NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}


def _word_or_int(token: str) -> Optional[int]:
    token = token.strip().lower()
    if token.isdigit():
        return int(token)
    return _NUMBER_WORDS.get(token)


def _count_command_behaviours(text: str) -> int:
    """Count `## ` command-behaviour headings in commands.md, excluding any that
    sit inside fenced code blocks (e.g. the ADR template shown under new-decision).
    Fence-aware rather than name-matched so renaming/adding an example heading, or
    a real command sharing a template heading's name, cannot miscount."""
    in_fence = False
    n = 0
    for line in text.splitlines():
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        # CommonMark fence: ``` or ~~~ with at most 3 spaces of indent (4+ is an
        # indented code block, not a fence).
        if indent <= 3 and (stripped.startswith("```") or stripped.startswith("~~~")):
            in_fence = not in_fence
            continue
        if not in_fence and line.startswith("## "):
            n += 1
    return n


def check_doc_generated_facts() -> Optional[CheckResult]:
    """Fail when a documentation count/name diverges from its filesystem source.

    Authoritative sources: skill/hedl/agents/*.md (core agents), tiers.json
    (tiers), and the `##` command-behaviour headings in commands.md (outside code
    fences). Returns None (skip) outside the Hedl source tree.
    """
    agents_dir = os.path.join(_u.REPO_ROOT, "skill", "hedl", "agents")
    if not os.path.isdir(agents_dir):
        return None  # not the Hedl source tree

    agent_names = sorted(f[:-3] for f in os.listdir(agents_dir) if f.endswith(".md"))
    n_agents = len(agent_names)

    failures: list[str] = []

    # Inside the source tree (agents/ present) the sibling sources must exist and
    # parse — a missing or corrupt source is a FAIL, not a silent skip, so the
    # detector can never report PASS without the authority it checks against.
    n_tiers: Optional[int] = None
    tiers_path = os.path.join(_u.REPO_ROOT, "skill", "hedl", "tiers.json")
    if not os.path.exists(tiers_path):
        failures.append("  skill/hedl/tiers.json: missing (expected in source tree)")
    else:
        try:
            with open(tiers_path, encoding="utf-8") as fh:
                n_tiers = len(json.load(fh).get("tiers", {}))
        except (json.JSONDecodeError, OSError) as exc:
            failures.append(f"  skill/hedl/tiers.json: unreadable/invalid ({exc})")

    n_behaviours: Optional[int] = None
    commands_md = os.path.join(_u.REPO_ROOT, "skill", "hedl", "references", "commands.md")
    if not os.path.exists(commands_md):
        failures.append("  skill/hedl/references/commands.md: missing (expected in source tree)")
    else:
        try:
            with open(commands_md, encoding="utf-8") as fh:
                n_behaviours = _count_command_behaviours(fh.read())
        except OSError as exc:
            failures.append(f"  skill/hedl/references/commands.md: unreadable ({exc})")

    def _check_number(relpath: str, pattern: str, expected: int, what: str) -> None:
        path = os.path.join(_u.REPO_ROOT, relpath)
        if not os.path.exists(path):
            return
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        # A doc that does not state the fact makes no claim to verify — only a
        # stated-but-wrong value is drift. Every stated form is checked, so the
        # same count written two ways (e.g. "all 7 core agents" and "(core 7)")
        # is each verified.
        for m in re.finditer(pattern, text):
            if _word_or_int(m.group(1)) != expected:
                failures.append(f"  {relpath}: {what} says {m.group(1)!r}, source has {expected}")

    # Core-agent count (current reality = filesystem count). Both the prose form
    # and the parenthetical "(core N)" form in commands.md are checked.
    _check_number("skill/hedl/references/review-library.md",
                  r"(\w+) core agents live as named", n_agents, "core-agent count")
    _check_number("skill/hedl/references/agents.md",
                  r"(\w+) core agents live as named", n_agents, "core-agent count")
    _check_number("skill/hedl/references/commands.md",
                  r"all (\d+) core agents", n_agents, "core-agent count")
    _check_number("skill/hedl/references/commands.md",
                  r"\(core (\d+)\)", n_agents, "core-agent count")
    # Every agent file must be named (whole-word) in review-library.md.
    rl = os.path.join(_u.REPO_ROOT, "skill", "hedl", "references", "review-library.md")
    if os.path.exists(rl):
        with open(rl, encoding="utf-8") as fh:
            rl_text = fh.read()
        missing = [a for a in agent_names if not re.search(rf"\b{re.escape(a)}\b", rl_text)]
        if missing:
            failures.append(f"  review-library.md: agent(s) not named: {', '.join(missing)}")
    # Command-behaviour count (anchored to the summary sentence) and tier count.
    if n_behaviours is not None:
        _check_number("skill/hedl/references/tiers.md",
                      r"All (\d+) command behaviors", n_behaviours, "command-behaviour count")
    if n_tiers is not None:
        _check_number("skill/hedl/references/tiers.md",
                      r"(\w+) tiers[^\n]*drop in", n_tiers, "tier count")

    # Citation-freshness: file:line citations in alternatives.md must not exceed the
    # actual file's line count. Pattern: `path/to/file.py:NNN` or `:NNN-MMM`.
    # Only checks citations against files that exist in the source tree.
    alt_path = os.path.join(_u.REPO_ROOT, "docs", "alternatives.md")
    if os.path.isfile(alt_path):
        with open(alt_path, encoding="utf-8") as fh:
            alt_text = fh.read()
        cite_re = re.compile(r"`([^`]+\.py):(\d+)(?:-(\d+))?`")
        line_cache: dict[str, int] = {}
        for m in cite_re.finditer(alt_text):
            rel, start_s, end_s = m.group(1), m.group(2), m.group(3)
            # Resolve relative to _u.REPO_ROOT; accept either skill/hedl/... or bare name
            candidates = [
                os.path.join(_u.REPO_ROOT, rel),
                os.path.join(_u.REPO_ROOT, "skill", "hedl", "scripts", os.path.basename(rel)),
            ]
            resolved = next((c for c in candidates if os.path.isfile(c)), None)
            if resolved is None:
                continue
            if resolved not in line_cache:
                try:
                    with open(resolved, encoding="utf-8") as fh:
                        line_cache[resolved] = sum(1 for _ in fh)
                except OSError:
                    continue
            total = line_cache[resolved]
            for line_s in ([start_s] + ([end_s] if end_s else [])):
                line_n = int(line_s)
                if line_n > total:
                    failures.append(
                        f"  docs/alternatives.md: citation `{rel}:{m.group(2)}"
                        f"{'-%s' % end_s if end_s else ''}` line {line_n} "
                        f"exceeds {os.path.basename(resolved)} ({total} lines)"
                    )
                    break

    if failures:
        return CheckResult("doc-facts", False,
                           "documentation facts diverge from their filesystem source",
                           "\n".join(failures))
    return CheckResult(
        "doc-facts", True,
        f"doc facts match source ({n_agents} agents, {n_tiers} tiers, {n_behaviours} command behaviours)",
    )


