# Handles

Every command the board answers to.

The spelling follows the setup — `/pearde status` where commands take
arguments, "pearde status" in plain chat. The meanings are fixed.

**Several of these are also skills of their own**, invocable without the
board in front of them: `pearde-drill`, `pearde-memo`, `pearde-view`,
`pearde-master`, `pearde-doctor`, `pearde-persona`, `pearde-persona-ask`,
`pearde-persona-create`, `pearde-scout`. Typed inside a round they are the
short handles below and behave exactly as this table says. Typed cold they
are the same feature with no round around it — `@@skills` is the list, and
each skill file says what it does with no board in scope.

| Want                         | Say                                                                                                      |
|------------------------------|-----------------------------------------------------------------------------------------------------------|
| report only, change nothing  | `status`                                                                                                 |
| one round, then stop         | `once`                                                                                                   |
| more implementers            | `workers=5` — written to `prds/settings.md`, persists                                                    |
| deeper spec pipeline         | `pipeline=5` — written to `prds/settings.md`, persists                                                   |
| new PRD                      | `add <title>` — dir + `prd.md` from `@references/templates/prd.md`, `state: open`, `origin: requested`    |
| park a derived PRD           | `defer <prd>` — `state: deferred`, per @references/parts/derived.md |
| work out what is wanted      | `drill <prd>` — interview per `@references/drill.md`; with no `<prd>`, into a new tree                    |
| retry a failed PRD           | `retry <prd>` — moves `## Failure` into the body as history, sets `open`                                 |
| a blocked PRD's event landed | `unblock <prd>` — re-runs only the open boxes; `done` when they close                                    |
| close what is finished       | `collect` — every PRD whose acceptance boxes are all `[x]`: verify, commit, `done`. Loop step 6, run on its own |
| run one PRD to done          | `run <prd>` — the loop scoped to that PRD's subtree                                                      |
| record a decision            | `memo <subject>` — `prds/memos/<slug>.md` from `@references/templates/memo.md`                            |
| who is working               | `persona` — the active one and why; `persona <id>` switches, for this session only. Stored nowhere        |
| one persona's read on one problem | `ask <id> <question>` — calls that persona, pointed at this session for context, and talks to it until the question is settled. It answers and writes nothing; the session keeps its own persona. The board calls one on its own judgment too, unasked |
| a persona for a new field    | `persona create <topic>` — research the field and its real practitioners, compose one from the best of them, per `@@personas` |
| pre-plan the dispatch order  | `plan` — `@resources/board/plan.py plan`; print the frontier and queue it returns                                       |
| the local timeline           | `gantt` — `@resources/board/plan.py gantt --open`: the plan as `prds/.view.html`, x = distance to the vision |
| open the board               | `view` — `@resources/board/serve.py ensure`, then the URL it prints                                          |
| plan across projects         | `master <path> …` — writes `members:` in `prds/settings.md`, asks the group's `name:` the first time. This board is then the parent every round works in |
| what a master merges         | `master` with no path — `@resources/board/plan.py members`: every member, its path, `MISSING` when not on disk |
| re-order after anything moved| `reconcile` — `@resources/board/plan.py reconcile`: schedule recomputed, anchor kept. The live service already does it, on every board |
| is this thing wired?         | `doctor` — `@resources/doctor.sh --fix`, per @@doctor; print every line |

- `add` is the user asking, so `origin: requested`. Only the orchestrator
  writes `origin: derived`, and only with `from:` — @references/parts/derived.md
  says what must be true before it is filed `open` rather than `deferred`.
- `collect` changes nothing about the gate: a PRD with an open box, or with no
  verify output on record, is verified first and `failed` if the tree is red —
  a board whose finished work is not closed schedules around it.
- `master <path>` takes one or more paths, each a board or a repo holding one,
  and appends them to `members:`. It creates nothing in the member and moves
  no file. Print what the merged board now holds: member count, PRD count, the
  plan `reconcile` produced.
- `memo <subject>` slugs the subject — lowercase, spaces to hyphens. The slug
  is both the filename and the `memo:` key, and `doctor` fails if they
  disagree. Write the memo when the call is made, not when the work lands.
- `persona <id>` and `ask <id>` are the switch and the question. Switch when
  the whole round wants a different reading. Ask when one problem does.
  Neither writes a file — a persona is session state, per `@@personas`, and
  the round's `· as <id>` is the only record it has.
- `ask` is a handle, not a permission. The board reaches a persona on its own
  judgment mid-round — before `done`, on a naming call, on a report it cannot
  check from inside its own frame — and says who it asked and what came back.
  Typing `ask` is how you start that conversation rather than waiting for it.
- `add` takes the title as written. A one-line title is too thin to spec, so
  the analyst returns REFINE or QUESTION. `drill` settles it first — it runs
  @references/drill.md to completion and leaves a tree the loop picks up:
  settled contract as the body, each branch a child dir, `state: open`.
  Dispatch nothing while a drill is running.

`run <prd>` filters the board to that PRD and its children:

- Scan still parses everything, for the sweep and the progress line, but only
  PRDs inside `prds/<prd>/` change state.
- The user named it, so a `failed` target or child is reopened first, as
  `retry` would.
- A `done` target is reported and left alone. No match: list the near-misses,
  change nothing.
- The run ends when the subtree is drained — report the target's final state —
  or everything left in it is blocked on the user.

One orchestrator per board. On start, fresh `analyzing` / `claimed` claims you
did not make may be another session's live workers: say so and run `status`
only. Never sweep another live session's claims.
