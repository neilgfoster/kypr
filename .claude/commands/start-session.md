# /start-session

The SessionStart hook runs `.claude/startup.sh` automatically — its output is already
visible. This command provides the same orientation on demand.

1. Read CLAUDE.md — confirm you understand the current phase
2. Read the active work item from .work/work.json
3. State out loud: "I am working on [WORK-XXXX]: [title]. The acceptance criteria are: [list]"
4. Do not begin coding until you have stated the above
5. **Drift check** — if `skill/hedl/scripts/install.py` is present, run:

   ```bash
   python3 skill/hedl/scripts/install.py --doctor 2>&1
   ```

   - If output contains no DRIFT or MISSING lines and exit code is 0: silent (do not mention it).
   - If output contains DRIFT or MISSING lines: surface them and suggest
     re-running `python3 skill/hedl/scripts/install.py` to sync before starting work.
   - If the command exits non-zero (including `python3` not found): surface the full
     output and stop — do not skip silently.
   - If `skill/hedl/scripts/install.py` is not present: skip this step silently.

If startup.sh output is missing, read these files in order:

1. CLAUDE.md
2. .work/work.json (active item only)
3. .work/session.json

Do not summarise the project. Do not make a plan. Just confirm the active task and start.
