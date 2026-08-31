---
name: pearde-workflow
description: How a kind of job is done, kept where the next session looks — an ordered route of atomic steps a worker follows, and that gets better every time it is followed. Read the library, print one as a worker is handed it, attach one to a PRD, check the set. Use for "/workflow", "workflow", "how do we do X", "how is this kind of job done", "which workflow fits this", "attach a workflow", "improve the workflow", "check the workflows", "add an atomic", "what route should this worker follow". A workflow is written from a run, never from reading.
---

Read @references/workflow.md for the format — the two file shapes, the closed
frontmatter set, the steps grammar, and the `## Workflow <slug>` section a run
returns. @references/parts/workflows.md is the mechanism: when one is written,
how it is attached, what a run is allowed to change, the table that decides
whether each returned edit is applied or refused, and how `runs` is counted.
Loop step 6 is where that collect happens. The scope is `@@workflows`.

```sh
python3 @resources/pearde.py workflow list  [board]        # slug · kind · runs · updated · subject
python3 @resources/pearde.py workflow show  <slug> [board] # the file
python3 @resources/pearde.py workflow brief <slug> [board] # the workflow as one page, atomics inlined
python3 @resources/pearde.py workflow check [board]        # what doctor reports for `workflows`
```

`workflow` forwards to @resources/workflows.py, the only reader of that
format. `brief` is what a worker is handed and exits 1 on an atomic slug — an
atomic is shown, not briefed.

Workflows live at `.pearde/workflows/`, so a board is needed to read one. With
none in scope, say where the library would be; adding a file and attaching a
slug to a PRD are orchestrator writes, and neither happens uninvited.
