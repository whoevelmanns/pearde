---
complexity: 12
footprint:
  - references/parts/loop.md
  - resources/board/plan.py
---

# spec01 — one rule for what a box is, and one place that decides `collect`

`collect` must never name a PRD a gate would refuse. Two things break that
today, and both are in `plan.py`. `body_has_open_box` matches the single
literal `- [ ]` while all four trees' gates have matched five further
spellings of the same rendered box since 2026-08-28, so a `* [ ]` box is red
to every gate and invisible here. And `gantt_payload` spells `collect` a
second time, from the pre-decision rule — `held and total and closed == total`,
the specs only — into the `all[]` rows the view's list, inspector and
merge-ready lane list read.

The prose half is `references/parts/loop.md`. Its finished sentence already
names both files; what it does not say is that `- [~]` is a closure, what a
box is, or that `boxes c/t` stays the specs' number while `collect` reads
both. Those are the three things a reader gets wrong next.

Job 1 of the PRD is already discharged — `body_has_open_box` is in `HEAD` at
`6cd1edf`, an ancestor of HEAD, and the acceptance box for it is already
`[x]`. Nothing here re-does it.

## Acceptance

- [x] `plan.py` carries `opens_an_unticked_box(line)` and
      `strip_list_marker(rest)` as named module-level functions, not a
      predicate inside a comprehension, and `body_has_open_box` calls the
      first — so the Python can be read beside
      `shared/shared/tests/done_boxes_are_ticked.rs`, which holds the same two
      names

      The Rust is at `shared/conserved/tests/done_boxes_are_ticked.rs`, not
      `shared/shared/` — the spec's path is one segment wrong; the PRD has it
      right. Both names are there, and the Python is a line-for-line port.

      ```
      $ grep -n '^def strip_list_marker\|^def opens_an_unticked_box\|^def body_has_open_box\|opens_an_unticked_box(l)' resources/board/plan.py
      315:def strip_list_marker(rest):
      337:def opens_an_unticked_box(line):
      367:def body_has_open_box(prd):
      387:    return any(opens_an_unticked_box(l) for l in text.splitlines())
      ```
- [x] `opens_an_unticked_box` returns the same verdict as the four gates on
      all eighteen rows of
      `the_matcher_reads_every_spelling_of_one_rendered_box`
      (`shared/shared/tests/done_boxes_are_ticked.rs:301-320`, held
      byte-identical by mitosys, model and realm). Run the table, quote
      `18/18`, and name any row that disagrees

      18/18, no row disagrees. The four trees' copies were checked rather than
      taken on the spec's word — the eighteen `cases` rows and the
      `strip_list_marker`/`opens_an_unticked_box` bodies hash the same in all
      four files (the whole files differ, they hold different neighbours):

      ```
      $ for f in realm/src/gates/tests/... mitosys/src/mitosys/gates/tests/... model/gates/tests/... shared/conserved/tests/...; do ... shasum -a 256 ...; done
      realm/src/gates/tests/done_boxes_are_ticked.rs           cases=30e68cc85d552bf7 fn=31bf53387a26d90a
      mitosys/src/mitosys/gates/tests/done_boxes_are_ticked.rs cases=30e68cc85d552bf7 fn=31bf53387a26d90a
      model/gates/tests/done_boxes_are_ticked.rs               cases=30e68cc85d552bf7 fn=31bf53387a26d90a
      shared/conserved/tests/done_boxes_are_ticked.rs          cases=30e68cc85d552bf7 fn=31bf53387a26d90a
      ```

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
- [x] `- [~]` and `- [x]` are still closures under the wider matcher, on all
      three bullets — quoted from the run, so
      `../prds/memos/struck-box-spelling.md`'s claim about the three readers
      stays true

      From the same run. `- [x]`, `- [X]` and `* [x]` are rows 10, 11 and 13 of
      the eighteen above, all `false` and all agreeing; `- [~]` is row 12 and
      is checked again on all three bullets below. `False` is "not an open
      box", i.e. still a closure, under both the new matcher and HEAD's:

      ```
      $ python3 prds/finished-counts-both-files/probe/probe_matcher.py
      `- [~]` under both matchers — struck-box-spelling.md's claim:
        '- [~] struck'               new=False head=False  (False = still a closure)
        '  - [~] indented struck'    new=False head=False  (False = still a closure)
        '* [~] star struck'          new=False head=False  (False = still a closure)
      ```

      And the full cross-product the box asks for — both closure spellings on
      all three bullets, `[X]` included:

      ```
      $ python3 -c "import sys; sys.path.insert(0,'resources/board'); import plan as P; ..."
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
- [x] `BOX_RE` is byte-unchanged from `HEAD`
      (`git diff HEAD -- resources/board/plan.py | grep '^[-+].*BOX_RE'`
      returns nothing), and a comment above it says why it is not the gates'
      matcher: a different population (`specs/*.md`, `## Acceptance` only), a
      different job (a progress fraction, not a verdict), and a `[ xX]`
      capture that deliberately neither counts nor closes `[~]`

      ```
      $ git diff HEAD -- resources/board/plan.py | grep '^[-+].*BOX_RE' || echo "BOX_RE unchanged"
      BOX_RE unchanged
      ```

      A bare `grep BOX_RE` over the same diff does **not** print nothing, and
      cannot: the comment this box also requires sits directly above the line,
      so `BOX_RE` appears in that hunk's trailing context, prefixed with a
      space. Context is not a change. The unambiguous form is `-U0`, and both
      lines mentioning `BOX_RE` are byte-identical to HEAD, moved nine lines
      down by the comment:

      ```
      $ git diff -U0 HEAD -- resources/board/plan.py | grep BOX_RE || echo "nothing"
      nothing

      $ git show HEAD:resources/board/plan.py | grep -n BOX_RE
      240:BOX_RE = re.compile(r"^\s*[-*]\s+\[([ xX])\]", re.M)
      254:        for box in BOX_RE.findall(sec):

      $ grep -n BOX_RE resources/board/plan.py
      249:BOX_RE = re.compile(r"^\s*[-*]\s+\[([ xX])\]", re.M)
      263:        for box in BOX_RE.findall(sec):
      ```

      The comment is `plan.py:240-248`, directly above the line, and names all
      three:

      ```
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
      *"under `## Acceptance`"* and no longer reasons about "the widest of the
      two" — all four gates have read the whole file since 2026-08-28

      "the widest of the two" is gone from the file entirely. `## Acceptance`
      survives in the docstring only in the negated past tense — the sentence
      now says mitosys's scoping is retired, which is what the gate itself
      says (`mitosys/src/mitosys/gates/tests/done_boxes_are_ticked.rs:28`:
      *"between `## Acceptance` and the next `## ` — that scoping is
      retired."*).

      ```
      $ grep -c 'widest of the two' resources/board/plan.py
      0

      $ sed -n '367,382p' resources/board/plan.py
      def body_has_open_box(prd):
          """True when `prd.md` itself still carries an unticked box.

          The specs are not the whole contract. All four trees' `done` gates read
          the boxes in `prd.md` over the whole file, under every heading — mitosys's
          was scoped under `## Acceptance` until 2026-08-28 and is not any more — so
          a PRD whose specs are all closed can still be one the gate refuses.
          Clearing what the gates clear is what `collect` has to do, because saying
          "collect" on a PRD a gate would reject is how a board manufactures the
          `done`-with-open-boxes defect it is trying to remove.

          The match is `opens_an_unticked_box`, the gates' own matcher, not a
          literal `- [ ]`: a `* [ ]` box is red to every tree's gate, and until
          2026-08-28 it was invisible here. `- [~]` stays a closure under it. This
          is the one place the marker set matters, which is why it is not
          `acceptance_of`'s `== "x"` test."""
      ```
- [x] `gantt_payload` decides `collect` in exactly one place. `all[]` rows
      take it from `standing()`, not from a second spelling of the rule;
      `grep -c 'closed == total' resources/board/plan.py` returns 1, and the
      one hit is inside `standing`

      One hit, at `:406`, and `standing` opens at `:390` and returns at `:408`
      — so the hit is inside it. `gantt_payload`'s `all[]` row now reads
      `_, closed, total, collect = standing(p)` at `:779`, the same reader
      `tasks[]` uses at `:744`.

      ```
      $ grep -n 'closed == total' resources/board/plan.py
      406:    ready = bool(held and total and closed == total

      $ grep -c 'closed == total' resources/board/plan.py
      1

      $ grep -n '^def standing\|standing(p)\|"collect": collect' resources/board/plan.py
      390:def standing(prd):
      744:        frac, closed, total, ready_to_collect = standing(p)
      779:            _, closed, total, collect = standing(p)
      793:            "collect": collect,
      1117:        frac, closed, total, ready_to_collect = standing(p)
      ```

      Swept for a third spelling as well, rather than assuming two: no other
      reader in the payload chain re-derives `collect`. `render.py:218` and
      `view.js` read the payload's `collect` field; `landing()`'s `"ready"`
      (`plan.py:663`) reads `tasks[].collect`; `serve.py:532`'s
      `acceptance_of(body)` is a per-spec progress fraction for the inspector,
      not a verdict.
- [x] Break-it proof, re-run and quoted, not inherited: a held PRD whose every
      spec box is `[x]`, planted with each of `- [ ]`, `* [ ]`, `+ [ ]`,
      `-  [ ]`, `- []` and `1. [ ]` in its own `prd.md` in turn, is absent
      from `plan`'s `collect:` line every time — and present when its `prd.md`
      is clean, `- [x]` or `- [~]`. Run the same nine fixtures against
      `git show HEAD:resources/board/plan.py` and quote which five HEAD offers
      for collection

      Nine fixtures, run end to end through the shipped `plan` command over
      pearde's own board, HEAD and working tree side by side. All six planted
      spellings are suppressed in the working tree; all three closures
      (clean, `- [x]`, `- [~]`) are offered. The five HEAD offers while
      carrying an open box are `* [ ]`, `+ [ ]`, `-  [ ]`, `- []` and
      `1. [ ]` — exactly the five rows the gates' table names as the ones that
      walked past the literal matcher.

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
      ```

      The `collect:` lines themselves, verbatim, for the six planted rows:

      ```
        `- [ ]` the literal spelling
          HEAD          (no collect line — 0 finished)
          working tree  (no collect line — 0 finished)
        `* [ ]` a star bullet
          HEAD          collect: 1 finished, waiting to be closed
          working tree  (no collect line — 0 finished)
        `+ [ ]` a plus bullet
          HEAD          collect: 1 finished, waiting to be closed
          working tree  (no collect line — 0 finished)
        `-  [ ]` two spaces
          HEAD          collect: 1 finished, waiting to be closed
          working tree  (no collect line — 0 finished)
        `- []` no inner space
          HEAD          collect: 1 finished, waiting to be closed
          working tree  (no collect line — 0 finished)
        `1. [ ]` ordered
          HEAD          collect: 1 finished, waiting to be closed
          working tree  (no collect line — 0 finished)
      ```

      The proof the PRD asks for (§ Job 2, steps 1-4) could not be run as
      written and was not: its fixture
      `@realm/done-means-done/realm-classify` carries no open `prd.md` box to
      tick, and both PRDs the memo predicts in `collect:` are `state: done`,
      so neither is in a `HOLDING_STATE` and neither can reach `collect` under
      any matcher. This is the same set of propositions on a fixture that
      exists — a held PRD with closed specs, built and removed by the probe.
- [x] Break-it proof for the payload, re-run and quoted: on the same fixture,
      `tasks[].collect` and `all[].collect` give the same answer for the same
      `rel` in the same payload, before and after a `- [ ]` is planted

      They agree on all three fixtures in the working tree. At HEAD they do
      not — this is the defect, measured rather than argued: on a `- [ ]`
      planted in `prd.md`, HEAD's payload says `False` on the timeline row and
      `True` on the row `view.js` feeds the list, the inspector and
      `landing()`'s merge-ready lane list.

      ```
      $ python3 prds/finished-counts-both-files/probe/probe_payload_collect.py
      clean prd.md
        HEAD           tasks[].collect=True   all[].collect=True   counts.collect=1
        working tree   tasks[].collect=True   all[].collect=True   counts.collect=1
      `- [ ]` open box in prd.md
        HEAD           tasks[].collect=False  all[].collect=True   counts.collect=0   <-- TWO ANSWERS, ONE PAYLOAD
        working tree   tasks[].collect=False  all[].collect=False  counts.collect=0
      `* [ ]` open box in prd.md
        HEAD           tasks[].collect=True   all[].collect=True   counts.collect=1
        working tree   tasks[].collect=False  all[].collect=False  counts.collect=0

      HEAD 6cd1edf..: the two spellings agree on every fixture: False
      working tree: the two spellings agree on every fixture: True
      ```
- [x] The fixture board is left clean — the planted PRD directory is removed
      and `git status --porcelain` on that board is quoted with no line for it

      The fixture board is pearde's own `prds/`. Both probes remove
      `prds/__probe/` in a `finally`, and `resources/board/_plan_at_HEAD.py`
      — the temporary sibling copy HEAD's `plan.py` has to be run from, since
      it imports `memos` relative to `__file__` — with it. No line for either:

      ```
      $ git status --porcelain | grep -i '__probe\|_plan_at_HEAD' || echo "no __probe / _plan_at_HEAD line in git status"
      no __probe / _plan_at_HEAD line in git status

      $ test -d prds/__probe && echo "STILL THERE" || echo "prds/__probe absent"
      prds/__probe absent
      ```
- [x] A census, not a sample: every `prd.md` on every board this install plans
      is read line by line and the count of lines the widened matcher newly
      calls an open box is quoted, together with the count it stops calling
      one. The second must be `0`

      266 `prd.md` files, every line of every one. Newly called an open box:
      `0`. No longer called one: `0` — the required answer, and the one that
      says the widening only adds.

      ```
      $ python3 prds/finished-counts-both-files/probe/probe_escape_census.py
      population: 266 prd.md files over 2 boards (/Users/feb/dev/infra/prds, /Users/feb/dev/infra/pearde/prds)
      lines the widened matcher newly calls an open box: 0
        none — every escape spelling is absent from every board file today,
        so the widening moves no verdict on the boards as they stand.
      lines both matchers call an open box: 197
      lines HEAD called open and the widened matcher no longer does: 0
      ```

      The two board roots are six boards: `scan` on the master board walks its
      four members. The population, enumerated rather than asserted:

      ```
      mitosys      127
      model         75
      realm         18
      shared        15
      infra/prds    18   (the master board's own PRDs)
      pearde        13
      total        266
      ```

      That is every board the PRD's blast-radius section names.
- [x] `references/parts/loop.md`'s finished sentence names **both files**,
      says `- [x]` and `- [~]` are both closures in either file, and says what
      a box is — any of `-`, `*`, `+` or an ordered marker, any run of spaces
      before the bracket

      `references/parts/loop.md:158-169`. The PRD cites the sentence at
      `:100`; it is at `:158` — the citation is stale, and the file has moved
      under it.

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
- [x] `references/parts/loop.md` states that `boxes c/t` stays the specs'
      number under `## Acceptance` while `collect` reads `prd.md` whole-file
      too, and that a bar at 100% beside a PRD not in **collect** is correct
      output rather than a bug

      `references/parts/loop.md:171-178`, the paragraph directly after.

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
- [x] `python3 resources/index.py check` is run and its output quoted, with
      `probe/` moved out of the tree first — the probes are the analyst's
      scratch, uncommitted by design, and every one of them is a file with no
      manifest row. Its only remaining line is
      `resources/scout/snapshots/2026-08-28.tsv`, a known row outside this
      PRD, not to be fixed here

      No move was needed and none was made: the probes now live at
      `prds/finished-counts-both-files/probe/`, and `prds/` is outside the
      manifest scan, so they cost the gate nothing where they sit. That is
      what the spec's `mv probe /tmp/probe.$$` dance was for; the Verify block
      below is updated to the paths that exist. One line, the known one:

      ```
      $ python3 resources/index.py check
      resources/scout/snapshots/2026-08-28.tsv is on disk with no row in references/files.md
      ```
- [x] `python3 resources/memos.py check` is run and its output quoted, silent

      Silent, exit 0.

      ```
      $ python3 resources/memos.py check
      $ echo $?
      0
      ```
- [x] `bash resources/doctor.sh` is run and its output quoted; `board`,
      `origin`, `memos`, `questions`, `plan` and `view` are `ok`

      All six named rows `ok`. `index` carries the one known row above;
      `guard` and `workflows` are `off`, and the spec names neither.

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
- [x] `python3 resources/board/plan.py plan /Users/feb/dev/infra/prds` runs to
      completion and its `collect:` line (or its absence) is quoted, before
      and after the change, showing the board's real verdict did not move

      No `collect:` line on either board, at HEAD or in the working tree —
      nothing on either is finished and waiting. Stronger than the box asks:
      the two plans are byte-identical, so no line moved, not just the collect
      one. That is what the census predicted — `0` lines newly matched means
      `0` verdicts changed.

      ```
      $ git show HEAD:resources/board/plan.py > resources/board/_plan_at_HEAD.py   # sibling copy; the working file is never reverted

      $ python3 resources/board/_plan_at_HEAD.py plan /Users/feb/dev/infra/prds > head_master.txt   # exit 0
      $ grep -A5 '^collect:' head_master.txt || echo "(no collect: line at HEAD)"
      (no collect: line at HEAD)

      $ python3 resources/board/plan.py plan /Users/feb/dev/infra/prds > wt_master.txt   # exit 0
      $ grep -A5 '^collect:' wt_master.txt || echo "(no collect: line in working tree)"
      (no collect: line in working tree)

      $ diff head_master.txt wt_master.txt && echo identical
      identical
      ```

      The same on pearde's own board, re-run after the last box above was
      closed — at which point this PRD itself becomes the board's one
      collectable, on **both** sides of the change, because its `prd.md`
      carries no escape spelling for the two matchers to disagree about:

      ```
      $ diff head_pearde.txt wt_pearde.txt > /dev/null && echo "identical HEAD vs working tree"
      identical HEAD vs working tree

      $ grep -A2 '^collect:' wt_pearde.txt
      collect: 1 finished, waiting to be closed
        ✓ finished-counts-both-files [claimed] 16/16 boxes closed
      ```

      Earlier in the round, before this spec's own boxes were closed, both
      sides printed no `collect:` line at all on this board. Either way the
      two sides agree, which is the box's claim.

## Verify and Proof

The probes live inside this PRD folder, not at the repo root: `prds/` is
outside `index.py check`'s manifest scan, so scratch code costs the gate
nothing there and needs no `mv` around the run.

```sh
cd /Users/feb/dev/infra/pearde
P=prds/finished-counts-both-files/probe

# the matcher, against the gates' own eighteen-row table
python3 $P/probe_matcher.py

# the census: every prd.md on every board this install plans
python3 $P/probe_escape_census.py

# the break-it proof, HEAD vs working tree, nine fixtures, end to end
python3 $P/probe_breakit.py

# one rule, one place: tasks[].collect and all[].collect on one PRD,
# HEAD and working tree side by side
python3 $P/probe_payload_collect.py

# exactly one place still spells the specs-only rule, and it is `standing`
grep -n 'closed == total' resources/board/plan.py

# BOX_RE untouched
git diff HEAD -- resources/board/plan.py | grep '^[-+].*BOX_RE' || echo "BOX_RE unchanged"

# the board's own gate
python3 resources/index.py check
python3 resources/memos.py check
bash resources/doctor.sh

# the real boards still plan, and their verdict has not moved
git show HEAD:resources/board/plan.py > resources/board/_plan_at_HEAD.py
for b in /Users/feb/dev/infra/prds /Users/feb/dev/infra/pearde/prds; do
  python3 resources/board/_plan_at_HEAD.py plan "$b" > /tmp/head.txt
  python3 resources/board/plan.py             plan "$b" > /tmp/wt.txt
  diff /tmp/head.txt /tmp/wt.txt && echo "$b: identical"
  grep '^collect:' /tmp/wt.txt || echo "$b: no collect line"
done
rm -f resources/board/_plan_at_HEAD.py

# nothing left behind by the fixtures
git status --porcelain | grep -i '__probe\|_plan_at_HEAD' || echo "fixture board clean"
```
