---
name: pearde-doctor
description: Tell a broken install from an absent one, and repair what is unambiguous — one line per part, each ok, off, or broken, with the exact command that fixes it. Checks the skill files parse, the index matches the tree, the status line renders, the board is on its contract path, memos parse, the view is watching, and a master board's members are on disk. Use for "/doctor", "is this wired up", "why is nothing happening", "check the install", "pearde is not working", "diagnose", "health check", "fix the install", "the status line is blank", "the skill never fires".
---

Read @references/parts/doctor.md. The scope is `@@doctor`.

```bash
python3 @resources/pearde.py doctor [board]         # report; exit 1 when a part is broken
python3 @resources/pearde.py doctor --fix [board]   # report, then repair
```

- **An install that is present and broken looks exactly like one that is
  absent.** That is the whole reason this exists: `off` means installed
  nowhere and nothing to repair, `broken` means installed and not working.
- **No agent is named, and none is looked for.** Where a skill folder goes
  and where a status line is wired are the reader's setup, and
  @references/install.md is that step. Doctor checks what is true regardless.
- `--fix` repairs one thing: a view service down or not watching this board.
  It never writes a settings file.
- `index` is never `--fix`-able — which row a new file belongs in is a
  judgement, not a repair.

Print every line it returns. A part that reads `off` is not a problem to
solve unless the user wanted that part.
