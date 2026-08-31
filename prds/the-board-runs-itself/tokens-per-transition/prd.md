---
state: done
origin: requested
actual: 1.3h
commit: 00a1371
priority: 40
complexity: 32
blast-radius: mid
repo: pearde
workflow: probe-then-spec
needs:
  - one-command
  - the-loop-is-commands
footprint:
  - resources/guard.py
  - resources/board/transitions.py
  - resources/board/plan.py
  - resources/board/view.js
  - references/parts/guard.md
  - references/parts/view.md
  - prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh
---

# tokens-per-transition — the round's cost is a number on the page, not a post-mortem

When this is done, the cost of moving one PRD one state is a number the page
draws over time, and a round that starts re-deriving shows it on the board
while it happens rather than in a report written the day after.

## Contract

| where | is |
|---|---|
| `resources/board/state/guard/<session>.json` | already one file per session. Gains per-board counters: `calls`, `reads`, `bash`, `edits`, `refused`, and `since` — the time of the last transition |
| the `.transitions.jsonl` row a transition appends | `{"t","prd","from","to","calls","reads","refused","tokens"}` — the counters since the last transition, then reset. `tokens` is the output-token sum from the transcript when the hook input names one, else `null`. `.history.jsonl` is untouched |
| `pearde status` | one more line: `this session: <calls> calls · <refused> refused · <n> transitions · <calls/n> per transition` |
| the **analytics** view | two series: calls per transition over the last thirty transitions, refusals per session. A rising line is the board re-deriving |
| `report.md` at the repo root | stays as the one measured session; the analytics page is the same measurement, continuous |

## Rules

- The guard counts what it sees. A session with the guard off records
  nothing, and the page says `no guard` rather than zero.
- Tokens are `unmeasured` unless the transcript is on disk and readable; the
  proxy is calls, and the page names it as the proxy.
- No new hook beyond the matcher `the-loop-is-commands` adds, no new
  process. The guard already fires on every call; the transition already
  writes its row.
- Nothing here changes what the round does — it measures.

## Files

| file | change |
|---|---|
| `resources/guard.py` | the counters |
| `resources/board/transitions.py` | the row |
| `resources/board/plan.py` | `cmd_status`'s line; a reader of `.transitions.jsonl` beside `read_history` |
| `resources/board/view.js` | the two series under analytics |
| `references/parts/guard.md` · `view.md` | the rows above |

## Verify

- Under a session with the guard wired, on a copy of the example board: two
  `pearde set --force` transitions after ten `Read` calls → two history rows,
  the first with `calls: 10`, the second with `calls: 0` or the calls between.
- `pearde status` prints the line with the same numbers.
- `viewtest` on the copy: the analytics view holds the two series, and
  reads `no guard` when the state file is absent.

## Report

DONE 21/21 · commit 00a1371 · probe 42/42
