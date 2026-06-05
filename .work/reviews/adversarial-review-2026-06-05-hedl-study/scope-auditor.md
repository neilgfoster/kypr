# scope-auditor — hedl-study review 2026-06-05

## Findings

| Severity | Finding | Evidence | Status |
|----------|---------|----------|--------|
| SIGNIFICANT | "What Kypr may adapt" section contained prescriptive design recommendations ("Kypr may choose", "can be simpler") — these belong in ADR-001, not a study | docs/hedl-study.md §7 "What Kypr may adapt" | Fixed — reframed as "Observations for ADR-001" |
| MINOR | §3.1 missing explanation of how tier inheritance is resolved at install time | docs/hedl-study.md §3.1 | Fixed — added inheritance resolution note |
| MINOR | §3.2 missing explanation of why os.path.relpath() matters for symlink portability | docs/hedl-study.md §3.2 | Fixed — added portability note |
