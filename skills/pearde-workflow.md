---
name: pearde-workflow
description: How a kind of job is done, kept where the next session looks — an ordered route of atomic steps a worker follows, and that gets better every time it is followed. Read the library, print one as a worker is handed it, attach one to a PRD, check the set. Use for "/workflow", "workflow", "how do we do X", "how is this kind of job done", "which workflow fits this", "attach a workflow", "improve the workflow", "check the workflows", "add an atomic", "what route should this worker follow". A workflow is written from a run, never from reading.
---

Read @references/workflow.md for the format — the two file shapes, the closed
frontmatter set, the steps grammar, and the `## Workflow <slug>` section a run
returns. @references/parts/workflows.md is when one is written, how it is
attached, and what a run is allowed to change. The scope is `@@workflows`.

- **A route, not an engine.** Nothing runs a step. A worker reads one page and
  follows it, and `on failure` is a route it walks rather than a handler that
  fires.
- **An atomic is one unit** — `## Do`, `## Done when`, `## Fails when`. A
  workflow is `## Use when` and an ordered `## Steps` over atomics, one
  back-edge per row. Exactly one slug key says which it is.
- **From a run, never from reading.** An edit cites the step and the PRD that
  ran it; an atomic that "could be clearer" to a reader is not an edit. The
  lesson replaces the sentence that was wrong — `updated` is the date, and git
  holds what it replaced.
- **The worker never writes here. The orchestrator does, and only it.** A
  worker returns its edits in the report, and the collect applies or refuses
  each one — @references/parts/workflows.md is the table that decides.
- **`runs` is evidence, not a score.** One collect counts one run, and a `0`
  beside an old `date` is a file to delete, not a file to promote.

```sh
python3 @resources/pearde.py workflow list  [board]        # slug · kind · runs · updated · subject
python3 @resources/pearde.py workflow show  <slug> [board] # the file
python3 @resources/pearde.py workflow brief <slug> [board] # the workflow as one page, atomics inlined
python3 @resources/pearde.py workflow check [board]        # what doctor reports for `workflows`
```

`workflow` forwards to `@resources/workflows.py`, the only reader of that
format. `brief` is what a worker is handed and exits 1 on an atomic slug — an
atomic is shown, not briefed.

Workflows live at `prds/workflows/`, so a board is needed to read one. With
none in scope, say where the library would be; adding a file and attaching a
slug to a PRD are orchestrator writes, and neither happens uninvited.
