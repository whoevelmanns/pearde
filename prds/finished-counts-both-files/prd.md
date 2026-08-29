---
state: done
origin: derived
actual: 0.75h
commit: 41a46e6
from: exemptions-name-their-reason
priority: 55
complexity: 18
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
| `frac` / `closed` / `total` | `specs/*.md`, `## Acceptance

Every box below was reset to `- [ ]` and re-ticked only where this implementer
ran the check itself. The output quoted under each is this session's own.

- [x] `resources/board/plan.py`'s working-tree change is committed, and
      `git show HEAD:resources/board/plan.py | grep -c 'body_has_open_box'`
      returns non-zero with the output quoted

      **Closed by the orchestrator, 2026-08-27, sha `6cd1edf`** — not by an
      implementer, because it cannot be: `@references/parts/workers.md` names
      "a box asking for a commit message" as one of exactly two unclosable
      boxes to catch when specs land, and committing is the orchestrator's
      act. The box is otherwise right to exist, so it is closed rather than
      struck.

      **Re-run by this implementer**, since the command is one an implementer
      *can* run. `6cd1edf` is an ancestor of HEAD, and HEAD carries both
      halves — the function and its call site:

      ```
      $ git merge-base --is-ancestor 6cd1edf HEAD && echo yes
      yes

      $ git show HEAD:resources/board/plan.py | grep -c 'body_has_open_box'
      2
      ```

      **Partially staged, on the user's call.** `plan.py` was dirty before the
      round: 31 of its 155 added lines are this contract's, ~124 are another
      session's in-flight work. Only these hunks were committed; the rest stay
      in the working tree. The staged file was run in its real location before
      the commit and answered `collect` correctly, so the committed state is
      not one that was never executed.

      Still true today, and still not this implementer's to resolve:
      `plan.py` carries 151 added / 19 deleted uncommitted lines, of which one
      insertion after `question_counts` (`ANSWER_LINE_RE`, `QUESTION_HEAD_RE`,
      `_h2_sections`, `_qid`, `answers_of` — 60 lines) belongs to another
      session's asks-view work. It was neither reverted nor included in this
      PRD's footprint, and it is byte-intact: see § Failure-free footprint at
      the end.
- [x] `references/parts/loop.md:100` reads the replacement sentence above,
      naming both files and `- [~]` as a closure

      The citation is stale — the sentence is at `:158`, not `:100`; the file
      has moved under the PRD. Measured, not assumed:

      ```
      $ grep -n 'A PRD is \*\*finished\*\*' references/parts/loop.md
      158:A PRD is **finished** when every acceptance box in its specs is `[x]` and
      ```

      It names both files, and the paragraph under it names `- [~]` — and
      `- [x]`, and what a box is, which the replacement sentence in the body
      above does not go on to say:

      ```
      $ sed -n '158,169p' references/parts/loop.md
      A PRD is **finished** when every acceptance box in its specs is `[x]` and
      `prd.md` carries no open box of its own. That is not a state — it is a
      condition read off **both files** on disk, which is why the scan reads it for
      you: a PRD in its **collect** section is finished, and `boxes c/t` on any
      other line is how far a live one has got. Counting boxes by opening the specs
      yourself is the same number for the price of the whole file.

      `- [x]` and `- [~]` are both closures, in either file: a struck box is a
      contract term withdrawn with a reason beside it, never work still owed. And a
      box is whatever a tree's own `done` gate calls a box — any of `-`, `*` or
      `+`, or an ordered marker, with any run of spaces before the bracket — so
      that a PRD the board offers for collection is never one a gate would reject.
      ```
- [x] `references/parts/loop.md` states that `frac`/`closed`/`total` stay the
      specs' numbers while `collect` reads both files

      `:171-178`. The prose calls them `boxes c/t`, which is what the plan
      prints, rather than `frac`/`closed`/`total`, which is what the code
      calls them.

      ```
      $ sed -n '171,178p' references/parts/loop.md
      **`boxes c/t` and the collect line answer different questions, and are meant
      to disagree.** `c/t` is the specs' number and stays the specs' number:
      `specs/*.md` under `## Acceptance`, the only thing that moves while a worker
      works, which is what the lane bar is drawn from. Collect is the stricter
      question and reads `prd.md` whole-file as well. A bar at 100% beside a PRD
      that is not in **collect** is correct output, not a bug — the specs are
      closed and `prd.md` is not. Folding several hundred static `prd.md`
      requirement boxes into `c/t` would swamp the one live signal the plan has.
      ```
- [~] ~~The break-it proof is re-run by the implementer and all four steps'
      `collect:` lines quoted, with any disagreement against the memo's
      prediction recorded~~ — **struck: the fixture the four steps name no
      longer exists.** Measured here, not inherited:

      ```
      $ python3 -c "... P.scan('/Users/feb/dev/infra/prds') ..."
      @realm/02-linux-driver: state='done' held=False specs 21/21 open prd.md boxes=0 collect=False
      @realm/done-means-done/realm-classify: state='done' held=False specs 21/21 open prd.md boxes=0 collect=False
      ```

      Step 1 says "tick `realm-classify`'s two open `prd.md` boxes"; it has
      zero. Steps 1-3 predict `collect:` lines naming `@realm/02-linux-driver`
      and `@realm/done-means-done/realm-classify`; both are `state: done`,
      therefore not in a `HOLDING_STATE`, therefore unreachable by `collect`
      under **any** matcher — `standing()` requires `held` before it looks at
      a box. The steps are not merely unmeasured, they are unrunnable.

      **The disagreement against the memo's prediction, recorded:** the memo
      predicts `collect: 2 finished` at step 3 and `collect: 1 finished` at
      step 1. Neither can occur today. The prediction was true when the memo
      was written and the board has moved past it; nothing about the rule is
      refuted by that, only the fixture.

      The same propositions were re-run on a fixture that does exist — a held
      PRD whose specs are closed, built and removed by the probe — under
      `specs/spec01.md` box 7, with nine fixtures rather than four steps and
      HEAD beside the working tree. That is where the proof lives.
- [x] `realm/prds/done-means-done/realm-classify/prd.md` is byte-identical
      before and after, checked with `git -C realm status --porcelain`

      Trivially so, because the proof that would have edited it did not run.
      No line for it, and no line for anything under `done-means-done`:

      ```
      $ git -C /Users/feb/dev/infra/realm status --porcelain
       M prds/.history.jsonl
      ```

      The one line is realm's daily progress row, rewritten in place by a
      `plan` run at 12:42 — before this session, and outside this PRD.
- [x] `body_has_open_box` takes the same matcher the four trees' gates take —
      any of `-`/`*`/`+`, any run of spaces, and the ordered arm — lifted out
      of the comprehension so it can be read beside
      `shared/conserved/tests/done_boxes_are_ticked.rs`

      Two named module-level functions, the same two names the Rust holds, and
      the comprehension now calls the first:

      ```
      $ grep -n '^def strip_list_marker\|^def opens_an_unticked_box\|^def body_has_open_box\|opens_an_unticked_box(l)' resources/board/plan.py
      315:def strip_list_marker(rest):
      337:def opens_an_unticked_box(line):
      367:def body_has_open_box(prd):
      387:    return any(opens_an_unticked_box(l) for l in text.splitlines())
      ```

      "The same matcher" is measured against the gates' own eighteen-row
      table, not asserted — 18/18, where HEAD's manages 12/18:

      ```
      $ python3 prds/finished-counts-both-files/probe/probe_matcher.py
      new matcher vs the gates' table: 18/18 agree

      HEAD's matcher vs the same table: 12/18 agree
        MISSES  '* [ ] a star bullet': gates say True, HEAD says False
        MISSES  '+ [ ] a plus bullet': gates say True, HEAD says False
        MISSES  '- [] no space inside the brackets': gates say True, HEAD says False
        MISSES  '-  [ ] two spaces after the bullet': gates say True, HEAD says False
        MISSES  '1. [ ] an ordered task list': gates say True, HEAD says False
        MISSES  '1) [ ] an ordered task list, paren marker': gates say True, HEAD says False
      ```

      And "the four trees hold it byte-identical" was checked rather than
      taken on the spec's word — the eighteen `cases` rows and the two matcher
      bodies hash the same in all four files:

      ```
      realm/src/gates/tests/done_boxes_are_ticked.rs           cases=30e68cc85d552bf7 fn=31bf53387a26d90a
      mitosys/src/mitosys/gates/tests/done_boxes_are_ticked.rs cases=30e68cc85d552bf7 fn=31bf53387a26d90a
      model/gates/tests/done_boxes_are_ticked.rs               cases=30e68cc85d552bf7 fn=31bf53387a26d90a
      shared/conserved/tests/done_boxes_are_ticked.rs          cases=30e68cc85d552bf7 fn=31bf53387a26d90a
      ```
- [x] `BOX_RE` is left byte-unchanged, and its docstring says why: a different
      population (`specs/*.md`, `## Acceptance` only), a different job (a
      progress fraction, not a verdict), and a `[ xX]` capture that
      deliberately neither closes nor counts `[~]`

      A module-level compiled regex has no docstring, so it is a comment
      directly above the line — `plan.py:240-248`. All three reasons are
      named.

      ```
      $ git diff HEAD -- resources/board/plan.py | grep '^[-+].*BOX_RE' || echo "BOX_RE unchanged"
      BOX_RE unchanged

      $ sed -n '240,249p' resources/board/plan.py
      # Deliberately NOT `opens_an_unticked_box`, and deliberately left as it was
      # when the gates widened. It answers a different question over a different
      # population: the boxes under `## Acceptance` in `specs/*.md`, counted both
      # ways to make a progress fraction, where `opens_an_unticked_box` reads the
      # whole of `prd.md` to make a verdict. Its `[ xX]` capture is the fraction's
      # alphabet — `[~]` is neither counted nor closed by it, because a struck box
      # is a contract term withdrawn rather than a term met, and folding it into
      # `closed/total` would move a bar that nothing was built behind. Matching it
      # to the gates would be matching two rules that answer two questions.
      BOX_RE = re.compile(r"^\s*[-*]\s+\[([ xX])\]", re.M)
      ```
- [x] `body_has_open_box`'s docstring no longer says mitosys's gate is scoped
      *"under `## Acceptance`"* — all four gates have been whole-file since
      2026-08-28, so the "widest of the two" reasoning no longer describes two
      things

      "the widest of the two" is gone from the file entirely. `## Acceptance`
      survives in the docstring only in the negated past tense: the sentence
      now says mitosys's scoping is retired, which is what mitosys's own gate
      says.

      ```
      $ grep -c 'widest of the two' resources/board/plan.py
      0

      $ grep -n 'Acceptance' /Users/feb/dev/infra/mitosys/src/mitosys/gates/tests/done_boxes_are_ticked.rs | head -1
      28://! between `## Acceptance` and the next `## ` — that scoping is retired.

      $ sed -n '369,373p' resources/board/plan.py
          The specs are not the whole contract. All four trees' `done` gates read
          the boxes in `prd.md` over the whole file, under every heading — mitosys's
          was scoped under `## Acceptance` until 2026-08-28 and is not any more — so
          a PRD whose specs are all closed can still be one the gate refuses.
          Clearing what the gates clear is what `collect` has to do, because saying
      ```
- [x] The break-it proof for this job is re-run by the implementer and quoted,
      not inherited: a `* [ ]` box planted in a held PRD's `prd.md` suppresses
      that PRD from `collect:` after the change, and does not before it; the
      planted box is reverted and `git status --porcelain` on that board is
      quoted clean afterwards

      Nine fixtures rather than one, driven through the shipped `plan` command
      over pearde's own board, HEAD beside the working tree. `* [ ]` is row 3:
      `IN collect` at HEAD, `suppressed` after the change — which is the box's
      claim, and the other four escape spellings behave the same way.

      ```
      $ python3 prds/finished-counts-both-files/probe/probe_breakit.py
      board: /Users/feb/dev/infra/pearde/prds
      fixture prd.md carries               HEAD 6cd1edf   working tree
      ------------------------------------------------------------------
      clean prd.md, no box at all            IN collect     IN collect
      `- [ ]` the literal spelling           suppressed     suppressed
      `* [ ]` a star bullet                  IN collect     suppressed  <-- HOLE at HEAD
      `+ [ ]` a plus bullet                  IN collect     suppressed  <-- HOLE at HEAD
      `-  [ ]` two spaces                    IN collect     suppressed  <-- HOLE at HEAD
      `- []` no inner space                  IN collect     suppressed  <-- HOLE at HEAD
      `1. [ ]` ordered                       IN collect     suppressed  <-- HOLE at HEAD
      `- [x]` ticked                         IN collect     IN collect
      `- [~]` struck                         IN collect     IN collect

      the collect: lines themselves, verbatim
        `* [ ]` a star bullet
          HEAD          collect: 1 finished, waiting to be closed
          working tree  (no collect line — 0 finished)
      ```

      The fixture is a PRD directory the probe creates and removes, not a box
      planted in a real PRD, so "reverted" is "removed". Clean afterwards:

      ```
      $ git status --porcelain | grep -i '__probe\|_plan_at_HEAD' || echo "no __probe / _plan_at_HEAD line in git status"
      no __probe / _plan_at_HEAD line in git status

      $ test -d prds/__probe && echo "STILL THERE" || echo "prds/__probe absent"
      prds/__probe absent
      ```

      **A second defect, not named by this PRD, was found and fixed under
      `specs/spec01.md`.** `gantt_payload` spelled `collect` twice: `tasks[]`
      from `standing()`, `all[]` from the pre-decision `held and total and
      closed == total` — the specs only. `all[]` is what `view.js` feeds the
      list and the inspector, and what `landing()` reads for `"ready"`, so a
      lane on a PRD with an open `prd.md` box was marked ready to merge. Same
      PRD, two answers, one payload, measured at HEAD:

      ```
      $ python3 prds/finished-counts-both-files/probe/probe_payload_collect.py
      `- [ ]` open box in prd.md
        HEAD           tasks[].collect=False  all[].collect=True   counts.collect=0   <-- TWO ANSWERS, ONE PAYLOAD
        working tree   tasks[].collect=False  all[].collect=False  counts.collect=0

      HEAD 6cd1edf..: the two spellings agree on every fixture: False
      working tree: the two spellings agree on every fixture: True
      ```

      One place decides it now, and the payload chain was swept for a third
      spelling rather than assumed to hold two:

      ```
      $ grep -c 'closed == total' resources/board/plan.py
      1
      $ grep -n 'closed == total' resources/board/plan.py
      406:    ready = bool(held and total and closed == total     # inside `standing`, :390-408
      ```
- [x] The report states that `- [~]` is still a closure under the wider
      matcher, so `../prds/memos/struck-box-spelling.md`'s claim about the
      three readers stays true

      It does, and it is measured on all three bullets and on both closure
      spellings rather than on one line. `False` here is "not an open box",
      i.e. still a closure:

      ```
      $ python3 prds/finished-counts-both-files/probe/probe_matcher.py
      `- [~]` under both matchers — struck-box-spelling.md's claim:
        '- [~] struck'               new=False head=False  (False = still a closure)
        '  - [~] indented struck'    new=False head=False  (False = still a closure)
        '* [~] star struck'          new=False head=False  (False = still a closure)
      ```

      ```
        '- [x] a closure'          opens_an_unticked_box=False
        '- [X] a closure'          opens_an_unticked_box=False
        '- [~] a closure'          opens_an_unticked_box=False
        '* [x] a closure'          opens_an_unticked_box=False
        '* [X] a closure'          opens_an_unticked_box=False
        '* [~] a closure'          opens_an_unticked_box=False
        '+ [x] a closure'          opens_an_unticked_box=False
        '+ [X] a closure'          opens_an_unticked_box=False
        '+ [~] a closure'          opens_an_unticked_box=False
      ```

      `- [~]` is row 12 of the gates' own eighteen-row table, which the Python
      agrees with 18/18, so the third reader in the memo's claim — the gates —
      is the same body it is being compared against.
- [x] `resources/index.py check` is run and its output quoted

      One line, the known `resources/scout/snapshots/2026-08-28.tsv` row,
      outside this PRD and deliberately not fixed here. The probes cost the
      gate nothing where they now sit: `prds/` is outside the manifest scan.

      ```
      $ python3 resources/index.py check
      resources/scout/snapshots/2026-08-28.tsv is on disk with no row in references/files.md
      ```
- [x] `resources/memos.py check` is run and its output quoted

      Silent, exit 0.

      ```
      $ python3 resources/memos.py check
      $ echo $?
      0
      ```
- [x] `resources/doctor.sh` is run and its output quoted

      ```
      $ bash resources/doctor.sh
      pearde doctor — /Users/feb/dev/infra/pearde

        skills      ok      11 well-formed · pearde-doctor pearde-drill pearde-master pearde-memo pearde-persona-ask pearde-persona-create pearde-persona pearde-report pearde-scout pearde-view pearde
        index       broken  1 problem
                            resources/scout/snapshots/2026-08-28.tsv is on disk with no row in references/files.md
        statusline  ok      ~/dev/infra/pearde main *19 ↑3
        guard       off     not wired in /Users/feb/dev/infra/pearde/.claude/settings.json
        board       ok      /Users/feb/dev/infra/pearde/prds · 13 PRDs · language English
        origin      ok      10 requested (5 live) · 3 derived (3 live)
        memos       ok      3 memos · frontmatter checks out
        workflows   off     no workflows/ — a job gets one when it repeats
        questions   ok      no PRD carries a round — nothing is waiting on you
        view        ok      watching · http://127.0.0.1:8443/board/pearde
        plan        ok      planned 2026-08-28
      ```

      `board`, `origin`, `memos`, `questions`, `plan` and `view` are `ok`.
      `index` carries the one known row above. `guard` and `workflows` are
      `off` and were `off` before this round.

## What this round found: evidence that spells a box *is* a box

The matcher is line-based and knows nothing about code fences. Pasting a
probe's output into an acceptance box therefore plants real boxes: the first
draft of the evidence above put nine of them into this `prd.md` and this
spec, and `plan.py` read them exactly as it is now built to —

```
$ python3 -c "... P.acceptance(p), P.body_has_open_box(p) ..."
prd.md lines the matcher calls an open box: 8
acceptance (closed,total): (17, 25)
```

Eight open boxes in its own `prd.md` and nine phantom acceptance boxes in its
spec, on a PRD whose actual boxes were all closed. It could never have
reached `collect`, and the bar would have read 17/25 forever.

**The widening makes this strictly more likely, not less.** At HEAD only a
quoted `- [ ]` bit; now a quoted `* [ ]`, `+ [ ]`, `-  [ ]`, `- []` or
`1. [ ]` bites too — and evidence for a matcher PRD is exactly where those
spellings get quoted. The four Rust gates already carry an `EXEMPT` list for
this class; `body_has_open_box` has no such escape and needs none, because the
fix is free: **quote the spelling.** A line starting with a backtick is not a
list item, so `` `* [ ]` `` reads identically to a human and is invisible to
every one of the five readers.

The two probes that print box spellings were changed to emit their labels
backtick-quoted, and their comments say why, so the next run's output is
paste-safe by construction rather than by remembering. Measured after:

```
$ python3 -c "... same three numbers ..."
prd.md lines the matcher calls an open box: 0
spec01.md lines the matcher calls an open box: 0
acceptance (closed,total): (16, 16)
body_has_open_box: False
standing: (1.0, 16, 16, True)
```

This is a note for `@references/parts/workers.md`, which tells a worker to
quote its output, and not for `loop.md` — it is a rule about writing
evidence, not about what finished means. `workers.md` is outside this PRD's
footprint and was not edited.

## Footprint, and the 60 lines that are not this PRD's

`resources/board/plan.py` carries one insertion this PRD did not make and did
not touch: `ANSWER_LINE_RE`, `QUESTION_HEAD_RE`, `_h2_sections`, `_qid` and
`answers_of`, 60 lines after `question_counts`, another session's asks-view
work. It was not committed, not reverted, and is not in this PRD's footprint.

Byte-intact at the end of the round, hashed over the block itself:

```
$ git diff -U3 -- resources/board/plan.py | grep -c '^@@'
7

$ git diff -U3 -- resources/board/plan.py | grep '^@@'
@@ -237,6 +237,15 @@ def spec_data(prd):
@@ -303,25 +312,79 @@ def claim_of(fm):
@@ -559,9 +622,12 @@ def landing(board, everything):
@@ -591,8 +657,9 @@ def landing(board, everything):
@@ -701,10 +768,15 @@ def gantt_payload(board, prds, mp, settings):
@@ -718,7 +790,7 @@ def gantt_payload(board, prds, mp, settings):
@@ -1217,6 +1289,66 @@ def question_counts(prd):     <-- not this PRD's

$ sed -n '1292,1351p' resources/board/plan.py | shasum -a 256
2f8258bc0952bd7d60bd5dba10a3997edc4b69e48788d81d9b85418edfa38bf2  -
```

That the sed range is exactly the foreign hunk and nothing else is checked
rather than eyeballed — the 60 lines on disk and the 60 `+` lines of that
hunk are the same bytes:

```
$ git diff -U3 -- resources/board/plan.py | sed -n '/^@@ .*question_counts/,$p' | grep '^+' | sed 's/^+//' > hunk.txt
$ wc -l < hunk.txt
      60
$ shasum -a 256 < hunk.txt
2f8258bc0952bd7d60bd5dba10a3997edc4b69e48788d81d9b85418edfa38bf2  -
$ sed -n '1292,1351p' resources/board/plan.py | diff - hunk.txt && echo "IDENTICAL"
IDENTICAL
```

The other six hunks are this PRD's, and `plan.py` was not otherwise edited
this session: the matcher pair and its docstrings (`:237`, `:303`), the two
`landing()` comments (`:559`, `:591`), and the `gantt_payload` single-spelling
fix (`:701`, `:718`).
