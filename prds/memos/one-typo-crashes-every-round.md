---
memo: one-typo-crashes-every-round
kind: note
status: open
subject: a non-numeric complexity in any spec crashes scan board-wide, three lines from the try/except that would prevent it
date: 2026-08-28
---

# one-typo-crashes-every-round — complexity is the one weight read without a guard

## Decision

Not decided. This records a reproduced crash and puts the fix to the user,
because the tripwire is at parity and the deliverable was ruled to finish
first — but unlike the other parked findings, this one takes the board down
for every session on it, so it is written up the moment it was measured
rather than at the end of the round.

## Why

`resources/board/plan.py:244`, inside `spec_data`:

```python
est += float(fm.get("complexity", 0) or 0) or hours(fm.get("est", ""))
```

No guard. `spec_data` is called for every live PRD by `compute_plan`, which is
called by `cmd_scan` — step 1 of every round. So one spec file anywhere on the
board with a non-numeric `complexity` takes down the scan, the plan, the
progress line and the view, for **every** session working that board.

**Reproduced**, fixture: a scratch board outside the repo with one `specced`
PRD whose `specs/spec01.md` carries `complexity: x`.

```
File ".../resources/board/plan.py", line 244, in spec_data
    est += float(fm.get("complexity", 0) or 0) or hours(fm.get("est", ""))
ValueError: could not convert string to float: 'x'
```

Found by another session's `specced-is-a-command` analyst, on the third run of
`probe-then-spec`, in a harness of its own.

The argument for fixing it is not the crash on its own — it is that **the
codebase already knows the answer and complexity is the outlier.** Three lines
of the same file, at `:823`:

```python
    pr = float(p["fm"].get("priority", 0))
except (TypeError, ValueError):
    pr = 0.0
```

`priority` is guarded. `complexity` is not. Two weights, read the same way, one
of which is defensive — that is not a considered asymmetry, it is a line
somebody wrote without the guard.

It also has an unusually cheap trigger. `complexity` is written by an analyst,
by hand, on every spec file — it is one of the two keys `references/parts/contract.md`
requires — so the population of writers is every worker the board has ever
dispatched, and the failure is a typo.

## Alternatives considered

**Fix it now as an instrument repair.** One `try`/`except` matching the one
already three lines away. It lost today on a coordination fact, not on merit:
a second session is writing `resources/board/plan.py` additively right now,
and a change to a shared file made outside any PRD is the edit that reappears
later as a mystery — this repo already carries one that landed exactly that
way, a count that was wrong the day it was written.

**File it as a derived PRD.** It is one by @references/parts/derived.md's test.
It lost on the tripwire: three derived PRDs are already parked by the user's
decision, and filing a fourth is the board working on itself.

**Wait for it to fire.** Rejected. The cost is not proportional to the defect:
a typo produces a stack trace with no PRD name in it, in the one command both
sessions run first, and the person reading it has no reason to suspect a spec
file.

## Consequences

- Until this is fixed, `complexity` is an unguarded input on a critical path.
  A worker that writes `complexity: high` instead of a number stops both
  sessions.
- The fix should be paired with the same guard on any other unguarded
  `float()` over frontmatter in that file, found by census rather than by
  memory — `weight_of` and `progress_terms` read `complexity` too.
- It says nothing about whether a bad value should be `0`, the board average,
  or a reported problem. `priority` chooses `0.0` silently; a weight that
  silently becomes `0` makes a PRD weightless and moves it in the plan, which
  may be the wrong default for this key. That is the decision the fix has to
  make, and this memo does not make it.
