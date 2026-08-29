---
state: done
origin: requested
actual: 1.2h
commit: cfc0906
priority: 66
complexity: 30
blast-radius: high
repo: pearde
workflow: probe-then-spec
footprint:
  - resources/board/collect.py
  - references/parts/commits.md
  - prds/memos/the-record-is-always-whole.md
  - prds/memos/adjacent-edits-merge-into-one-hunk.md
  - prds/memos/a-container-cannot-reach-done.md
  - prds/the-board-runs-itself/collect-is-a-command/probe/verify.sh
---

# collect-keeps-its-word — the record lands whole, a hunk with two authors is refused, and a parent lands through the tool

When this is done, three things `pearde collect` promised on 2026-08-28 and
did not keep are kept, each measured on a fixture that reproduces the day's
failure first.

## The three consequences, named

1. **The record staged by hunk.** `prds/memos/the-record-is-always-whole.md`:
   on a master-board collect the PRD's `prd.md` was staged "by hunk" against
   the claim baseline, so the commit carried ticked boxes under `state:
   analyzing`, and `state: done`, `complexity`, `actual`, `commit` and the
   posted `## Report` were written after the commit and rode the next one.
   Rule: nothing under the PRD's own folder is ever staged by hunk — the
   board's record is committed whole. Everything `collect` writes lands in
   the commit it makes, except `commit:` itself, which lands in a second,
   one-key commit `<prd> — record` immediately after, so no rider list exists.
2. **A hunk with two authors.** `prds/memos/adjacent-edits-merge-into-one-hunk.md`:
   two edits on adjacent lines merge into one `-U0` hunk whose body is in
   neither baseline, `new_hunks` returns `all`, and the foreign lines are
   committed as the worker's. Rule: a hunk that matches neither the
   baseline's diff nor the worker's is refused — `two authors on one hunk:
   <file>:<line>` — and the worker widens with `--widen` or separates the
   edits. Line-level matching is not attempted.
3. **A container cannot reach done.** `prds/memos/a-container-cannot-reach-done.md`:
   a parent whose children are all `done` has no command that moves it;
   `workflows-on-the-board` and `the-board-runs-itself` were closed by hand.
   Rule: `collect` lists such a parent in `scan`'s collect band and closes
   it — `state: done`, `actual` the sum of its children's, `commit:` the
   last child's — with no verify to run and no paths to add but its own
   `prd.md`, in one commit `<parent> — done: every child landed`.

DONE · committed

## Files

| file | change |
|---|---|
| `resources/board/collect.py` | step 3: the PRD folder is always whole; the merged-hunk refusal; steps 4–5: the record's keys before the commit, `commit:` in the second commit; the container branch |
| `resources/board/plan.py` | the collect band offers a parent whose children are all done — one clause in `standing()`, named in the report; if it needs more than a clause, it is a finding for `one-predicate-for-dispatchable` |
| `references/parts/commits.md` | the three rules, one sentence each |
| the three memos | `status: decided`, the decision filled in |

## Verify

- A fixture PRD whose claim baseline holds its body and whose implementer ticked three boxes: after `collect`, `git show HEAD:<prd.md>` reads `state: done` with the ticks, and `HEAD~1`… no — `HEAD` is `<prd> — record` carrying only `commit:`, `HEAD~1` carries everything else; `git status --porcelain <prd dir>` is empty.
- A fixture file with a foreign edit on line 10 and the worker's on line 11: `collect` exits 1 with `two authors on one hunk: <file>:10`, the index is at HEAD, nothing committed; with one untouched line between them, both paths stage right.
- A fixture parent with two `done` children: `scan` lists it under collect; `collect <parent>` sets `done` with `actual` summed and `commit:` the last child's; one commit; `git status` clean under it.
- `prds/the-board-runs-itself/collect-is-a-command/probe/verify.sh` and `hunks-land-where-they-came-from/probe/verify.sh` green at their counts, or each moved line named.
