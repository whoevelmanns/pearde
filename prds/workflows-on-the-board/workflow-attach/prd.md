---
state: open
origin: requested
priority: 50
complexity: 0
blast-radius:
repo: pearde
needs:
  - workflow-format
  - workflow-reader
footprint:
  - references/parts/contract.md
  - references/templates/prd.md
  - references/templates/spec.md
  - references/parts/workers.md
  - references/drill.md
  - references/parts/workflows.md
  - resources/board/plan.py
---

# workflow-attach — a PRD or a spec names its workflow, and the brief opens with it

When this is done, `workflow:` is a contract key, the analyst names the
workflow its build followed, the drill attaches one when it writes a tree,
and a dispatched worker's brief carries the workflow expanded.

## Contract

`prd.md`:

| key        | written by                                                                  | read for                                              |
|------------|------------------------------------------------------------------------------|--------------------------------------------------------|
| `workflow` | user · drill, on the tree it writes · orchestrator on `specced`, from the analyst's report | the worker brief · `workflows.py check` · the scan line |

`specNN.md`:

| key        | written by | read for                                  |
|------------|------------|--------------------------------------------|
| `workflow` | analyst    | overrides the PRD's for that unit          |

Missing reads as none: the brief is as today.

## Files

| file                              | change                                                                                                        |
|-----------------------------------|----------------------------------------------------------------------------------------------------------------|
| `references/parts/contract.md`    | the two rows; `workflow` in the defaults table as none                                                          |
| `references/templates/prd.md`     | the key, commented, beside `repo`                                                                              |
| `references/templates/spec.md`    | the key, commented, beside `footprint`                                                                         |
| `references/parts/workers.md`     | the block below in both briefs; the analyst's SPECCED report names the workflow followed, or `none fit`         |
| `references/drill.md`             | Output: when a workflow's `## Use when` fits a branch, write `workflow:` on that child                          |
| `resources/board/plan.py`         | the scan line carries `· wf <slug>` when set, `· wf <slug>?` when the slug names no file                       |
| `references/parts/workflows.md`   | the attach row filled                                                                                          |

## The block

Opens the brief after the persona line, verbatim, placeholders filled:

> Follow the workflow `<slug>`: `python3 @resources/workflows.py brief <slug>
> <board>` prints it — the steps in order, each with its atomic inlined. Take
> the steps in order. When a step fails, go where its `on failure` says; a
> back-edge is taken at most twice, then stop and report with the step named.
> Your report carries `## Workflow <slug>` per @references/workflow.md: one
> row per step, and under `### Edits` the replacement text for every failure
> the atomic caused — a wrong command, a stale path, a check that cannot
> fail, a shape `## Fails when` does not list. Never edit the workflow files
> yourself.

A spec with its own `workflow:` — the implementer follows that one for that
spec and the PRD's for the rest; the report carries one `## Workflow` section
per workflow followed.

## Rules

- A worker never writes under `workflows/`. Edits go in the report;
  `workflow-improve` says what happens to them.
- An analyst that followed no workflow reports `workflow: none fit`. A job it
  saw recur is a finding in its report, not a file — a new workflow is
  `workflow add`, the orchestrator's act, at `runs: 0`.
- A `workflow:` naming no file is a broken PRD, not a silent one: `check`
  reports it, the scan marks it, the worker is not dispatched until it is
  fixed or removed.
- A member PRD on a master board resolves `workflow:` against its own
  board's library, then the master's — the same order `needs:` resolves in.

## Verify

- `plan.py scan` on a board with `workflow: x` on one PRD prints `wf x` on
  its line; with the file absent, `wf x?`.
- `workflows.py check` reports the dangling one and is silent once the file
  exists.
- `python3 resources/index.py check` silent.
