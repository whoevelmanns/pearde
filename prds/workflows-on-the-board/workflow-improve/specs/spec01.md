---
complexity: 8
footprint:
  - references/parts/loop.md
---

# spec01 — the collect applies the run's edits, and counts the run

`references/parts/loop.md` step 6 is where a finished worker's result becomes
board state. It lists the mechanical actions on any result; this adds the five
that only a result carrying `## Workflow <slug>` has — read the rows, apply or
refuse each edit, count the run, check the format, and put the changed files on
the PRD's commit. They are one bullet block in the same batch, not a second
pass: a collect that reads the report twice is the analysis step 6 refuses.

Step 1 gains the other half. A worker its infrastructure killed still ran the
route it was handed, and its `### Edits` are the ones with the most to say — a
library that only learns from runs whose PRD landed never learns from the runs
that hit walls. So the rows are read with the report **before** the sweep moves
the state, and a swept worker that left no report ran nothing.

Step 6's own summary sentence is corrected here too. It read "those are six
mechanical actions" over a list of seven — validate, write the transition,
commit, clear `claim:`, print the progress line, rewrite `prds/.round.md`, post
the report ("return to step 2" is the loop's next hop, not an action on the
result). `git log -S` puts `POST /report` in `341848f` and "six mechanical" in
the later `10f6e7e`, so the number was wrong the day it was written. The fix is
the word; the guard is that the harness now derives the count from the list
instead of asserting a literal, because this block is the one another PRD adds
a sentence to.

Standing after the probe: both blocks are written, and
`prds/workflows-on-the-board/workflow-improve/probe/verify.sh` asserts every
sentence of them. What is left is review of the wording.

## Acceptance

- [x] Step 6 of `references/parts/loop.md` carries a block opening on a report
      carrying `## Workflow <slug>`, with five numbered rules in this order:
      read the rows, apply/refuse, `runs` +1 and `updated`, `workflows.py
      check` before the commit, the changed files on the PRD's commit.
- [x] Rule 1 says the PRD's transition is the verdict's and a `stopped` row
      changes nothing about it — the state is not a function of the route.
- [x] Rule 2 names the four failures that are the atomic's (a wrong command, a
      stale path, a check that cannot fail, an unlisted failure shape), says a
      failure that was the code's or the PRD's is refused with which one said
      out loud, and says the orchestrator pastes or refuses the worker's text
      and never rewrites it.
- [x] Rule 3 says `runs` +1 on the workflow and on every atomic that ran, and
      `updated: <today>` only on a file whose text changed.
- [x] Rule 4 says `python3 @resources/workflows.py check` runs before the
      commit and that a format-breaking edit is refused, not repaired.
- [x] Rule 5 says the changed files ride the PRD's commit and that the PRD's
      own `footprint:` does not change.
- [x] The block closes on one writer being the orchestrator, and on two workers
      editing one atomic in one round being two collects.
- [x] Step 1 says a swept worker's `## Workflow` rows are read with its report
      before the sweep moves the state, and that a swept worker with no report
      ran nothing.
- [x] The five actions appear in `references/parts/loop.md` in the same order
      the summary in `references/parts/workers.md` gives them — the harness
      compares the two rather than only asserting each is present.
- [x] Step 6's spelled count of the mechanical actions agrees with the list it
      counts: the sentence reads seven, and the list under `On each finished
      worker:` holds seven actions on the result. The harness derives the
      number from the list rather than asserting a literal, so a sentence
      added to that batch without the count moving fails, and so does the
      count moving without the list.
- [x] `bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh` still
      prints `47/47 checks pass` — that harness asserts eleven sentences of
      this same file, and this is the first PRD able to break them.
- [x] `python3 resources/index.py check` prints nothing this spec added.

## Verify and Proof

```sh
bash prds/workflows-on-the-board/workflow-improve/probe/verify.sh
bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh
python3 resources/index.py check
```
