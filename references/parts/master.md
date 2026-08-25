# Master boards

One plan across several repos, without moving a file.

A **master board** merges other boards to plan across projects: one scan, one
plan, one timeline, one progress line over several repos.

```yaml
# prds/settings.md, at the master
---
name: master
language: English
workers: 6
pipeline: 4
members:
  - ../mitosys/prds
  - model: ../model/prds
---
```

- `members:` in `settings.md` **is** what makes a master board. Otherwise it is
  an ordinary board: its own PRDs, memos, view.
- An entry is `- <path>` or `- <name>: <path>`. A relative path resolves
  against the master's `prds/`. A path at a repo root gains `/prds`. The name
  defaults to the directory the board sits in, and `<name>: <path>` pins it.
- **Nothing moves.** Every member keeps its own `prds/`, `settings.md`,
  `memos/`, view. PRDs, specs and memos are written where they live. The master
  holds only the plan and the progress line.

**Addressing.** A member PRD is `@<member>/<rel>` board-wide —
`@model/nucleus`. A PRD directory is never named `@…`, so a qualified address
cannot collide with the master's own PRDs. Every handle takes it: `run
@model/nucleus`, `needs: @model/nucleus`.

**The master is where you work.** One orchestrator, on the master. It scans
every member, dispatches their workers, and writes each transition into that
PRD's own `prd.md` at its real path — exactly one file per PRD, the member's.
A member session working its own board while a master session works the group
is the forbidden two-orchestrators case.

**Reconcile.** A transition in one member re-orders the whole board:

```sh
python3 @resources/view/plan.py reconcile [board]   # schedule recomputed, anchor kept
```

The live service watches every member and reconciles within about a second.
`plan` re-anchors the schedule on today. `reconcile` only re-orders.

**Across a board boundary:**

| thing                            | scope                                                                                  |
|----------------------------------|-----------------------------------------------------------------------------------------|
| `prd.md`, specs, memos, `state`  | the member. Written where the PRD lives, never at the master                             |
| `needs:`                         | the whole master board. Resolved in the PRD's own board first; across boards it is `@<member>/<prd>`. A bare name matching two boards is ambiguous, reported, and ignored |
| `footprint:`                     | qualified with the member name before any overlap check — two repos touching `src/lib.ts` are not one file. An **absolute** path is left as written, so a deliberate cross-repo overlap still clashes |
| `language`                       | the PRD's own board. The master's is for its own PRDs and the round                      |
| `workers`, `pipeline`            | the master — it is the one dispatching                                                   |
| `complexity` scoring             | the member — one repo's units do not size another's                                      |
| `repo` for a worker brief        | the PRD's own `repo:`, else the member's repo root — the directory holding its `prds/`   |

**Naming.** The first round that meets a master board with no `name:` asks the
user for one and writes it to `settings.md`. Until then the name is inferred
from the members (`mitosys+model`) — a placeholder, not an answer.

**On the master's own board:** only PRDs spanning more than one member. True of
one member alone → it belongs on that member's board.
