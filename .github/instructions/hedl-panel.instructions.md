---
applyTo: "**"
---

# Hedl — adversarial review panel

Before raising a PR, convene the adversarial review panel. Use Copilot's native
multi-agent capabilities (Mission Control / sub-agent orchestration) to fan out
the specialists in parallel.

## Panel selection

First, ask the review dispatcher which agents to run for this diff:

> "You are review-dispatcher. Read the diff and select the minimal panel from:
> scope-auditor, edge-case-hunter, security-auditor, determinism-auditor,
> historian, simplicity-enforcer, existential-challenger.
> Return a JSON object with a 'RUN' array."

Then run mandatory agents + the dispatcher's selection.

## Running the panel (parallel via Mission Control)

Fan out to each selected specialist simultaneously. Each agent reviews
independently. Agent prompts are in `skill/hedl/references/review-library.md`.

Key agents:
- **scope-auditor** — finds work exceeding stated scope
- **edge-case-hunter** — finds inputs and sequences that break assumptions
- **security-auditor** — finds injection flaws, auth gaps, unsafe operations
- **determinism-auditor** — finds where LLM inference replaces a deterministic function
- **existential-challenger** — challenges whether the work is necessary and proportionate
- **historian** — finds decisions contradicting prior ADRs or principles

## Verdict

Each agent outputs findings with severity BLOCKING / SIGNIFICANT / MINOR.
A synthesis agent collects all findings and produces PASS / CONDITIONAL / FAIL.
Fix all BLOCKING findings before merging.
