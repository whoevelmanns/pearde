# Handles

Every command the board answers to.

The spelling follows the setup — `/pearde status` where commands take
arguments, "pearde status" in plain chat. The meanings are fixed.

**Several of these are also skills of their own**, invocable without the
board in front of them: `pearde-drill`, `pearde-memo`, `pearde-view`,
`pearde-report`, `pearde-master`, `pearde-doctor`, `pearde-persona`,
`pearde-persona-ask`, `pearde-persona-create`, `pearde-scout`, `pearde-workflow`. Typed inside a round they are the
short handles below and behave exactly as this table says. Typed cold they
are the same feature with no round around it — `@@skills` is the list, and
each skill file says what it does with no board in scope.

| Want                         | Say                                                                                                      | Command |
|------------------------------|-----------------------------------------------------------------------------------------------------------|---------|
| report only, change nothing  | `status` — `@resources/board/plan.py scan` plus the progress line. Changes nothing, reads no file the scan already read | `pearde status` |
| the board as one page        | `scan` — `@resources/board/plan.py scan`: counts, progress terms, collect, in flight, waiting on you, ready, gated. Loop step 1, run on its own | `pearde scan` |
| one round, then stop         | `once`                                                                                                   | — |
| more implementers            | `workers=5` — written to `.pearde/settings.md`, persists                                                    | — |
| deeper spec pipeline         | `pipeline=5` — written to `.pearde/settings.md`, persists                                                   | — |
| new PRD                      | `add <title>` — dir + `prd.md` from `@references/templates/prd.md`, `state: open`, `origin: requested`. Runs as printed: with no `--as` and no `PEARDE_AS` it files the PRD `· as engineer (default)`, the one transition that does — a new PRD has no earlier line to rewrite | `pearde add [--dry]` |
| park a derived PRD           | `defer <prd>` — `state: deferred`, per @references/parts/derived.md; `release <prd> open` is its inverse, the one way back from any parked state | `pearde defer [--dry]` |
| work out what is wanted      | `drill <prd>` — interview per `@references/drill.md`. With no `<prd>`: the board's own open frontier where there is one, else a new tree | — |
| retry a failed PRD           | `retry <prd>` — moves `## Failure` into the body as history, sets `open`                                 | `pearde retry [--dry]` |
| a blocked PRD's event landed | `unblock <prd>` — re-runs only the open boxes; `done` when they close                                    | `pearde unblock [--dry]` |
| close what is finished       | `collect` — every PRD whose acceptance boxes are all `[x]`: verify, commit, `done`. Loop step 6, run on its own | `pearde collect [--dry]` |
| run one PRD to done          | `run <prd>` — the loop scoped to that PRD's subtree                                                      | — |
| the state, for a person      | `report` — rewrites `.pearde/report.md` whole: planned, in work, undecided or failing, in plain words per `@@report` | — |
| record a decision            | `memo <subject>` — `.pearde/memos/<slug>.md` from `@references/templates/memo.md`                            | `pearde memo add <subject>` |
| the workflow library         | `workflow` — `@resources/workflows.py list`: slug · kind · runs · updated · subject, per `@@workflows` | `pearde workflow list` |
| one, as a worker sees it     | `workflow <slug>` — `@resources/workflows.py brief`: the `## Use when`, then every step with its atomic inlined. `show` when the slug is an atomic — an atomic is shown, not briefed, and `brief` exits 1 on one | `pearde workflow brief <slug>` |
| a new atomic                 | `workflow add atomic <subject>` — a file from `@references/templates/atomic.md`, slugged as a memo is, at `runs: 0`. An orchestrator write, and only from a job that recurred | — |
| a new workflow               | `workflow add <subject>` — a file from `@references/templates/workflow.md`; every atomic a step names exists first, or the step sends a worker nowhere | — |
| attach a workflow to a PRD   | `workflow attach <prd> <slug>` — writes `workflow:` on that `prd.md`. An orchestrator write; the drill writes it on the tree it produces | — |
| check the library            | `workflow check` — `@resources/workflows.py check`: one problem per line, silent when clean. The `doctor` row alone | `pearde workflow check` |
| who is working               | `persona` — the active one and why; `persona <id>` switches, for this session only: `export PEARDE_AS=<id>`, the variable every command reads, exported as `engineer` by the install line. Stored on no board file | — |
| one persona's read on one problem | `ask <id> <question>` — calls that persona, pointed at this session for context, and talks to it until the question is settled. It answers and writes nothing; the session keeps its own persona. The board calls one on its own judgment too, unasked | — |
| a persona for a new field    | `persona create <topic>` — research the field and its real practitioners, compose one from the best of them, per `@@personas` | — |
| pre-plan the dispatch order  | `plan` — `@resources/board/plan.py plan`; print the frontier and queue it returns                                       | `pearde plan` |
| the local timeline           | `gantt` — `@resources/board/plan.py gantt --open`: the plan as `.pearde/.state/view.html`, x = distance to the vision | `pearde gantt --open` |
| weight in real hours         | `calibrate` — `@resources/board/plan.py calibrate`: fit hours-per-weight from every done PRD with an `actual:` across every registered board; the view prints real hours from it | `pearde calibrate` |
| open the board               | `view` — `@resources/board/serve.py ensure`, then the URL it prints                                          | `pearde view` |
| plan across projects         | `master <path> …` — writes `members:` in `.pearde/settings.md`, asks the group's `name:` the first time. This board is then the parent every round works in | — |
| what a master merges         | `master` with no path — `@resources/board/plan.py members`: every member, its path, `MISSING` when not on disk | `pearde members` |
| re-order after anything moved| `reconcile` — `@resources/board/plan.py reconcile`: schedule recomputed, anchor kept. The live service already does it, on every board | `pearde reconcile` |
| is this thing wired?         | `doctor` — `@resources/doctor.sh --fix`, per @@doctor; print every line | `pearde doctor --fix` |
| take a PRD for a worker      | `claim` | `pearde claim [--dry]` |
| hand a PRD back with a state | `release` | `pearde release [--dry]` |
| answer a question on a PRD   | `answer` | `pearde answer [--dry]` |
| force any transition         | `set` | `pearde set [--dry]` |
| validate the specs, sum the weight| `specced` | `pearde specced [--dry]` |
| children from the analyst's split| `refine` | `pearde refine [--dry]` |
| print a worker's brief       | `brief <prd> [--role <role>] [--as <id>] [--force]` — `@resources/board/brief.py`: header line, persona line, workflow block, the role's brief from `@references/parts/workers.md` with the placeholders filled; the role follows the state, `--role` overrides. `brief --consult <id> --question "<q>" [--transcript <path>]` is the consultant's | `pearde brief` |
| sweep the stale claims       | `sweep [--apply]` — every claim silent past `claim-ttl` (@references/settings.md), one line each with what `--apply` does: `analyzing → open`, `claimed → failed` with `## Failure` written; never a claim `.pearde/.state/round.md` names, never an analyst whose specs are on disk. Loop step 1, once per session | `pearde sweep [--dry]` |
| a board, registered and planned| `init` | `pearde init [--dry]` |
| the board's settings         | `settings` | `pearde settings [--dry]` |
| the vision and its axis      | `vision` | `pearde vision` |

The Command column is the line @resources/pearde.py answers. A `—` is a
handle the round answers by hand, with no command behind it. `[--dry]` marks
a command that writes: with it, the command prints the line the real run
would print, `dry ·` in front, then `would write:` and every path, and
writes nothing. A flag a command does not declare is refused before the
board is read — `unknown flag --dyr — release takes: --as, --board, --dry`,
exit 2 — and `pearde <cmd> --help` prints that same list.

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
- `report` is the only document on the board a person is the reader of. It is
  one state and never a log: the file is rewritten whole, and no PRD name,
  board state or weight survives into it.
- `memo <subject>` slugs the subject — lowercase, spaces to hyphens. The slug
  is both the filename and the `memo:` key, and `doctor` fails if they
  disagree. Write the memo when the call is made, not when the work lands.
- `persona <id>` and `ask <id>` are the switch and the question. Switch when
  the whole round wants a different reading. Ask when one problem does.
  Neither writes a board file — the switch is `export PEARDE_AS=<id>` per
  `@@personas`, or `--as <id>` on a line that runs in a fresh shell; the call
  is `@@consult`; and the round's `· as <id>` is the only record on the board
  either leaves.
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
  PRDs inside `.pearde/prds/<prd>/` change state.
- The user named it, so a `failed` target or child is reopened first, as
  `retry` would.
- A `done` target is reported and left alone. No match: list the near-misses,
  change nothing.
- The run ends when the subtree is drained — report the target's final state —
  or everything left in it is blocked on the user.

One writer per file, sequenced between sessions. On start, fresh `analyzing`
/ `claimed` claims you did not make may be another session's live workers:
say so and run `status` only. `sweep` lists them and `--apply` leaves any
claim `.pearde/.state/round.md` names.
