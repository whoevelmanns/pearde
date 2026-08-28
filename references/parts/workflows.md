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

## The two shapes this is not

- **A workflow engine.** Nothing runs a step. A worker reads one page and
  follows it, and `on failure` is a route it walks rather than a handler that
  fires.
- **A searchable index.** No ranking, no tags, no cross-library query. `list`
  and `## Use when` are the whole lookup — a library too large to skim is a
  library of workflows nobody follows.
