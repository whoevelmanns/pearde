---
name: pearde-doctor
description: Tell a broken install from an absent one, and repair what is unambiguous — one line per part, each ok, off, or broken, with the exact command that fixes it. Checks the skill files parse, the index matches the tree, the status line renders, the board is on its contract path, memos parse, the view is watching, and a master board's members are on disk. Use for "/doctor", "is this wired up", "why is nothing happening", "check the install", "pearde is not working", "diagnose", "health check", "fix the install", "the status line is blank", "the skill never fires".
---

Read @references/parts/doctor.md. The scope is `@@doctor`. That file is the
part table — what each row's `off` and `broken` mean, which of them `--fix`
touches, and why no agent is named anywhere in the check. None of it is
repeated here.

```bash
python3 @resources/pearde.py doctor [board]              # report; exit 1 when a part is broken
python3 @resources/pearde.py doctor --fix [board]        # report, then repair
python3 @resources/pearde.py doctor --harnesses [board]  # …and run the board's harnesses
```

Print every line it returns. A part that reads `off` is not a problem to
solve unless the user wanted that part.
