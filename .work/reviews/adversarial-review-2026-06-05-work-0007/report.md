# Adversarial Review — WORK-0007 (plugin.json, projections.json, ADR-002)

**Log:** adversarial-review-2026-06-05-work-0007
**Session:** in-session
**Depth:** Standard (4 agents + synthesis, 1 fix cycle)
**Commit:** e73239c reviewed; fixes verified at f55f139

## Verdict: PASS

Panel: scope-auditor, historian, future-engineer, devil-advocate (dispatch-validated), synthesis

## Dimension Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| Scope | PASS | ADR-002 judged necessary scope; two cosmetic notes |
| Consistency | PASS | After fix: deviation from hedl explicitly documented per requirements §3 |
| Contract durability | PASS | After fix: manifest semantics, path bases, copy-once exceptions, stable gate path all defined |
| Security | PASS | After fix: per-subdir filter rules mandated; 'active' constrained to identifier token |

## Strengths

- Operator decision on target layout captured as an ADR rather than made implicitly
- Fix cycle converted three BLOCKING contract gaps into explicit, written semantics before any consumer (install.py) exists
- DA1/H1 cross-persona convergence caught a genuine requirements §3 compliance gap

## Blocking Findings

| ID | Persona | Finding | Status |
|----|---------|---------|--------|
| FE1 | [future-engineer](future-engineer.md) | Schema cannot express overwrite vs copy-once | UPHELD — FIXED (f55f139) |
| FE2 | [future-engineer](future-engineer.md) | Manifest-completeness claim contradicted ADR-001 §5 | UPHELD — FIXED (f55f139) |
| DA1 | [devil-advocate](devil-advocate.md) | .kypr/ deviation not justified as "required" per requirements §3 | UPHELD — FIXED (f55f139) |

## Significant Findings

| ID | Persona | Finding | Status |
|----|---------|---------|--------|
| H1 | [historian](historian.md) | Deviation from hedl model not explicitly identified | UPHELD — FIXED (f55f139) |
| FE3 | [future-engineer](future-engineer.md) | Path bases undefined | UPHELD — FIXED (f55f139) |
| FE4 | [future-engineer](future-engineer.md) | Directory projection semantics undefined | UPHELD — FIXED (f55f139) |
| FE5 | [future-engineer](future-engineer.md) | Ordering trap: mechanically-correct, non-functional install mid-phase | UPHELD — FIXED (f55f139) |
| DA2 | [devil-advocate](devil-advocate.md) | Split-brain .kypr/ vs .claude/ namespaces | UPHELD — FIXED (f55f139) |
| DA3 | [devil-advocate](devil-advocate.md) | Hardcoded cross-namespace encryption-gate path | UPHELD — FIXED (f55f139) |
| DA4 | [devil-advocate](devil-advocate.md) | Rejected-options reasoning inconsistent | UPHELD — FIXED (f55f139) |
| DA5 | [devil-advocate](devil-advocate.md) | Plaintext 'active' co-located with encrypted dirs | UPHELD — FIXED (f55f139) |

## Minor Findings

| ID | Persona | Finding | Status |
|----|---------|---------|--------|
| SA1 | [scope-auditor](scope-auditor.md) | ADR-002 not listed in WORK-0007 AC | NOTED — necessary scope |
| SA2 | [scope-auditor](scope-auditor.md) | Branch name omits the ADR | NOTED — flagged in PR |
| H2 | [historian](historian.md) | References omitted hedl-study.md | FIXED (f55f139) |
| FE6 | [future-engineer](future-engineer.md) | No schema version marker | NOTED — deliberate per ADR-001 |
| FE7 | [future-engineer](future-engineer.md) | 'active' content unconstrained | FIXED (f55f139) |
| DA6 | [devil-advocate](devil-advocate.md) | Dotdir auditability trade-off | NOTED — operator-chosen |
| DA7 | [devil-advocate](devil-advocate.md) | ADR Accepted before dependents exist | NOTED — revisit at phase close |

## Synthesis

Synthesis agent read the committed ADR-002 at f55f139 and verified every claimed
fix against specific section text (Decision deviation statement, Manifest
semantics, Encryption-gate stable contract, Consequence 2 filter rules,
Consequence 3 ordering note, References). No BLOCKING or SIGNIFICANT finding
remains unfixed. Verdict PASS after one fix cycle.

## Next Actions

- [x] All BLOCKING and SIGNIFICANT findings fixed in f55f139
- [ ] Before /phase-complete: optionally backfill ADR-002 into WORK-0007 AC record (SA1)
- [ ] At phase close: confirm WORK-0009/0011/0012 validated the .kypr/ layout before treating ADR-002 as load-bearing downstream (DA7)
