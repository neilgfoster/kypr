# historian — ADR-001 review 2026-06-05

## Findings

| Severity | Finding | Evidence | Status |
|----------|---------|----------|--------|
| SIGNIFICANT | Installer manifest format left ambiguous between "plain list or minimal JSON" and "embedded in install.py" | ADR-001 Consequences §1 vs §3 | Fixed — resolved to projections.json flat JSON array |
| SIGNIFICANT | WORK-0005 description listed adapters.json as phase 2 deliverable, contradicting ADR-001 §3 decision (no adapters.json) | .work/work.json WORK-0005 description vs ADR-001 §3 | Fixed — WORK-0005 description updated to reference adapters/claude-code/ |
| MINOR | ADR-001 did not state whether install.py must verify git-crypt before projecting (load-bearing requirement per requirements.md §2) | ADR-001 Consequences §1; requirements.md §2; hedl-study.md §7 open question 5 | Fixed — install.py git-crypt check made explicit in Consequences §1 and resolved questions table |
