---
name: pearde-memo
description: Record a decision the code will not explain, and check the ones on record — one file per call, holding what was decided, what it beat, and why, never buried in a PRD. Slugged from the subject, with a closed set of frontmatter keys that a checker enforces. Use for "/memo", "memo <subject>", "record this decision", "write this down as a decision", "why did we choose X", "what did we decide about Y", "check the memos", "adr", "decision record", "document this tradeoff". Write it when the call is made, not when the work lands.
---

Read @references/parts/memos.md for when one is owed, @references/memo.md for
the format and the closed frontmatter set, @references/templates/memo.md for
the file. The scope is `@@memos`.

```bash
python3 @resources/pearde.py memo list [board]    # slug · kind · status · date · subject
python3 @resources/pearde.py memo add <subject>   # a new memo, slugged from the subject
python3 @resources/pearde.py memo check [board]   # what doctor reports for `memos`
```

`memo` forwards to @resources/memos.py, the only reader of that format.

Write one at the moment the call is made, not when the work lands: a memo
exists because a future reader will ask "why is it like this" and the code
will not answer.

Memos live at `prds/memos/`, so a board is needed to file one. With none in
scope, write the memo and say where it should go.
