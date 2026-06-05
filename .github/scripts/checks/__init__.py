"""checks/ package — re-exports all public check functions.

Existing callers that import from am_i_done (the thin dispatcher) continue
to work unchanged because am_i_done.py re-exports everything from here.
"""
from checks._util import (  # noqa: F401,I001
    CheckResult, Report, REPO_ROOT, run, _hedl_version,
    _work_item_prefix, _load_hedl_config, _get_gate_timeout,
    _VERIFY_DEFAULT_ALLOWLIST, _VERIFY_DENYLIST, _SHELL_METACHARS,
    _verify_allowlist, _run_declared_check,
)
from checks._state import (  # noqa: F401,I001
    _work_item_id_re, _state_backend, _load_work_items,
    _load_work_items_local, _load_work_items_github, _GITHUB_ISSUE_READ_LIMIT,
)
from checks.git import check_git, check_branch, BRANCH_PATTERN, VALID_PREFIXES  # noqa: F401,I001
from checks.dispatch import (  # noqa: F401,I001
    check_dispatch, _load_dispatch_rules, _get_changed_files, _required_agents,
    _DISPATCH_RULES_FILE,
)
from checks.config import (  # noqa: F401,I001
    check_config, check_state_template_sync,
    check_workflow_template_sync, check_commands,
    check_seed_placeholders,
)
from checks.markdown import (  # noqa: F401,I001
    check_markdown_schemas, check_markdown, _pymarkdown_cmd,
    _SCHEMA_VALIDATOR, _SCHEMAS_FILE,
)
from checks.quality import check_lint, check_types, check_tests  # noqa: F401,I001
from checks.pr import (  # noqa: F401,I001
    check_dependabot, check_pr_threads, check_template, check_ci,
    _should_poll_ci, _DEPENDABOT_LOGINS, _GH_AUTH_HINTS, _GH_RATE_HINTS,
)
from checks.docs import (  # noqa: F401,I001
    check_streams, check_skill_metadata, check_docs_index,
    check_doc_generated_facts, _word_or_int, _count_command_behaviours,
)

__all__ = [
    "CheckResult",
    "Report",
    "REPO_ROOT",
    "run",
    "_hedl_version",
    "_work_item_prefix",
    "_load_hedl_config",
    "_get_gate_timeout",
    "_VERIFY_DEFAULT_ALLOWLIST",
    "_VERIFY_DENYLIST",
    "_SHELL_METACHARS",
    "_verify_allowlist",
    "_run_declared_check",
    "_work_item_id_re",
    "_state_backend",
    "_load_work_items",
    "_load_work_items_local",
    "_load_work_items_github",
    "_GITHUB_ISSUE_READ_LIMIT",
    "check_git",
    "check_branch",
    "BRANCH_PATTERN",
    "VALID_PREFIXES",
    "check_dispatch",
    "_load_dispatch_rules",
    "_get_changed_files",
    "_required_agents",
    "_DISPATCH_RULES_FILE",
    "check_config",
    "check_state_template_sync",
    "check_workflow_template_sync",
    "check_commands",
    "check_seed_placeholders",
    "check_markdown_schemas",
    "check_markdown",
    "_pymarkdown_cmd",
    "_SCHEMA_VALIDATOR",
    "_SCHEMAS_FILE",
    "check_lint",
    "check_types",
    "check_tests",
    "check_dependabot",
    "check_pr_threads",
    "check_template",
    "check_ci",
    "_should_poll_ci",
    "_DEPENDABOT_LOGINS",
    "_GH_AUTH_HINTS",
    "_GH_RATE_HINTS",
    "check_streams",
    "check_skill_metadata",
    "check_docs_index",
    "check_doc_generated_facts",
    "_word_or_int",
    "_count_command_behaviours"
]
