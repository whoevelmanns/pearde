---
name: view
description: Look at the board and edit it — a local service rendering every PRD as a timeline ordered by dependency, importance and complexity, with the critical path marked and edits written straight back to the files. Also the one-shot render when no service is wanted. Binds 127.0.0.1, needs Python 3, nothing leaves the machine. Use for "/view", "open the board", "show me the board", "show me the plan", "gantt", "timeline", "what is the critical path", "what runs next", "reconcile the plan", "re-order the board", "board ui", "visualise the prds".
---

Read @references/parts/view.md. The scopes are `@@view` and `@@order`.

```bash
python3 @resources/board/serve.py ensure    # start it, register this board, print the URL
python3 @resources/board/serve.py status    # what it is watching
python3 @resources/board/serve.py stop      # end it
python3 @resources/board/plan.py plan       # the frontier and the queue, no service
python3 @resources/board/plan.py gantt --open  # prds/.view.html, self-contained
python3 @resources/board/plan.py reconcile  # recompute after anything moved
```

- **One daemon per machine**, singleton by port bind. `ensure` on another
  board registers it with the same service; every board is listed at `/`.
  `PEARDE_PORT` moves the port.
- **Nothing leaves the machine.** It reads the board's files and writes the
  same files back on an edit.
- **No axis is a clock.** The order comes from dependency, importance and
  complexity — @references/parts/order.md is why, and it is the thing to read
  before arguing with the sequence.
- The board plans and reads without any of this. The view is how a person
  looks at it.
