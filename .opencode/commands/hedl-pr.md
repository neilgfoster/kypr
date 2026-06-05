---
description: Drive branch to an operator-ready PR — gate, template, CI
agent: General
---

Drive the current branch to an operator-ready PR:

1. Run local gate: `python3 .github/scripts/am_i_done.py`
   Fix any failures before pushing.

2. Push and create/update PR using `gh pr create` (or `gh pr view` if exists).
   PR body must include: Summary, Work item, Type, Changes, Validation sections.

3. Run PR gate: `python3 .github/scripts/am_i_done.py --pr <PR_NUMBER>`
   This checks: template validity, unresolved threads, Dependabot alerts.

4. Poll CI: `python3 .github/scripts/am_i_done.py --pr <PR_NUMBER> --check ci`
   Wait for all matrix checks to pass.

5. Report PR state (checks, review verdict, open threads) and stop.
   Never merge — merging is the operator's decision.
