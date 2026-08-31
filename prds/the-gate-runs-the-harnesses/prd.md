---
state: done
origin: derived
actual: 1.4h
from: complexity-is-guarded-like-priority
priority: 65
complexity: 22
blast-radius: mid
repo: pearde
footprint:
  - resources/doctor.sh
  - references/parts/doctor.md
  - references/settings.md
  - prds/the-gate-runs-the-harnesses/probe
---

# the-gate-runs-the-harnesses — a thousand checks nobody runs

When this is done, `bash resources/doctor.sh` runs the board's harnesses and
goes red when one does, so a green gate means the checks passed rather than
that nobody asked.

## The consequence, named

```
$ grep -rn 'verify.sh' resources/ .claude
(nothing)
```

Seventeen harnesses on this board, roughly a thousand checks between them, and
**nothing runs any of them**. No CI — this repo has none. No git hook —
`.git/hooks` holds only samples. No `doctor` row. Every green total recorded
in a report today exists because a person remembered to type the command.

Measured 2026-08-28. That day the board shipped a matcher ported into
`plan.py` from four Rust gates and guarded every number read off a file a
person typed; both are protected by acceptance boxes in harnesses that run
only when asked. `complexity-is-guarded-like-priority` closed nine unguarded
`float()` reads and named this gap in its own report rather than papering over
it: *nothing stops the next unguarded `float()` from being written; the AST
census holds only while that harness is run.*

That is the requested work this gets wrong. Every PRD on this board is closed
against `prds/settings.md` § Deliverable, and two of its three gates —
`index.py check` and `memos.py check` — do run. The third thing a PRD is
closed against, its own acceptance harness, runs at the moment it is written
and possibly never again.

## The shape, and the one it beat

A `doctor` row per harness, red when its count falls below a number recorded
elsewhere, is the obvious design and it is wrong. A recorded count is a second
copy of a fact the harness already states, and this board has now paid twice
for exactly that shape: a sentence saying "six mechanical actions" over a list
of seven, and a `## Fails when` count pinned to a snapshot the first real run
destroyed. Both were repaired by **deriving the number from the thing it
counts**, never by keeping a ledger beside it.

So: the expected count comes from the harness itself. `workflow-seed`'s probe
already pins its own denominator —

```sh
[ "$((PASS+FAIL))" = 39 ] || no "expected 39 checks, ran $((PASS+FAIL))"
```

— which makes a dropped check fail loudly instead of printing a smaller total
and exiting 0. A harness that pins its own denominator needs no ledger: run
it, read its exit code. A harness that does not pin one is the finding.

## Files

| file                          | change                                                                                                   |
|-------------------------------|--------------------------------------------------------------------------------------------------------------|
| `resources/doctor.sh`         | a `harnesses` row: `find prds -name verify.sh`, run each, report `N of M green`. `broken` on any non-zero exit, naming the harness and its first FAIL line. `off` when the board has none. Slow by construction — see Rules |
| `references/parts/doctor.md`  | the row in the table and its bullet, saying what `off`/`ok`/`broken` mean and why the row is opt-in |

## Rules

- **The count is the harness's own.** No ledger, no recorded expected totals,
  no second copy of a number the file already carries. A harness that does not
  pin its denominator is reported as unpinned rather than trusted.
- **Opt-in, because it is slow.** Seventeen harnesses take on the order of a
  minute, and `doctor` is run to answer "is this wired up" in a second. A
  `harnesses: on` key in `prds/settings.md`, default off, and a
  `doctor --harnesses` flag that runs them regardless. A gate nobody can
  afford to run is the defect this PRD is fixing, repeated.
- **A harness outside this board is not this board's business.** Run what
  `find prds -name verify.sh` returns and nothing else.

## Verify

- A board whose harnesses all pass: the row reads `ok · N of N green`.
- One acceptance box flipped to a failing check in a scratch copy: the row
  reads `broken`, names that harness and its first FAIL line, and `doctor`
  exits 1. Restore.
- A harness with no pinned denominator: reported as unpinned in the row's
  detail, and the row is not green on its account alone.
- With `harnesses:` absent from settings, `doctor` runs no harness and its
  wall-clock is unchanged from before this PRD — measured, both numbers quoted.
