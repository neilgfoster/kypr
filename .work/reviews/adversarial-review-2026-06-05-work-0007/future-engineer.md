# future-engineer — WORK-0007 review

**Run:** adversarial-review-2026-06-05-work-0007
**Model:** opus
**Commit:** e73239c

## Findings

| ID | Severity | Category | Finding | Status |
|----|----------|----------|---------|--------|
| FE1 | BLOCKING | schema-expressiveness | {source, target} schema cannot express overwrite vs copy-once semantics needed by .work/ and workspace-state/ | UPHELD — FIXED in f55f139: manifest = overwrite-always file copies only; copy-once state out-of-band with named install.py exceptions |
| FE2 | BLOCKING | manifest-completeness | ADR-002 Consequence 3 claimed manifest completeness, contradicting ADR-001 §5 .work/ init handling | UPHELD — FIXED in f55f139: "complete list of copied files; not the complete list of installer actions" |
| FE3 | SIGNIFICANT | path-semantics | Relative-path bases for source/target never stated | UPHELD — FIXED in f55f139: source relative to skill/kypr/, target relative to target repo root; containment + '..' rejection |
| FE4 | SIGNIFICANT | directory-vs-file | Directory projection semantics undefined | UPHELD — FIXED in f55f139: entries name files only; workspace-state skeleton is an out-of-band step |
| FE5 | SIGNIFICANT | ordering-trap | WORK-0009 ships against a deliberately incomplete manifest; install passes its own AC but is non-functional | UPHELD — FIXED in f55f139: Consequence 3 states the gap; full-install verification assigned to the last structural item |
| FE6 | MINOR | schema-versioning | Bare top-level array, no version marker | NOTED — deliberate, per ADR-001 flat-array decision |
| FE7 | MINOR | metadata-leak-risk | 'active' file content unconstrained; could accrete personal data | UPHELD — FIXED in f55f139: constrained to a single workspace identifier token |
