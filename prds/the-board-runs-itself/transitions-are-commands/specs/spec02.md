---
complexity: 12
workflow: implement-a-spec
footprint:
  - resources/board/serve.py
  - prds/the-board-runs-itself/transitions-are-commands/probe/edit_route.py
---

# spec02 — the view's state writes and `/new` go through the transition, forced, and the daemon re-execs when the gate changes

`serve.py`'s `/edit` pops `state` out of `fm`, writes every other key as
before, and last calls `transitions.transition(board, rel, state, "view",
force=True, source="view", out=<print, flushed>)` — so the kanban drag and
the answer flow (`append` + `fm.state` in one POST) both move the state
through the one writer, ungated because a person at the page is the user
talking to the board, and the daemon's `serve.log` carries `▸ <prd>: <from>
→ <to> · forced · view · … · as view`. A `Refused` (a name that resolves to
nothing, a state equal to the current one) answers 409 with the message.
`/new` calls `transitions.add(...)` — the slug gate, the template, the row and
the line — and answers 409 with the gate on a taken slug instead of
suffixing `-2`. `transitions.py` is in `SOURCES`, so the daemon re-execs when
the gate changes.

## What stands from the probe

All four hunks are in `resources/board/serve.py` (the import, `SOURCES`,
`/new`, `/edit`) — `git diff resources/board/serve.py` hunks at `import edit
as editlib`, the `SOURCES` tuple, the `/new` body and the `/edit` `fm` loop
are this PRD's; the hunks in the API docstring and in `do_GET` are another
session's and are not touched. The live daemon re-exec'd on the edit and
came back (`serve.py status` → `up`).
`python3 prds/the-board-runs-itself/transitions-are-commands/probe/edit_route.py`
drives both routes in-process through the real `Handler` with a stub socket —
no daemon, no port, no registry file — and printed `15 checks · 15 pass · 0
fail` on 2026-08-28.

## What is left

- A browser-driven drag. `viewtest.js` has no drag scenario today and the
  file is `an-example-board`'s footprint; the drag's only code path is
  `save(rel, {fm: {state}})` → `/edit`, which `edit_route.py` drives. When
  `viewtest.js --example` exists, a drag scenario there is one more line of
  proof, not a change here.
- `/new` used to suffix a taken slug (`-2`, `-3`); it now refuses with the
  gate. The page's "Not saved — add: the slug `x` is taken" toast is that
  refusal surfacing; if the view should suffix instead, do it in the page
  before the POST, never in the route.

## Acceptance

- [x] `python3 prds/the-board-runs-itself/transitions-are-commands/probe/edit_route.py` prints `0 fail`
- [x] POST `/edit` with `fm: {state: "claimed"}` on a PRD a command would refuse (gated `needs:`) answers 200, writes `state:` and no `claim:`, and the captured line contains `· forced · view ·` and ends `· as view`
- [x] POST `/edit` with `append` under `Answers` and `fm: {state: "open"}` in one call answers 200 with `wrote` equal to `["append", "state"]`
- [x] POST `/new` with a fresh title answers 200 with `{"prd": "<slug>"}`, the file carries `state: open` and `origin: requested`, and the line `▸ <slug>: — → open` is printed; with a taken slug it answers 409 with `taken` in `error`
- [x] `grep -n transitions.py resources/board/serve.py` shows the import and the `SOURCES` entry
- [x] the daemon, if running, is `up` after the edit: `python3 resources/board/serve.py status` prints `serve: up`

## Verify and Proof

```sh
python3 prds/the-board-runs-itself/transitions-are-commands/probe/edit_route.py
grep -n "transitions" resources/board/serve.py
python3 resources/board/serve.py status | head -1
```
