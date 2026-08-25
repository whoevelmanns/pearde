---
name: memo
description: Record a decision the code will not explain, and check the ones on record — one file per call, holding what was decided, what it beat, and why, never buried in a PRD. Slugged from the subject, with a closed set of frontmatter keys that a checker enforces. Use for "/memo", "memo <subject>", "record this decision", "write this down as a decision", "why did we choose X", "what did we decide about Y", "check the memos", "adr", "decision record", "document this tradeoff". Write it when the call is made, not when the work lands.
---

Read @references/memo.md for the format, @references/parts/memos.md for when
one is owed. The scope is `@@memos`.

- **A decision, not a status.** A memo exists because a future reader will
  ask "why is it like this" and the code will not answer. Work that merely
  happened does not get one.
- **What it beat is the memo.** The option not taken, and the reason, is the
  half that carries information. A memo naming only the winner is a label.
- **One file, slugged from the subject** — lowercase, spaces to hyphens. The
  slug is both the filename and the `memo:` key, and `doctor` fails when they
  disagree. @references/templates/memo.md is the shape.
- `python3 @resources/memos.py check <board>` reads them — the only reader of
  that format. `list` and `show` are the other two verbs.

Memos live at `prds/memos/`, so a board is needed to file one. With none in
scope, write the memo and say where it should go.
