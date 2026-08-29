---
memo: a-container-cannot-reach-done
kind: note
status: decided
subject: a parent PRD whose children are all done has no path to done through the tool
date: 2026-08-29
prds:
  - workflows-on-the-board
---

# a-container-cannot-reach-done — the state machine has no exit for a container

## Decision

Decided 2026-08-29, built in `collect-keeps-its-word` on
`one-predicate-for-dispatchable`'s predicate: **`collect` accepts a
container directly**, `open → done`. `dispatchable()` in plan.py is
the one word for the shape — children all `done`, no spec, no open
box of its own — `claim` refuses on it with `container: every child
done — pearde collect closes it`, `scan` lists it under collect, and
`collect <parent>` (or the bare `collect`) writes `done`, `actual:`
the children's sum and `commit:` the last child's in one commit
`<parent> — done: every child landed`. A separate `close` verb was
not taken: the band that lists finished work is the band that closes
it. A parent with specs or boxes of its own is never closed this way.

## Why

`workflows-on-the-board` has six children, all `done`, and no open box of its
own. Its contract is the sum of the children — @resources/board/plan.py calls
such a parent a container, weighs it at zero while its children are live, and
folds it out of the schedule the moment they finish. **The planner folds it
away. The state never moves.** It sits at `open` on a finished tree.

Reproduced, on the live board:

```
$ pearde claim workflows-on-the-board orchestrator --as engineer
▸ workflows-on-the-board: open → analyzing

$ pearde collect workflows-on-the-board --as engineer
collect: state is `analyzing` — collect closes `claimed` or `blocked`

$ pearde specced workflows-on-the-board --as engineer
specced: refused — workflows-on-the-board/specs/: no spec file —
         `specced` requires spec files on disk
```

`specced` is right to refuse: a container has no specs because its work is in
its children. But `claimed` is only reachable through `specced`, and `done` is
only reachable from `claimed` or `blocked`. So the one PRD shape that is
guaranteed to have no specs is the one shape that cannot be closed.

`references/parts/states.md` does not mention a parent or a container at all —
`grep -in 'parent\|container'` returns nothing — so this is not a rule written
and unenforced. It is a case the state machine was never told about.

The board hides it: a container weighs nothing while its children are live, so
it never appears as a thing waiting to be closed until the last child lands,
and then it appears as ordinary `open` work with an average weight and nothing
to do. `workflows-on-the-board` currently reads `p50 · w20` — a number invented
for a PRD whose work is finished.

## Alternatives considered

**A `close` transition for a parent with no live children and no open box.**
The narrow fix, and the one that matches how the planner already reasons — it
already computes exactly that condition to decide a container weighs nothing.

**Let `collect` accept a container directly**, `open → done`, when every child
is `done` and `prd.md` carries no open box. Fewer verbs, but it makes `collect`
mean two different things: verify-commit-close for work, and fold-away for a
container that has nothing to verify or commit.

**Leave it and close containers by hand.** Rejected on sight: `@@guard` exists
to refuse a hand-written `state:`, so the workaround for this gap is the one
thing the board is wired to prevent.

## Consequences

- Every parent PRD on every board reaches this. `workflows-on-the-board` is the
  first because it is the first tree here to finish.
- Until it is closed, a finished tree reads as open work with a fabricated
  weight, and the progress line counts it as not done — `asked 23/29` on this
  board includes a PRD whose six children all landed.
- It says nothing about a parent that has both children **and** work of its
  own. That shape exists and is not a container; the fix must not close it by
  accident.

## What this memo cost to find

I ran `claim` on the container to try to close it, which moved it `open →
analyzing` and left a claim on a finished tree. `sweep --apply` would not take
it back — the claim was seconds old and not silent past `claim-ttl` — and
`release <prd> open` was the way out. That is worth knowing before anyone
repeats the experiment on a board they care about.
