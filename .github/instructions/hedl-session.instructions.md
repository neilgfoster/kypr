---
applyTo: "**"
---

# Hedl — session and work-item discipline

## One item at a time

Check `.work/work.json` → `meta.active_item` for what is being worked on.
Do not start a new item until the active one is committed and its PR is open.

## Surgical changes

Touch only files the work item requires. Match existing style. Do not
clean up adjacent code that isn't broken. Every changed line should trace
to the active work item.

## Define the check first

Before implementing, confirm what passing looks like:
- What does the gate need to report `0`?
- What acceptance criteria are listed in the work item?

## Loop

1. Orient: read `.work/work.json` active item + acceptance criteria
2. Implement exactly what the criteria require — no more
3. Run the gate: `python3 .github/scripts/am_i_done.py`
4. Run adversarial review (see `hedl-panel.instructions.md`)
5. Commit and drive to PR

## Work-item state

Work items live in `.work/work.json` under `active`, `backlog`, `completed`.
Do not edit `.work/` state files directly — they are managed by the workflow.
