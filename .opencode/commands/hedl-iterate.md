---
description: Run the Hedl work loop — implement active item, validate, drive to PR
agent: General
---

Run the Hedl work loop for the active work item:

1. Read `.work/work.json` active item and acceptance_criteria
2. Implement exactly what the criteria require — no more, no less
3. Run the gate: `python3 .github/scripts/am_i_done.py`
4. Fix any gate failures before proceeding
5. Run `/hedl-review` to convene adversarial review
6. Run `/hedl-pr` to drive to an operator-ready PR

One item at a time. Surgical changes only. Every changed line traces to the
active work item.
