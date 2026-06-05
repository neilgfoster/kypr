# devil-advocate — WORK-0007 review

**Run:** adversarial-review-2026-06-05-work-0007
**Model:** opus
**Commit:** e73239c

## Findings

| ID | Severity | Category | Finding | Status |
|----|----------|----------|---------|--------|
| DA1 | BLOCKING | requirements-deviation | requirements §3 demands deviations be "required", not preferred; original ADR-002 rationale was aesthetic | UPHELD — FIXED in f55f139: Context argues required-ness (no hedl functional location fits harness-neutral core; collision and adapter-boundary grounds) plus operator decision |
| DA2 | SIGNIFICANT | split-brain-state | Core under .kypr/ and adapter under .claude/ scatters Kypr state across two namespaces | UPHELD — FIXED in f55f139: stable-contract section owns the coupling explicitly |
| DA3 | SIGNIFICANT | fragile-path-coupling | Adapter hardcodes .kypr/scripts/verify_encryption.py — the mandatory encryption gate — across the namespace boundary | UPHELD — FIXED in f55f139: .kypr/scripts/* declared fixed public paths; breaking requires a superseding ADR |
| DA4 | SIGNIFICANT | rejected-option-strawman | hedl-fidelity argument used against one alternative cuts equally against .kypr/ | UPHELD — FIXED in f55f139: rejection grounds rewritten to collision + adapter-boundary; deviation owned, not denied |
| DA5 | SIGNIFICANT | git-crypt-leak-risk | Plaintext 'active' co-located with encrypted dirs invites glob misconfiguration | UPHELD — FIXED in f55f139: per-subdir explicit filter rules mandated; negation carve-outs forbidden |
| DA6 | MINOR | discoverability | Hiding security-critical scripts in a dotdir trades auditability for tidiness | NOTED — operator-chosen trade-off, alternatives were presented |
| DA7 | MINOR | premature-acceptance | ADR Accepted before dependents (WORK-0009/0011/0012/0013) exist | NOTED — phase-2 learning goals cover layout validation; revisit at phase close |
