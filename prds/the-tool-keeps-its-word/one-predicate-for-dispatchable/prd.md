---
state: done
origin: requested
actual: 1.1h
commit: 3264820
priority: 64
complexity: 13
blast-radius: high
repo: pearde
workflow: probe-then-spec
footprint:
  - resources/board/plan.py
  - resources/board/transitions.py
  - references/parts/states.md
  - references/parts/order.md
  - references/parts/board.md
  - prds/memos/a-parked-child-holds-the-parent.md
  - prds/workflows-on-the-board/workflow-attach/probe/verify.sh
  - resources/board/brief.py
---

# one-predicate-for-dispatchable — scan's ready band and claim's gate read one function, and a parked child holds its parent

When this is done, a PRD `scan` lists as ready is a PRD `claim` accepts, on
every board, because both call one predicate in `plan.py`; and that
predicate says a parent whose child is parked is not dispatchable.

## The consequence, named

`prds/memos/a-parked-child-holds-the-parent.md`: on the master board, `scan`
listed `@mitosys/p6-rust-core` as ready and `claim @mitosys/p6-rust-core`
refused with `leaf: has children not done — p6n-chat-tui`, a parked child.
`plan.py`'s ready test ignores parked children; `transitions.gate_claim`
counts them. Two readers of one rule, disagreeing on the same second.

## The rule

- `dispatchable(prd, prds, settings) -> None | reason` lives in `plan.py`
  and is the only place the four gates are written: leaf (every child
  `done` — a parked child is not done and is not coming, so it holds the
  parent, per @references/parts/order.md "a parent lands after its
  children"), `needs:` all done, no footprint overlap with a `claimed` PRD,
  `workflow:` resolving. `compute_plan`'s ready band, `cmd_scan`'s
  `ready` section and `transitions.gate_claim` call it; `gate_claim` keeps
  its refusal wording by prefixing the reason.
- A parent held by a parked child is listed under `gated` with `held by
  <child> (parked)` — visible, never offered.

## Files

| file | change |
|---|---|
| `resources/board/plan.py` | `dispatchable()`; the ready band and the scan section call it; the `gated` line's reason |
| `resources/board/transitions.py` | `gate_claim` calls `plan.dispatchable`, keeps its prefixes |
| `references/parts/states.md` · `order.md` · `board.md` | one sentence: a parked child holds its parent; the four gates are one function |
| the memo | `status: decided` |

## Verify

- On a copy of the example board with `big/second` set to a parked state (`state: later`): `scan` lists `big` under gated with `held by big/second (parked)`, never under ready; `claim big w` exits 1 with the same reason.
- For every PRD `scan` lists as ready on the copy, `claim <prd> w --dry` (or `gate_claim`) returns no reason; for every gated one, it returns the reason the scan line shows.
- `transitions-are-commands/probe/verify.sh` (74) and `the-loop-is-commands/probe/verify.sh` (60) green, or each moved line named; `scan` byte-identical on the untouched example copy.

## Report

DONE · committed
