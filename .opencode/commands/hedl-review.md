---
description: Convene Hedl adversarial review panel using OpenCode's agents
agent: General
---

Convene Hedl's adversarial review panel. Use OpenCode's built-in agents
(General, Explore, Scout) as parallel reviewers for model diversity.

Steps:
1. Ask review-dispatcher to select the panel:
   "You are review-dispatcher. Read the diff and select the minimal panel
   from: scope-auditor, edge-case-hunter, security-auditor, determinism-auditor,
   historian, simplicity-enforcer, existential-challenger. Return a JSON object
   with a 'RUN' array."

2. Run each selected agent in parallel using OpenCode's multi-agent capabilities.
   Agent prompts are in `skill/hedl/references/review-library.md`.

3. Collect findings (BLOCKING / SIGNIFICANT / MINOR) and synthesise a verdict
   (PASS / CONDITIONAL / FAIL).

4. Fix all BLOCKING findings before proceeding to PR.
