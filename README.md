# prd — the PRD board

One session orchestrates a board of PRDs — product requirement definitions.
It specs them ahead, dispatches implementers on the specced ones, puts blocking
questions to the user, and prints progress on every state change.

All state is on disk. Anything that can read files, write files, and run
commands can work the board.

- `SKILL.md` — entry point where skills are discovered from a directory
- `SYSTEM.md` — the same pointer as a drop-in block, where instructions are read from a file
- `INSTALL.md` — what installed means. Not wired up yet? Start there
- `DRILL.md` — how to ask. Missing, unclear, or the user's call: drill, don't guess
- `LANGUAGE.md` — how to write. Everything on the board follows it
- `PRD_TEMPLATE.md` — one PRD
- `SPEC_TEMPLATE.md` — one implementable unit
- `statusline.sh` — renders the progress numbers continuously

The board lives at `prds/` in the repo root.

## Roles

- **Orchestrator** — the session working the board. The ONLY writer of PRD
  state. One writer means nothing to race, so there is no locking. One
  orchestrator per board.
- **Analyst** — turns one `open` PRD into specs, a split, or questions.
- **Implementer** — turns one `specced` PRD's specs into verified code.

Workers do the work; the orchestrator moves the states.

## The board

```
prds/<prd-name>/
  prd.md            # the PRD: frontmatter state + the request
  specs/            # written by the analyst; one implementable unit per file
    spec-<name>.md
  <child-prd>/      # a sub-PRD produced by refine; a dir with its own prd.md
    prd.md
```

A directory holding `prd.md` is a PRD. A subdirectory holding its own `prd.md`
is a child PRD; `specs/` holds none, so it is private material.

A parent with children is **not dispatchable** until every child is `done`.
Work flows to the leaves.

## Frontmatter contract

Tools know a handful of keys. Everything else in a `prd.md` or a spec is
yours, and no tool touches it.

`prd.md`:

| key        | written by                     | read for                     |
|------------|--------------------------------|------------------------------|
| `state`    | orchestrator                   | the loop, the status line    |
| `priority` | user                           | dispatch order, higher first |
| `est`      | orchestrator, from the analyst | progress line, `~<h>h left`  |
| `actual`   | orchestrator                   | calibration                  |
| `claim`    | orchestrator                   | the sweep, elapsed on `done` |
| `repo`     | user                           | the worker brief; optional   |

`specNN.md`:

| key         | written by | read for                    |
|-------------|------------|-----------------------------|
| `est`       | analyst    | summed into the PRD's `est`  |
| `footprint` | analyst    | the overlap check in step 5 |

`state` is the only key the loop cannot run without. Missing `priority` sorts
at 0. Missing `est` weighs at the board average.

Match a key by name, at any indentation, anywhere in the frontmatter. Nest it,
reorder it, group it — a `time:` map holding `est` and `actual` reads the same
as `est` and `actual` at the top. Names are unique within one file.

Writing frontmatter preserves what you did not write: unknown keys, order,
comments, nesting. Add `complexity`, `blast-radius`, `owner`, anything — it
survives every transition.

The body carries contract too: `## Questions`, `## Answers`, `## Failure` in a
PRD, `## Acceptance` and `## Verify and Proof` in a spec. Sections you add
beside them are yours.

## States

| state       | meaning                            | set by                         | leaves via                                                   |
|-------------|------------------------------------|--------------------------------|--------------------------------------------------------------|
| `open`      | can be claimed for analysis        | user / orchestrator            | analyst dispatched     → `analyzing`                         |
| `analyzing` | analyst is working out what to do  | orchestrator                   | analyst returns        → `specced` \| `refine` \| `question` |
| `refine`    | needs sub-PRD split or more detail | orchestrator (analyst verdict) | children created       → `open`                              |
| `question`  | blocked on the user                | orchestrator (analyst verdict) | answers written        → `open`                              |
| `specced`   | specs exist, ready to implement    | orchestrator                   | implementer dispatched → `claimed`                           |
| `claimed`   | implementer working it             | orchestrator                   | returns                → `done` \| `failed`                  |
| `done`      | specs implemented and verified     | orchestrator                   | terminal                                                     |
| `failed`    | attempt failed, needs revisit      | orchestrator                   | `retry <prd>` → `open`                                       |

Never take a worker's word for a transition. `specced` requires spec files on
disk. `done` requires the verify commands actually run, output in the report —
spot-check the cheap ones.

## The loop

Run until the board is drained or everything left is blocked on the user.
`once` = one round. `status` = step 1 plus the progress report, change nothing.

1. **Scan** — `find prds -type f -name prd.md`, parse every
   frontmatter. No board? Create `prds/`, report it empty, stop.
   Once per session, sweep a dead session's leftovers: `analyzing` with no live
   worker → `open`; `claimed` with no live worker → `failed`. Partial code may
   exist — a human look is cheaper than a blind retry.

2. **Answer** — collect `## Questions` from every `question` PRD and put them
   to the user as one round per `DRILL.md`: the whole frontier, numbered, each
   with your recommended answer. Questions from different PRDs share a round.
   A question that depends on another still open belongs to the next round.
   Write answers under `## Answers`, set those PRDs `open`. No reply: leave
   them `question`, work the rest.

3. **Refine** — the analyst left the proposed split in its report. Create each
   child dir + `prd.md` (`state: open`, the child's contract as body), set the
   parent `open`. No usable split proposal means nobody understands the PRD
   yet: drill it per `DRILL.md`, then write that tree as the children. Never
   invent a split to keep the board moving.

4. **Spec ahead** — while count(`specced`) < **pipeline** (default 3) and
   dispatchable `open` PRDs exist (leaf, unclaimed, priority desc): mark each
   `analyzing` + `claim: <worker> <started>`, dispatch analysts, in one
   parallel batch.

5. **Implement** — while count(`claimed`) < **workers** (default 3) and
   `specced` PRDs exist: pick by priority, skip any whose spec footprint
   overlaps a PRD already `claimed`, mark `claimed` + `claim: <worker>
   <started>`, dispatch an implementer.

6. **Collect** — on each finished worker: validate the result (specs on disk /
   verify output present), write the transition, write `actual:` on a clean
   `done` per **Calibration**, clear `claim:`, print the progress line, return
   to step 2. A finished analyst refills the pipeline; a finished implementer
   frees a worker slot. Do not poll if results are pushed to you.

7. **Stop** — nothing in flight and nothing dispatchable: report per-state
   counts, every `question`/`refine`/`failed` PRD by name with what it needs,
   and the final progress line.

## Progress line

Print on EVERY state change:

```
▸ <prd>: <from> → <to> · done <d>/<n> · <p>% · open <o>/<n> · <q>% · ~<h>h left @<w> workers
```

- weight = the PRD's `est`. No `est` yet counts at the average est of estimated
  PRDs, 4h if none are estimated.
- `<p>` = Σ est(done) / Σ est(all). `failed` counts as remaining.
- `<o>` = PRDs still `open` — untouched, no analyst on them. `<q>` = `<o>/<n>`.
  Both are counts, never est-weighted: an `open` PRD has no `est` to weight by.
- `<q>` and `<p>` do not sum to 100. `<q>` is how much of the board is
  untouched, `<p>` how much of the work is done.
- `~<h>h left` = Σ est(not done) ÷ active workers. An estimate — label jumps
  honestly; a refine split that adds children moves it up.

`statusline.sh` renders the same numbers continuously where a status line can
run a command. Optional.

## Calibration

`est` is a guess. `actual` is what a run measured. Every clean run makes the
next `est` better.

Write `actual:` on the `claimed → done` transition. Elapsed = now minus the
timestamp in `claim:`. Round to the nearest 5 minutes; the units are `est`'s —
`45m`, `2h`.

Write it only when the run was clean:

- one dispatch, from `specced` straight to `done`
- DONE returned, every box `[x]`, verify output shown
- no BLOCKED round-trip
- no `## Failure` anywhere in the PRD's history

Anything else leaves `actual:` empty. A retry measures the retry. A BLOCKED
round-trip measures how long the user took to answer. Neither is the cost of
the work, and a wrong number is worse than none.

Read the record before writing a new `est:`:

```sh
grep -rl 'state: done' prds --include=prd.md \
  | xargs -r grep -H -E '^[[:space:]]*(est|actual):'
```

Scale by the ratio the pairs show. Three pairs at 4h/40m mean the board
estimates 6× high — say so in the report, and estimate the next PRD at the
corrected scale.

## Worker briefs

Give each worker exactly its brief with the placeholders filled in —
`<skill>` is this folder's path. Workers
never edit frontmatter, never touch other PRDs, and never write outside their
PRD folder — implementers also write the target repo. What they write follows
`LANGUAGE.md`. If a report is incomplete or the worker stopped mid-task,
continue THAT worker; it holds the context. Never respawn it.

**Analyst** — one per `open` PRD being specced:

> Read `prds/<prd>/prd.md`, including `## Answers`, and explore
> `<repo>` as needed. Return exactly one verdict:
> - **SPECCED** — write `specs/specNN.md` files, template
>   `<skill>/SPEC_TEMPLATE.md`, each one implementable unit:
>   goal, `est:` and `footprint:` in frontmatter, `- [ ]` acceptance boxes a
>   check can fail, and a verify command. Calibrate `est` against the
>   `est`/`actual` pairs of done PRDs on the board, per **Calibration**. Report
>   the spec list, the total `est` in hours, the ratio you calibrated by, and
>   the union of the footprints.
> - **REFINE** — the PRD holds more than one contract, or is too thin to spec.
>   Report the proposed children, `<dir-name> — one-line contract` each, and
>   what detail is missing.
> - **QUESTION** — a real fork only the user can settle: naming, scope, cost.
>   Never a fact you could look up — find facts yourself. Write `## Questions`
>   into prd.md in the round format of
>   `<skill>/DRILL.md` and report them.

SPECCED: confirm the spec files exist, write `est:`, set `specced`.
REFINE/QUESTION: set the state, keep the report.

**Implementer** — one per `specced` PRD dispatched:

> Read `prds/<prd>/prd.md` and every file in `specs/`. Implement the
> specs in `<repo>`. Run each spec's `verify:` command and the repo's own gate.
> Tick a box `[x]` only for a check you actually ran, quoting output. If
> blocked, STOP and report **BLOCKED** with the exact question or wall — do not
> guess, do not redefine the spec. Return **DONE** (per-spec box status +
> verify output) or **FAILED** (what broke, what you tried); on FAILED also
> write `## Failure` into prd.md.

DONE with every box ticked and verify output shown: set `done`.
Anything less: `failed` — or answer a BLOCKED worker and let it finish.

## Without parallel workers

Run the same loop single-file: scan → answer → refine → pick the
highest-priority actionable PRD → run its brief yourself as a checklist
(analyst for `open`, implementer for `specced`) with the transitions before and
after → print the progress line → repeat. Effectively `workers=1`,
`pipeline=1`.

Every rule still holds: one writer, verify before `done`, work flows to the
leaves.

## Handles

The spelling follows the setup — `/prd status` where commands take
arguments, "prd status" in plain chat. The meanings are fixed.

| Want                        | Say                                                                                                            |
|-----------------------------|------------------------------------------------------------------------------------------------------------------|
| report only, change nothing | `status`                                                                                                       |
| one round, then stop        | `once`                                                                                                         |
| more implementers           | `workers=5`                                                                                                    |
| deeper spec pipeline        | `pipeline=5`                                                                                                   |
| new PRD                     | `add <title>` — creates the dir + `prd.md` from `PRD_TEMPLATE.md`, `state: open`                                |
| work out what is wanted     | `drill <prd>` — interview per `DRILL.md`; with no `<prd>`, into a new tree                                      |
| retry a failed PRD          | `retry <prd>` — moves `## Failure` into the body as history, sets `open`                                        |
| run one PRD to done         | `run <prd>` — the loop scoped to that PRD's subtree                                                             |

`add` takes the title as written. A one-line title is too thin to spec, so the
analyst returns REFINE or QUESTION and the drill happens then. Use `drill` to
settle it first: it runs `DRILL.md` to completion and leaves a tree the loop
picks up — settled contract as the body, each branch a child dir with its own
`prd.md`, `state: open`. Dispatch nothing while a drill is running.

`run <prd>` filters the board to that PRD and its children. Scan still parses
everything, for the sweep and the progress line, but only PRDs inside
`prds/<prd>/` are answered, refined, specced, or implemented. Nothing
outside the subtree changes state. The user named it, so a `failed` target or
child is reopened first, exactly as `retry` would. A `done` target is reported
and left alone. No match: list the near-misses, change nothing. The run ends
when the subtree is drained — report the target's final state — or everything
left in it is blocked on the user.

One orchestrator per board. On start, if the scan shows fresh
`analyzing`/`claimed` claims you did not make, their workers may be alive in
another session: say so and run `status` only. Never sweep another live
session's claims.
