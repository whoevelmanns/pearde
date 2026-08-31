---
vision: One command moves the states, the board organises itself toward a declared destination, and a person reads one live page — nothing is done by hand on the board that a tool can do.
terminals:
  - the-board-runs-itself
---

# The destination

pearde today is a board of files, a loop a model runs by reading rules, and a
page that draws the board live. It works: nine boards on one daemon, 268 PRDs
on the master, 209 of them done. It costs too much and asks too much. A collect
is a dozen hand edits. A split is a model creating directories. A brief is
composed from three files at every dispatch. A first run asks a question. A
newcomer meets eleven skills and twenty-four scopes before the first PRD.

The design is right — files are the truth, one orchestrator writes state,
workers do the work, boxes are the live signal, the view is a reader of files.
The cost is in what the model still does by hand. This is the destination, in
five sentences:

- A **PRD** says what to build. A **spec** is one unit of how. Nothing else is
  needed to start.
- Every transition is **one command that checks its own gate**. The
  orchestrator chooses; the tool moves.
- A PRD too big for one sitting **splits itself** into children, and the board
  nests as it grows.
- A board is **created by one command that asks nothing**, and orders its queue
  toward the vision it declares in this file.
- **One page, live**, says what is happening, what is waiting on you, and what
  the session owes.

## Measured today — the numbers this moves

| measure | 2026-08-28 | done when |
|---|---|---|
| tool calls to collect one finished PRD | ~12 — grep the boxes, `git add` per path, three frontmatter edits, a message, the progress line, the round file, `POST /report` | 1 — `pearde collect` |
| files a worker brief is composed from | 3 per dispatch — `workers.md`, `personas/<id>.md`, `workflows.py brief` | 0 — `pearde brief <prd>` prints it |
| a REFINE split | the model creates N directories and N `prd.md` by hand | `pearde refine <prd>` from the analyst's table |
| a first run | `doctor --fix`, copy a settings block, one question | `pearde init` — no question |
| reference prose the loop executes | 2,037 lines in `references/parts/`; `loop.md` alone is 302 | the same rules as the spec of ~15 commands; `loop.md` under 120 lines |
| what a newcomer meets first | 11 skills, 29 scopes, 22 parts | one quickstart, three rings |
| the vision axis | `prds/vision.py` on one board, outside the skill, already cited by `order.md` | `prds/vision.md` read by `plan.py` on every board |
| worker liveness | a judgment — "no live worker" is the model's guess | `silent <age>` on the scan line and the page, from the files |

## What does not move

- The nine states, the gates on `specced` and `done`, one orchestrator per
  board, and the frontmatter contract.
- Files are the truth. No database, no service the board needs to plan.
- Python 3 stdlib, no build step, nothing leaves the machine.
- The writing rules of `references/language.md` for every document an agent
  reads. The README gets a human reader and a human shape.
