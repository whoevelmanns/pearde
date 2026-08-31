---
state: done
origin: derived
actual: 1.6h
commit: 34a2a37
from: a-parked-prd-comes-back
priority: 66
complexity: 36
blast-radius: high
repo: pearde
workflow: probe-then-spec
footprint:
  - resources/board/transitions.py
  - resources/board/specs.py
  - resources/board/collect.py
  - resources/board/brief.py
  - resources/board/init.py
  - resources/pearde.py
  - references/parts/handles.md
  - prds/the-board-runs-itself/init-asks-nothing/probe/verify.sh
---

# an-unknown-flag-refuses — a state-moving command with a flag it does not know writes nothing, and `--dry` is real on every one of them

When this is done, `pearde release <prd> open --dry` prints the transition
it would make and moves nothing; `pearde release <prd> open --dyr` prints
`unknown flag --dyr — release takes: --as, --board, --dry` and exits 2 with
nothing written; and every other command that moves state or commits does
the same.

## The consequence, named

On 2026-08-29 the orchestrator ran `pearde release check-crosses-member-boundaries
open --dry` to show another session the new verb. `release` has no `--dry`;
the flag was ignored and the command moved another session's parked PRD to
`open` on the live board, wrote the row, cleared `claim:`. Measured, not
inferred: `.transitions.jsonl`'s last row. Three things make it the tool's
defect rather than a slip:

- the guard cannot catch it — it refuses a hand-written `state:` and a board
  walked by hand; this was the sanctioned verb with one meaningless word;
- it fails in the dangerous direction — a refused flag costs a retype, an
  ignored one costs a transition on someone else's PRD;
- the argument handling is shared, so `claim`, `release`, `defer`, `retry`,
  `unblock`, `set`, `answer`, `specced`, `refine`, `collect`, `sweep
  --apply`, `brief` all accept nonsense the same way.

## The rule

- One flag parser for every command `pearde.py` discovers, in one place:
  a command declares the flags it takes; anything else that starts with `--`
  is `unknown flag <flag> — <cmd> takes: <list>`, exit 2, before any read of
  the board. A misspelt flag never reaches a write.
- `--dry` on every command that writes a board file or commits: prints the
  exact line the real run would print, prefixed `dry ·`, and every path it
  would write or add, and writes nothing. `collect --dry` already exists —
  it becomes the model, not the exception.
- `pearde <cmd> --help` lists the flags the same declaration lists; the two
  cannot drift because they are one list.
- `handles.md`'s Command column names `--dry` where it applies.

## Files

| file | change |
|---|---|
| `resources/board/transitions.py` | the declaration and the parser; `--dry` on every verb |
| `resources/board/specs.py` · `collect.py` · `brief.py` · `init.py` | declare their flags through the same parser; `--dry` where a write exists |
| `resources/pearde.py` | `--help` reads the declaration |
| `references/parts/handles.md` | `--dry` in the Command column |

## Verify

- On a copy of the example board, for each of the twelve commands above: an invented flag exits 2 with the flag and the real list named, and `git status --porcelain <copy>` and `.transitions.jsonl` are unchanged; `--dry` prints `dry ·` and the line, and the same two checks hold; the real run then makes exactly the change the dry line said.
- `pearde <cmd> --help` for each lists the same flags the refusal lists.
- `transitions-are-commands` (74), `one-predicate` (53), `a-parked-prd-comes-back` (44), `collect-keeps-its-word` (101), `specced-is-a-command` (90), `brief-is-printed` (104), `init-asks-nothing` (89) green, or each moved line named.
