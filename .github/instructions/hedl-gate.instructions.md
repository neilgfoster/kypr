---
applyTo: "**"
---

# Hedl — completion gate

Before declaring any task complete, run the gate:

```sh
python3 .github/scripts/am_i_done.py
```

For PR checks (adds template, threads, CI, Dependabot):

```sh
python3 .github/scripts/am_i_done.py --pr <PR_NUMBER>
```

The gate exits `0` when done. Non-zero means not done — fix what it reports,
never claim done on a red gate.

The gate is deterministic (stdlib Python, no inference). It checks: clean tree,
branch naming, PR-template validity, stale work-item IDs, lint, types, tests,
unresolved review threads, Dependabot alerts. CI runs a superset via `--pr`.

Customise for your stack via `hedl.toml`:

```toml
[verify]
lint  = "golangci-lint run"
types = "tsc --noEmit"
test  = "go test ./..."
```
