---
state: done
origin: requested
actual: 1.4h
commit: e2890a0 · infra 9776cb9
priority: 60
complexity: 50
blast-radius: mid
repo: pearde
workflow: probe-then-spec
needs:
  - one-command
footprint:
  - /Users/feb/dev/infra/prds/vision.py
  - /Users/feb/dev/infra/prds/allboards.py
  - /Users/feb/dev/infra/prds/.vision.json
  - /Users/feb/dev/infra/prds/settings.md
---

# vision-is-first-class — every board can declare where it is going, and the plan orders toward it

When this is done, `prds/vision.md` is a board file `plan.py` reads on any
board, plain or master; the axis in @references/parts/order.md is computed by
the skill rather than by a script on one board; and `prds/vision.py` and
`prds/allboards.py` on the master board are deleted with nothing lost.

## Contract

`prds/vision.md`:

```
---
vision: <one sentence — the destination>
terminals:
  - <prd>              # a PRD whose completion is the vision; `@<member>/<prd>` on a master
edges:
  - "<from> -> <to>"   # a dependency not written as needs:, usually across boards
---

# <The destination, in prose>
```

| key | required | is |
|---|---|---|
| `vision` | yes | one sentence, printed on the scan's first line |
| `terminals` | no | PRD addresses. None means no axis: the board orders as today |
| `edges` | no | `A -> B` pairs, the same resolution as `needs:` — plus one rule `needs:` lacks: `@<own-name>/<rel>`, where `<own-name>` is this board's `name:`, addresses the board's own PRDs, so a master can name its own terminals beside its members' |

`plan.py`:

- `axis_depth` reads `vision.md`, not `.vision.json`; `.vision.json` is
  neither read nor written.
- The depth of a PRD is the length of the longest serial chain from it to a
  terminal, over `needs:` plus `edges:`, where a `done` prerequisite costs
  nothing (`vision.py:149`) and a parent lands after its children
  (`vision.py:121-124`) — naming a parent as terminal puts its subtree on the
  axis. A live PRD from which no terminal is reachable is **off-axis**; `on`
  and `off` count live PRDs only, as `vision.py` does.
- `scan`'s first line carries `axis: <on> on · <off> off`; a line off the
  axis carries `· off-axis`; a board with no terminals prints neither.
- `pearde vision` prints the axis for a person — depth, the critical chain,
  the off-axis set. `pearde vision --json` prints what `.vision.json` held.
  `pearde vision --next` is the frontier in axis order — the same list as
  `plan`'s ready set, printed alone.
- The page is untouched. Its *to the vision* pill, ★ chain and `#crit=1`
  read the weighted critical path (`CPM`), not the axis — measured by the
  analyst; the one vision hook `view.js` has, `DATA.vision.purpose`, is never
  set by `gantt_payload`. Wiring the sentence into the payload is
  `the-page-shows-the-round`'s, with the `view.md` claim beside it.

## Rules

- **The master's file is already this format.** `/Users/feb/dev/infra/prds/vision.md`
  moves nothing; its `@master/…` terminals resolve by the own-name rule
  above once its `settings.md` says `name: master` (it does). The scripts
  beside it go once `pearde vision --json` on that board equals the last
  `.vision.json` it wrote, depth for depth. `plane_name()` and the
  `.plane.env` read in `plan.py` go in the same commit — Plane is gone, and
  the own-name rule is what replaces the prefix it supplied.
- `terminals:` naming no PRD on the board is a `doctor` failure under a new
  `vision` row; so is an edge whose end names nothing. Read by `plan.py`, the
  one reader.
- `init` writes the template with `terminals:` commented out —
  `init-asks-nothing` does that once this PRD defines the file.

## Files

| file | change |
|---|---|
| `resources/board/plan.py` | `axis_depth` from `vision.md`; `cmd_vision`; the scan line; the `off-axis` mark |
| `references/templates/vision.md` | new |
| `references/parts/order.md` | "The axis is `prds/vision.md`" — the `vision.py` sentence leaves |
| `references/parts/board.md` | `vision.md` in the layout |
| `references/parts/master.md` | terminals and edges address members as `needs:` does |
| `resources/doctor.sh` | the `vision` row |
| `index.md` · `references/files.md` | the template's rows; `@@order` gains it. `vision` registers through `COMMANDS` in `plan.py` |

## Verify

- On the master board: `pearde vision --json` equals `.vision.json`'s depths
  for every PRD both name, measured before `vision.py` is deleted, output
  quoted.
- On a copy of the example board with `terminals: [big]`: `next` is
  off-axis, `big/second` at depth 1, `big` at 0; the scan's first line says
  `axis: 2 on · 4 off` — six live PRDs, `big` and `big/second` on.
- With no `terminals:`, `scan` output is byte-identical to before this PRD.
- `doctor` reports `vision broken` on a terminal naming no PRD.

## Report

DONE · committed fa82dd3
