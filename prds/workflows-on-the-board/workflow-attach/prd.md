---
state: done
origin: requested
actual: 0.6h
commit: e053839
priority: 50
complexity: 27
blast-radius: mid
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
  - references/parts/loop.md
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
| `resources/board/plan.py`         | the scan line carries `· wf <slug>` when set, `· wf <slug>?` when the slug names no workflow — an atomic is a file, so naming one marks the same way. `plan`'s `ready now` line carries the `?` form too, beside `(unspecced)`: that list is the dispatch list step 5 skips from. Display only — `compute_plan`'s ordering is untouched |
| `references/parts/workflows.md`   | the attach row filled                                                                                          |
| `references/parts/loop.md`        | steps 4 and 5 gain the third skip: a PRD whose `workflow:` names no workflow is not dispatched — fix the slug or remove the key |
| `references/parts/contract.md`    | one more row, on the `specNN.md` table: who may write a spec, and the narrow condition under which the orchestrator may — `prds/memos/the-orchestrator-may-write-a-spec.md` |

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
- A `workflow:` naming no **workflow** is a broken PRD, not a silent one:
  `check` reports it, the scan marks it, the worker is not dispatched until it
  is fixed or removed. Naming an atomic is that same break — a route was asked
  for and a single step was found — and `resources/workflows.py` already
  reports the two cases with distinct messages.
- A member PRD on a master board resolves `workflow:` against its own
  board's library, then the master's — the same order `needs:` resolves in.

## Verify

- `plan.py scan` on a board with `workflow: x` on one PRD prints `wf x` on
  its line; with the file absent, `wf x?`.
- `workflows.py check` reports the dangling one and is silent once the file
  exists.
- `python3 resources/index.py check` silent.
- `references/parts/loop.md` step 5 skips a PRD whose `workflow:` names no
  workflow, and step 4's dispatchable test says the same.
- `plan.py plan` marks the same PRD `wf <slug>?` on its `ready now` line, and
  leaves `compute_plan`'s ordering alone.
