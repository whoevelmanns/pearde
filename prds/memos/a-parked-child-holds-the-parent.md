---
memo: a-parked-child-holds-the-parent
kind: decision
status: open
subject: scan's ready band ignores a parked child; claim's gate counts it — one rule has to win
date: 2026-08-28
prds:
  - the-board-runs-itself/transitions-are-commands
---

# a-parked-child-holds-the-parent — two readers of one rule, disagreeing on the same second

## Decision

Open. Found by the master-board session on 2026-08-28: `scan` lists
`@mitosys/p6-rust-core` as `ready`, and `claim @mitosys/p6-rust-core <w>`
refuses with `leaf: has children not done — p6n-chat-tui`. That child is in a
parked, user-owned state. `plan.py`'s dispatchable test does not count a
parked child; `transitions.py`'s `gate_claim` does. Not filed as a PRD: the
derived tripwire is at parity board-wide and is with the user.

## Why

@references/parts/board.md: a parent with children is not dispatchable until
every child is `done`. @references/parts/states.md: a parked state is the
user's own, never dispatched, out of every count. The two sentences never
said what a parked child means for its parent, so the two readers guessed
differently. A parked child is neither done nor coming; the parent cannot
land after it, which is what `order.md`'s "a parent lands after its children"
makes of it — so the gate's reading is the stricter and the right one, and
`scan` should stop offering the parent. The cost of the other reading is a
round that dispatches a parent whose child the user set aside.

## Alternatives considered

**Scan is right, the gate is loose.** A parked child would then be treated
as done for the parent's sake. Rejected on `order.md`: work flows to the
leaves, and a leaf the user parked is a leaf the board has been told not to
finish — so the parent is not finishable either, and offering it invites a
worker at a tree the user has paused.

**Both readers call one function.** The fix whichever reading wins:
`gate_claim` and the ready test share one predicate in `plan.py`, so they
cannot disagree again. That is the shape the fix takes; the memo is open on
which reading, not on the shape.

## Consequences

- Until settled, `scan`'s ready band can offer a parent that `claim` refuses;
  the refusal names the child, so nothing is dispatched wrongly — a round
  loses one call, not a worker.
- Two verify-block spellings fail at collect though they pass for a worker:
  `grep -c … # 0` (grep exits 1 on the wanted zero) and `grep …; test $? -eq
  1` (under `set -e` the grep aborts first). `! grep -q …` is the spelling
  that works — the library already carries the first as a `## Fails when`
  row; the brief header is the other place for it.
