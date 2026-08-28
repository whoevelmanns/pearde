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

## Job 3 — `body_has_open_box` takes the gates' matcher, and `BOX_RE` does not

Added 2026-08-28 by `@infra/gates-adopt-the-best-matcher` spec04. That node
moved mitosys, model and realm onto `shared`'s wide matcher — any of
`-`/`*`/`+`, any run of spaces, plus an ordered-marker arm — so as of today:

| reader | matcher | population |
|---|---|---|
| all four trees' `done_boxes_are_ticked` | `-`/`*`/`+`/`1.`/`1)`, any spacing | `prd.md`, whole file |
| `resources/board/plan.py:306` `body_has_open_box` | `l.lstrip().startswith("- [ ]")` | `prd.md`, whole file |
| `resources/board/plan.py:240` `BOX_RE` | `^\s*[-*]\s+\[([ xX])\]` | `specs/*.md`, `## Acceptance` only |

**The divergence widened rather than closed.** Before that node, the gates and
`body_has_open_box` were the same literal string test. After it, a `* [ ]` box
is red to every tree's gate and invisible to `collect` — the exact inversion of
the reason `body_has_open_box` exists, which is that `collect` must not name a
PRD a gate would reject.

**`BOX_RE` is not the disagreement, and the master board's own PRD said it was.**
`BOX_RE` reads a different set of files under a different heading rule to
produce a progress fraction rather than a verdict. Its `[-*]` class was never
the gates' class. Matching them would be matching two rules that answer two
questions.

**Why this matters more here than on any tree.** `infra/prds`, the master
board, carries no Rust workspace and therefore no gate. `body_has_open_box` is
the only box reader that ever looks at it. On the four member boards the narrow
matcher has a gate behind it; on the master board it is alone.

### Blast radius, enumerated rather than re-derived

- **Code that imports or executes `plan.py` (6):** `resources/board/serve.py`
  (`import plan as planlib`, and it calls `acceptance_of` directly at `:530`),
  `resources/board/render.py`, `resources/guard.py`, `resources/doctor.sh`,
  `resources/memos.py`, `resources/questions.py`.
- **Function-level call sites (2):** `acceptance_of` at `plan.py:276` and
  `serve.py:530`; `body_has_open_box` at `plan.py:344` only, inside `standing`.
  `BOX_RE` is used only by `acceptance_of`, at `plan.py:254`.
- **Boards it plans (6):** `infra/prds` (the master) and its four members
  `mitosys/prds`, `model/prds`, `realm/prds`, `shared/prds`, plus `pearde/prds`,
  which is its own board and not a member.

`plan.py` is installed once, not vendored per tree, so a change to
`body_has_open_box` changes the `collect` line on all six boards at once, and
`serve.py`'s live view re-reads it without a restart.

`- [~]` stays a closure under the wider matcher — a struck box's brackets are
not empty — so `../prds/memos/struck-box-spelling.md`'s claim that the mitosys
gate, the realm gate and `body_has_open_box` all read `- [~]` as a closure
stays true afterwards. Say so in the report rather than leaving it to be
re-checked.

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
- [ ] `body_has_open_box` takes the same matcher the four trees' gates take —
      any of `-`/`*`/`+`, any run of spaces, and the ordered arm — lifted out
      of the comprehension so it can be read beside
      `shared/conserved/tests/done_boxes_are_ticked.rs`
- [ ] `BOX_RE` is left byte-unchanged, and its docstring says why: a different
      population (`specs/*.md`, `## Acceptance` only), a different job (a
      progress fraction, not a verdict), and a `[ xX]` capture that
      deliberately neither closes nor counts `[~]`
- [ ] `body_has_open_box`'s docstring no longer says mitosys's gate is scoped
      *"under `## Acceptance`"* — all four gates have been whole-file since
      2026-08-28, so the "widest of the two" reasoning no longer describes two
      things
- [ ] The break-it proof for this job is re-run by the implementer and quoted,
      not inherited: a `* [ ]` box planted in a held PRD's `prd.md` suppresses
      that PRD from `collect:` after the change, and does not before it; the
      planted box is reverted and `git status --porcelain` on that board is
      quoted clean afterwards
- [ ] The report states that `- [~]` is still a closure under the wider
      matcher, so `../prds/memos/struck-box-spelling.md`'s claim about the
      three readers stays true
- [ ] `resources/index.py check` is run and its output quoted
- [ ] `resources/memos.py check` is run and its output quoted
- [ ] `resources/doctor.sh` is run and its output quoted
