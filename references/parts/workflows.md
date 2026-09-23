# Workflows

How a kind of job is done, kept where the next session looks.

A PRD says what to build and a memo says what was decided. A **workflow** says
how a job is done, and gets better every time it is followed.
@references/workflow.md is the format, the closed frontmatter set, the steps
grammar and the report section.

```
prds/workflows/<slug>.md
```

| kind         | file says          | is                                                |
|--------------|--------------------|----------------------------------------------------|
| **atomic**   | `atomic: <slug>`   | one unit — `## Do`, `## Done when`, `## Fails when` |
| **workflow** | `workflow: <slug>` | `## Use when`, then `## Steps` — an ordered list of atomics with a back-edge per row |

- No `state`. Never claimed, specced, or dispatched — invisible to scan and to
  the progress line, yet on the board.
- One flat directory, one file per slug, no nesting. `workflows:` in
  `prds/settings.md` points elsewhere, default `workflows/`.
- Frontmatter is a **closed set**, and exactly one of the two slug keys.
- `## Do` and `## Done when` are never empty. `## Fails when` is empty until a
  run fills it.

## When a file is written

| moment              | what happens                                                        |
|---------------------|----------------------------------------------------------------------|
| a job repeats       | a new file, by hand or from the drill's tree, at `runs: 0`           |
| a run hits a wall   | the text changes — a lesson folded into `## Do` or `## Fails when`, `updated` moved |
| a run ends          | the collect below — `runs` +1, the edits applied or refused, the files on the PRD's commit |

An edit is from a run, never from reading. The text carries the current
lesson; git holds every earlier one.

## Attached

A PRD or a spec names its route in frontmatter. The key is the same `workflow`
in both places, and @references/parts/contract.md is where it sits in the
contract:

| where       | written by                                                                    | is                                              |
|-------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| `prd.md`    | the user · the drill, on the tree it writes · the orchestrator on `specced`, from the analyst's report | the route every worker on this PRD is handed |
| `specNN.md` | the analyst                                                                   | overrides the PRD's, for that unit only          |

Missing reads as none, and the brief is exactly as it was before workflows
existed. Set, the worker's brief opens with the workflow block after the
persona line — @references/parts/workers.md holds that text, and the worker
returns `## Workflow <slug>` per @references/workflow.md.

A slug that names **no workflow** in the library is a broken PRD, not a silent
one: `check` reports it, `plan.py scan` marks the line `wf <slug>?`, and the
PRD is not dispatched until the key is fixed or removed. Naming an **atomic**
is that same break — an atomic is a file, so the slug resolves, but a route
was asked for and a single step was found. A set slug that does resolve prints
`wf <slug>` on the scan line, unmarked.

A member PRD on a master board resolves against its own board's library first,
then the master's — the order `needs:` resolves in.

```sh
python3 @resources/workflows.py list  [board]        # slug · kind · runs · updated · subject
python3 @resources/workflows.py show  <slug> [board] # the file
python3 @resources/workflows.py brief <slug> [board] # the workflow as one page, atomics inlined
python3 @resources/workflows.py check [board]        # what doctor reports for `workflows`
```

`brief` is what a worker is handed: the `## Use when`, then each step's row
with that atomic's body under it, in order — one page read once, instead of
a workflow and N atomics opened one at a time. It exits 1 on an atomic slug:
an atomic is shown, not briefed.

## Improved

A worker handed a route returns `## Workflow <slug>` — one row per step, and
under `### Edits` the replacement text for every failure the atomic caused.
@references/parts/loop.md step 6 is where those land, in the same batch as the
collect, and @references/parts/solo.md step 5 is the same five actions with no
report in between: the orchestrator followed the route itself, so it writes the
edit at the step that failed.

**The worker never writes here. The orchestrator does, and only it** — two
workers proposing edits to one atomic in one round is two collects, and the
second reads the file as the first left it. Nothing merges two edits to one
section.

What decides an edit:

| the failure was                       | the edit is | because                                                  |
|---------------------------------------|-------------|------------------------------------------------------------|
| a wrong command                       | applied     | the atomic named it, and the next run pays for it again    |
| a stale path                          | applied     | same                                                       |
| a check that cannot fail              | applied     | `## Done when` passed on a step that had not worked        |
| a shape `## Fails when` does not list | applied     | the run is the only way that table grows                   |
| the code's                            | refused     | the route was right and the tree was wrong                 |
| the PRD's                             | refused     | the contract was wrong, and a route cannot carry that      |

A refusal is said out loud — which of the two it was — and recorded in
`prds/.round.md` per @references/parts/round.md. The file is unchanged, so
nothing else on disk would say the run proposed it.

Four rules the collect holds the edit to:

- **From a run, never from reading.** An edit cites the step and the PRD that
  ran it. An atomic that "could be clearer" to a reader is not an edit.
- **Fold, do not log.** The lesson replaces the sentence that was wrong. No
  dated lines in the body — `updated` is the date, and git holds what it
  replaced.
- **An atomic stays one unit.** An edit that adds a second job splits the
  atomic instead, and the workflow gains a row. "And then" is two files.
- **The order may change from a run.** A step that always fails until a later
  one has run is in the wrong place: the report says so, the orchestrator moves
  the row, and the `on failure` back-edges are renumbered with it.

`runs` +1 goes on the workflow and every atomic that ran — a step the run never
reached does not count one, and a step that `stopped` did run. **One collect,
one count**: a step taken twice, because a back-edge came back to it, counts
once, and so does the atomic the back-edge landed on. `runs` is the number of
runs the file was in, not the number of traversals; the alternative would read
`runs: 3` off a single bad afternoon and call that file the exercised one.
`updated` moves only on a file whose text changed, so a route followed clean
ten times reads `runs: 10` with its original `updated`.

**`runs` is evidence, not a score:** `list` prints it so a reader sees which
files are exercised and which stand at `0`, and a `0` beside an old `date` is a
file to delete or a job that stopped repeating, not a file to promote.

Then `python3 @resources/workflows.py check`, before the commit. An edit that
breaks the format is refused, not repaired — the worker's text was wrong, and
repairing it in the collect makes the orchestrator the author of a line no run
produced.

**The commit is the PRD's.** The edited files are added with the rest and named
in the message, and the PRD's own `footprint:` does not grow to hold them: the
library is the board's, not the PRD's — @references/parts/commits.md. A library
`workflows:` points into another repo commits there, same subject, under the
one-commit-per-repo rule.

## The two shapes this is not

- **A workflow engine.** Nothing runs a step. A worker reads one page and
  follows it, and `on failure` is a route it walks rather than a handler that
  fires.
- **A searchable index.** No ranking, no tags, no cross-library query. `list`
  and `## Use when` are the whole lookup — a library too large to skim is a
  library of workflows nobody follows.
