---
state: done
origin: requested
actual: 1.2h
commit: 3a84801
priority: 68
complexity: 52
blast-radius: high
repo: pearde
workflow: probe-then-spec
needs:
  - one-command
  - an-example-board
footprint:
  - resources/board/transitions.py
  - resources/questions.py
  - resources/board/serve.py
  - resources/board/edit.py
  - references/parts/states.md
  - references/parts/progress.md
  - references/parts/contract.md
---

# transitions-are-commands — the orchestrator chooses, the tool moves the state

When this is done, every write of `state:` on a PRD goes through one command
that checks the gate @references/parts/states.md names, writes through
@resources/board/edit.py, prints the progress line, and refuses what the
table forbids with the gate named.

## Contract

| `pearde …` | does | gate |
|---|---|---|
| `add <title> [--priority N] [--body -]` | a directory and `prd.md` from the template, `open`, `origin: requested`; the body from stdin when `--body -` | the slug is free |
| `claim <prd> <worker>` | `open → analyzing` or `specced → claimed`; writes `claim: <worker> <now>` | leaf · unclaimed · `needs:` all `done` · no footprint overlap with a `claimed` PRD · `workflow:` resolves — the one test loop steps 4 and 5 share |
| `release <prd> <state>` | `analyzing → refine\|question\|open` · `claimed → blocked\|failed`; clears `claim:` | `question` needs a `## Questions` round `questions.py` accepts · `blocked` needs `needs:` · `failed` needs `## Failure` |
| `answer <prd> Q<n> "<text>"` | `**Q<n>** *(answered <now>)* — <text>` under `## Answers`; `open` when every question is answered | `Q<n>` exists in `## Questions` and is unanswered |
| `defer <prd>` · `retry <prd>` · `unblock <prd>` | per @references/parts/handles.md | `retry` needs `failed`; `unblock` needs `blocked` |
| `set <prd> <state> --force` | any transition, and says `forced` on the line | none — the escape hatch, never the path |

Every command:

- prints the progress line of @references/parts/progress.md, every term
  computed by the tool — the round no longer computes it;
- exits 1 with the gate named when refused, and writes nothing;
- touches one PRD and nothing else;
- takes `@<member>/<rel>` on a master board and writes at the member's real
  path;
- appends a row to `prds/.transitions.jsonl` — `{"t","prd","from","to"}` —
  the board's only memory of when a state moved. Never `.history.jsonl`: that
  file is the daemon's burn-down, one row a day, truncated to 400 rows on
  every write, and `view.js` reads `d`/`states` off every row. The new name
  joins the four machine-local names in `.gitignore`.

The persona term `as <id>` is the one term the tool cannot know. `--as <id>`
sets it, else `PEARDE_AS` in the environment — set by the session when it
switches, and per-session like the persona itself — else the command refuses:
the line is the only record of the persona, and a defaulted `engineer` after
a switch would rewrite it.

## Rules

- **One writer stays.** A command is the orchestrator's hand. The view's
  state writes in `serve.py` (`/edit`, the kanban drag) call the same
  function with `force` — a person at the page is the user talking to the
  board, per `loop.md` step 2, and is not gated — and the line the daemon
  prints says `forced · view`. `transitions.py` joins `SOURCES` in
  `serve.py`, so the daemon re-execs when the gate changes; otherwise a drag
  and a command diverge silently.
- A command cannot tell who called it. A worker's shell passes every gate.
  "Never edit frontmatter" stays in the brief, and the memo says so.
- `edit.py` stays the only writer of bytes — one line, atomically,
  frontmatter and body never in one write.
- **The gate is the table.** `states.md` gains a `command` column, and every
  rule the command enforces leaves the prose of `loop.md` when
  `the-loop-is-commands` lands — this PRD does not touch `loop.md`.
- A refused transition prints what would clear it: the `needs:` not done, the
  clashing PRD and path, the slug that names nothing.
- The guard's "round file owed" comment on a `prd.md` write stays — the
  `.round.md` is still the session's to write.

## Files

| file | change |
|---|---|
| `resources/board/transitions.py` | new — the table above, importing `plan.py` for the reads and `edit.py` for the writes |
| `resources/board/serve.py` | `/edit` state writes and `/new` call `transitions` |
| `references/parts/states.md` · `contract.md` · `progress.md` | the command column; "printed by the tool" |

## Verify

On a copy of the example board:

- every forbidden transition in the table exits 1 naming the gate; the
  `git diff` is empty afterwards;
- `claim next impl-1` on the gated PRD exits 1 naming `building`; after
  `set building done --force`, it succeeds and the diff is exactly two lines;
- the progress line on stdout equals `plan.py scan`'s `progress:` terms;
- `answer asking Q1 …`, `Q2 …`, `Q3 …` leaves `asking` `open` with three
  stamped lines under `## Answers` and `questions.py check` silent; a second
  `answer asking Q1` exits 1 with `answered`;
- a drag in the kanban view writes the same bytes as `pearde set --force`
  (`viewtest` drives the drag), and the daemon's log line carries `view`;
- a command run without `--as` and without `PEARDE_AS` exits 1;
- `.transitions.jsonl` gains one row per successful command, and
  `.history.jsonl` is byte-identical before and after.

## Report

DONE · committed · harnesses 47/47 73/73 39/39
