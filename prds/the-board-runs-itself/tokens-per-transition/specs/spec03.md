---
complexity: 6
footprint:
  - resources/board/plan.py
---

# spec03 — status prints the session's cost, and the readers the page needs

`resources/board/plan.py` gains, beside `read_history`: `read_transitions`
(the last thirty rows of `.transitions.jsonl`), `GUARD_DIR` (honouring
`PEARDE_GUARD_STATE`), `guard_sessions`, `guard_block`, `guard_view` (every
session that counted on this board, oldest first, or `None` when the guard
left no file) and `session_line`. `cmd_status` prints one more line — `this
session: <calls> calls · <refused> refused · <n> transitions · <calls/n> per
transition`, `—` for the ratio at zero transitions, and `this session: no
guard` when there is no session file. `gantt_payload` carries `transitions`
and `guard`. `scan` is untouched and byte-identical.

It stands from the probe, built in place; `plan.py` is the loop's hot path,
so the unit's work is the byte-identity and daemon checks below, run after
any further edit.

## Acceptance

- [x] `python3 resources/board/plan.py status <copy>` prints a last line matching `^this session: [0-9]+ calls · [0-9]+ refused · [0-9]+ transitions · [0-9.—]+ per transition$` when the guard's newest file holds a block for that board
- [x] with `PEARDE_GUARD_STATE` naming an absent directory the last line is exactly `this session: no guard`
- [x] the rendered payload has `transitions` (a list, at most thirty rows) and `guard` (`null` with no state file; otherwise `{"sessions": [...]}` with `session`, `refused`, `calls`, `transitions` per row)
- [x] `python3 resources/board/plan.py scan` on a fresh-mtime copy of the example board is byte-identical before and after the edit
- [x] `python3 resources/board/serve.py status` says `up` after the edit

## Verify and Proof

```sh
python3 -c "import ast; ast.parse(open('resources/board/plan.py').read())"
grep -n 'def read_transitions\|def guard_view\|def session_line\|^GUARD_DIR' resources/board/plan.py
T=$(mktemp -d); python3 resources/board/plan.py example "$T/ex" >/dev/null; find "$T/ex" -type f -exec touch {} +; python3 resources/board/plan.py scan "$T/ex/prds" > "$T/a.txt"; PEARDE_GUARD_STATE="$T/none" python3 resources/board/plan.py status "$T/ex/prds" | tail -1; rm -rf "$T"
bash prds/the-board-runs-itself/tokens-per-transition/probe/verify.sh </dev/null | sed -n '/^## status prints/,/^## the analytics/p'
```
