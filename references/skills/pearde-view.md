---
name: pearde-view
description: Look at the board and edit it — a local service rendering every PRD as a timeline ordered by dependency, importance and complexity, with the critical path marked and edits written straight back to the files. Also the one-shot render when no service is wanted. Binds 127.0.0.1, needs Python 3, nothing leaves the machine. Use for "/view", "open the board", "show me the board", "show me the plan", "gantt", "timeline", "what is the critical path", "what runs next", "reconcile the plan", "re-order the board", "board ui", "visualise the prds".
---

Read @references/parts/view.md — the service and its singleton, the sections,
the axes, the writers, the deep links, and what the board keeps on disk.
@references/parts/order.md is why the sequence is what it is, and it is the
file to read before arguing with it. The scopes are `@@view` and `@@order`.

```bash
python3 @resources/pearde.py view           # start it, register this board, print the URL
python3 @resources/pearde.py view status    # what it is watching
python3 @resources/pearde.py view stop      # end it
python3 @resources/pearde.py plan           # the frontier and the queue, no service
python3 @resources/pearde.py gantt --open   # prds/.view.html, self-contained
python3 @resources/pearde.py reconcile      # recompute after anything moved
```

The board plans and reads without any of this. The view is how a person looks
at it.
