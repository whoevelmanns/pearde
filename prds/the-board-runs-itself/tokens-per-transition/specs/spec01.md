---
complexity: 8
footprint:
  - resources/guard.py
  - references/parts/guard.md
---

# spec01 — the guard counts what it sees

`resources/guard.py` keeps, per board, in the session's file under `boards`:
`calls`, `reads`, `bash`, `edits`, `refused` (since the session first saw the
board), `since` (the last transition), `transitions`, and `mark` (the counters
as they stood at that transition, with `tokens`). Every `pre` call on a board
moves `calls` and the tool's own counter and keeps `transcript_path`; every
`deny` moves `refused`. `PEARDE_GUARD_STATE` moves the state directory.
`references/parts/guard.md` carries the table under `## What it counts`.

The probe built all of it in place — a counter has no meaning outside the
function it lives in — and it stands in the tree. What is left is the check
that it still holds against the harness, and the reading of `guard.md` for
a sentence the code no longer matches.

## Acceptance

- [x] `PEARDE_GUARD_STATE=<tmp> python3 resources/guard.py pre` fed ten `Read` hook payloads on one board leaves `<tmp>/<session>.json` with `boards[<board>]` holding `calls: 10`, `reads: 10`, `bash: 0`, `edits: 0`, `refused: 0`, a numeric `since`, and `transcript` at the top level equal to the payload's `transcript_path`
- [x] a third `Read` of the same unchanged file is denied and the block reads `refused: 1`, `calls: 11`
- [x] a `Bash` payload moves `bash`, an `Edit` payload moves `edits`, and both move `calls`
- [x] with `PEARDE_GUARD_STATE` set, no file appears under `resources/board/state/guard/` for the run
- [x] `references/parts/guard.md` has a `## What it counts` section whose table names every key in the block, and names `PEARDE_GUARD_STATE`

## Verify and Proof

```sh
python3 -c "import ast; ast.parse(open('resources/guard.py').read())"
grep -c 'PEARDE_GUARD_STATE' resources/guard.py references/parts/guard.md
grep -n '^## What it counts' references/parts/guard.md
bash prds/the-board-runs-itself/tokens-per-transition/probe/verify.sh </dev/null | sed -n '/^## the guard counts/,/^## the transition/p'
```
