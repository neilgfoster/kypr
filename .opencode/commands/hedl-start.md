---
description: Orient at session start — load active work item and phase context
agent: General
---

Read `.work/work.json` and report:
1. Current phase (meta.current_phase)
2. Active item ID and title (meta.active_item)
3. The active item's acceptance_criteria (list each criterion)
4. Last session notes from `.work/session.json`

If no active item, list the top 3 backlog items by priority_band.
Do not start implementing — just orient.
