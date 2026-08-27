---
state: open
origin: derived
from: exemptions-name-their-reason
priority: 55
complexity: 0
blast-radius: high
repo: pearde
footprint:
  - references/parts/loop.md
  - resources/board/plan.py
---

# finished-counts-both-files — the prose still says the narrow thing, and the code that says otherwise is not committed

`resources/board/plan.py` was changed on 2026-08-27 to define a finished PRD
the wide way. `references/parts/loop.md` still defines it the narrow way, and
it is the sentence a cold reader reaches first.

When this is done: the two agree, the code that made them disagree is
committed, and a worker — not the orchestrator who wrote it — has re-run the
proof.

## The two lines that disagree

| file | says |
|---|---|
| `references/parts/loop.md:100` | *"A PRD is **finished** when every acceptance box in its specs is `[x]`. That is not a state — it is a condition read off the specs on disk, and what step 1 sweeps for on a session that starts with work already done."* |
| `resources/board/plan.py:343` (inside `standing`) | `ready = bool(held and total and closed == total and not body_has_open_box(prd))` |

The code is the decided rule. The prose is the one that was superseded and not
edited.

### The replacement sentence

> A PRD is **finished** when every acceptance box in its specs is `[x]` **and**
> its own `prd.md` carries no open box. That is not a state — it is a condition
> read off both files on disk, and what step 1 sweeps for on a session that
> starts with work already done.

`- [~]` is a closure in both files. `- [x]` is a closure.

The decision is `prds/memos/done-counts-which-boxes.md` on the master board at
`../prds/memos/done-counts-which-boxes.md`, taken by the user 2026-08-27. **It
is not re-argued here.** This PRD carries the edit, not the case for it.

That memo also names the discipline this PRD exists to satisfy: *"one of the
two rules is edited in the same commit as the code or config that proves it.
Leaving both is what produced this."*

## Job 1 — the code is on disk and not committed

Measured 2026-08-27, and it **refutes** what the master board recorded:

```
$ git -C pearde status --porcelain -- resources/board/plan.py
 M resources/board/plan.py

$ git -C pearde show HEAD:resources/board/plan.py | grep -c 'body_has_open_box'
0

$ git -C pearde diff --numstat -- resources/board/plan.py
155	8	resources/board/plan.py
```

`prds/exemptions-name-their-reason/prd.md` § *What the orchestrator already did*
states the change is *"already implemented and committed"*. It is implemented.
**It is not committed** — `body_has_open_box` does not exist in `HEAD`, and the
whole change is 155 added / 8 deleted lines of unstaged working tree, mtime
`2026-08-27 10:30`.

That is the same shape the master board repaired in
`@model/next-wave/signed-ledger` and is holding open on
`@mitosys/p8-membrane/p8b-lua-gene-edge`: work on disk, no commit, every later
measurement standing on unrecorded source. One `git checkout` erases the
decided rule and every board reverts to the narrow one silently.

**Committing it is this PRD's first job**, before the prose edit and before the
verification.

## Job 2 — the code was never worker-verified

| symbol | line | state |
|---|---|---|
| `body_has_open_box` | `resources/board/plan.py:305` | landed on disk, uncommitted, **not worker-verified** |
| `standing` | `resources/board/plan.py:326` | landed on disk, uncommitted, **not worker-verified** |

Both were written by the orchestrator in the round that raised the question:
no spec, no dispatch, no worker report. The only evidence on record is the
author's own, which is the one check an author cannot run from inside their
own frame.

The board cites `standing` at `:325`. It is at `:326` — an off-by-one in the
citation, corrected here and in any document that repeats it.

**The implementer re-runs the break-it proof and quotes its own output.** Not
copied from the memo, not quoted from this PRD:

1. Tick `realm/prds/done-means-done/realm-classify/prd.md`'s two open `prd.md`
   boxes temporarily. Run `plan`. Record the `collect:` line — the memo
   predicts `collect: 1 finished`.
2. Revert the ticks. Run `plan`. Record the `collect:` line — the memo predicts
   none.
3. Revert `plan.py` to `HEAD`. Run `plan`. Record the `collect:` line — the
   memo predicts `collect: 2 finished`, naming `@realm/02-linux-driver` and
   `@realm/done-means-done/realm-classify`, both correctly `blocked`.
4. Restore `plan.py`. Leave `realm-classify` exactly as found.

A step whose output disagrees with the prediction is the finding, not a
failure of the run. Record it either way.

## The one behaviour a reader will otherwise get wrong

**`frac`, `closed` and `total` stay the specs' numbers. Only `collect`
widens.**

| number | reads | drawn on |
|---|---|---|
| `frac` / `closed` / `total` | `specs/*.md`, `## Acceptance` only, via `acceptance()` | the lane bar — the only thing that moves while a worker works |
| `collect` | the specs **and** `prd.md` whole-file, via `body_has_open_box` | the collect line — whether a gate would accept this PRD as `done` |

The two deliberately answer different questions, and the docstring on
`standing` says so. A lane bar at 100% beside a PRD that does not appear in
`collect:` is correct output, not a bug: the specs are closed and `prd.md` is
not. Folding several hundred static `prd.md` requirement boxes into `frac`
would swamp the one live signal the plan has.

`references/parts/loop.md` says this too, so the next reader does not
re-unify them.

## The verify

`pearde/prds/settings.md` § Deliverable: `resources/index.py check`,
`resources/memos.py check` and `resources/doctor.sh` are this board's gate. A
PRD here is `done` when all three are green and its own acceptance boxes are
closed.

## Constraints

- Do not widen `frac` / `closed` / `total`.
- Do not change `acceptance()`. It reads `specs/*.md` under `## Acceptance` and
  stays that way.
- `- [~]` stays a closure. The test is `startswith("- [ ]")`, not
  `acceptance_of`'s `== "x"`.
- Do not re-argue the decision. `prds/memos/done-counts-which-boxes.md` holds
  it and its alternatives.
- Leave `realm-classify` as found. The break-it proof edits another repo's
  board temporarily and reverts it.

## Pointers

- `../prds/memos/done-counts-which-boxes.md` — the decision
- `../prds/exemptions-name-their-reason/prd.md` — the master-board parent, and the section this PRD refutes
- `../shared/learnings/exemptions-name-their-reason.md` — the four trees' half of the same rule
- `references/parts/loop.md:100` — the sentence
- `resources/board/plan.py:305`, `:326` — the code

## Acceptance

- [x] `resources/board/plan.py`'s working-tree change is committed, and
      `git show HEAD:resources/board/plan.py | grep -c 'body_has_open_box'`
      returns non-zero with the output quoted

      **Closed by the orchestrator, 2026-08-27, sha `6cd1edf`** — not by an
      implementer, because it cannot be: `@references/parts/workers.md` names
      "a box asking for a commit message" as one of exactly two unclosable
      boxes to catch when specs land, and committing is the orchestrator's
      act. The box is otherwise right to exist, so it is closed rather than
      struck.

      ```
      $ git -C pearde show HEAD:resources/board/plan.py | grep -c 'body_has_open_box'
      2
      ```

      **Partially staged, on the user's call.** `plan.py` was dirty before the
      round: 31 of its 155 added lines are this contract's, ~124 are another
      session's in-flight work. Only these hunks were committed; the rest stay
      in the working tree. The staged file was run in its real location before
      the commit and answered `collect` correctly, so the committed state is
      not one that was never executed.
- [ ] `references/parts/loop.md:100` reads the replacement sentence above,
      naming both files and `- [~]` as a closure
- [ ] `references/parts/loop.md` states that `frac`/`closed`/`total` stay the
      specs' numbers while `collect` reads both files
- [ ] The break-it proof is re-run by the implementer and all four steps'
      `collect:` lines quoted, with any disagreement against the memo's
      prediction recorded
- [ ] `realm/prds/done-means-done/realm-classify/prd.md` is byte-identical
      before and after, checked with `git -C realm status --porcelain`
- [ ] `resources/index.py check` is run and its output quoted
- [ ] `resources/memos.py check` is run and its output quoted
- [ ] `resources/doctor.sh` is run and its output quoted
