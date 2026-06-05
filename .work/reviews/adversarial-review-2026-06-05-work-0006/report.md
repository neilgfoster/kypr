# Adversarial Review — WORK-0006 scaffold (architecture)

**Log:** adversarial-review-2026-06-05-work-0006
**Session:** in-session
**Depth:** Standard (4 agents + synthesis)
**Commit:** 30e1266 (chore/work-0006-scaffold-skill-kypr vs main)

## Verdict: PASS

Panel: scope-auditor, historian, new-engineer, security-auditor (dispatch-validated), synthesis

## Dimension Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| Scope | PASS | Scaffold-only; no logic smuggled in; bookkeeping as expected |
| Consistency | PASS | Layout matches ADR-001 and WORK-0006 description exactly |
| Security | PASS | Placeholders fail closed; no personal-data paths committed |
| Handoff clarity | PASS | Placeholders name their implementing WORK items |

## Strengths

- Placeholder Python files fail closed (exit 1) and name the implementing WORK item in their docstrings
- Directory structure matches the WORK-0006 description and ADR-001 exactly
- Both BLOCKING findings refuted deterministically (git ls-tree), not by argument

## Blocking Findings

| ID | Persona | Finding | Status |
|----|---------|---------|--------|
| H1 | [historian](historian.md) | adapters/claude-code/ and workspace-state/ missing from scaffold | WITHDRAWN — `git ls-tree -r 30e1266 -- skill/` lists both `.gitkeep` files; agents' scans missed dotfiles |
| S2 | [security-auditor](security-auditor.md) | Same claim as H1 | WITHDRAWN — same deterministic evidence |
| S1 | [security-auditor](security-auditor.md) | workspace-state/ scaffolded before .gitattributes (WORK-0013) | WITHDRAWN as blocking, downgraded to MINOR — constraint targets personal-data files, not empty keepfiles; WORK-0013 precedes any data |

## Significant Findings

| ID | Persona | Finding | Status |
|----|---------|---------|--------|
| N1 | [new-engineer](new-engineer.md) | SKILL.md has no owning work item despite phase-0.json:9 and hedl-study.md:28 naming it the non-Claude-Code routing table | UPHELD as backlog gap — out of diff scope; address before /phase-complete |
| H2 | [historian](historian.md) | projections.json is `[]`, contradicts ADR-001 | WITHDRAWN — owned by WORK-0007 AC |
| H3 | [historian](historian.md) | Ambiguity over who creates settings.json/startup.sh | WITHDRAWN — WORK-0011 AC explicit |
| S3 | [security-auditor](security-auditor.md) | install.py placeholder lacks verify_encryption call-site marker | DOWNGRADED to MINOR — owned by WORK-0009 AC |
| S4 | [security-auditor](security-auditor.md) | Pre-existing ReDoS in check_pr_template.py | OUT OF SCOPE — tracked as WORK-0014 |
| S5 | [security-auditor](security-auditor.md) | projections.json lacks schema/containment expression | WITHDRAWN — owned by WORK-0009 AC |

## Minor Findings

| ID | Persona | Finding | Status |
|----|---------|---------|--------|
| N2 | [new-engineer](new-engineer.md) | projections.json `[]` carries no placeholder marker (JSON limitation) | NOTED — WORK-0007 is a hard dependency of WORK-0009 |
| N3 | [new-engineer](new-engineer.md) | plugin.json version 0.0.1 reads as a real release | NOTED — WORK-0007 owns metadata |
| S6 | [security-auditor](security-auditor.md) | Placeholder stderr embeds WORK item IDs | NOTED — acceptable |
| S7 | [security-auditor](security-auditor.md) | No .gitignore defence-in-depth for workspace-state/ | NOTED — optional hardening before WORK-0012 |

## Next Actions

- [x] PASS — proceed; scaffold meets both acceptance criteria
- [ ] Before /phase-complete: file a backlog item for SKILL.md or record an explicit deferral note (N1)
- [ ] Optional hardening before WORK-0012: .gitattributes/.gitignore defence-in-depth for workspace-state/
