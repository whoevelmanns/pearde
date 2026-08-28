---
complexity: 10
workflow: implement-a-spec
footprint:
  - resources/questions.py
  - prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh
---

# spec04 — `questions.py check` accepts the round `drill.md` prescribes, so `release … question` has a gate that can pass

**Outside the PRD's `footprint:` — the orchestrator accepts this unit here
or files it derived.** The contract's gate for `release <prd> question` is "a
`## Questions` round `questions.py` accepts". The build hit this: on a round
in the exact shape of `@references/drill.md` — `### Q1: <title>`, the fork,
then `1. **label** — …`, `2. …`, `3. …` with one `(recommended)` —
`python3 resources/questions.py check` prints two lines per answer
(`asks nothing`, `carries no recommended answer`) and one per heading,
because `ITEM_RE` (`^(###\s+\S.*|\d+\.\s+\S.*)$`) reads every numbered
answer line as a question item of its own. No real board carries a
drill-shaped round today (`grep -rl '^### Q1' prds` finds only the probe's
fixture), which is why `doctor`'s `questions` row never showed it; the
example board's `asking` PRD will, and so will every round the drill writes.

The fix is in `questions_in`/`ITEM_RE`: when a section carries `###` heads,
a `\d+\.` line at the top level is an answer of the heading above it, not an
item; a section with no `###` head keeps today's reading (numbered questions
at the top level are live on real boards, per the file's own comment). The
two rules that judge a question — it asks something, it carries a
recommended answer — do not move, and `badround` (three answers, none
recommended) stays refused.

## What stands from the probe

The gate in `transitions.py` already calls `questions.check(board_path)` and
filters to the PRD's own lines; the harness marks the two checks that wait on
this file as `PEND` and prints them apart from the count:
`questions.py check silent` and `analyzing → question with a round the check
accepts`. Reproduced on `probe/fixture.py`'s `asking` on 2026-08-28: 18 lines
for a three-question round before any answer is written.

## What is left

The `questions.py` change, and flipping the two `pending` lines in
`probe/verify.sh` to `check`. The harness's row count stays 13 — the forced
fallback it takes today is replaced by the `release` that then succeeds.

## Acceptance

- [x] `python3 resources/questions.py check <copy of probe/fixture.py>` prints only the `badround` lines — `asking` is clean
- [x] `release asking question` from `analyzing` on the fixture (after `set asking analyzing --force`) exits 0 and the state is `question`
- [x] `release badround question` still exits 1 with `recommended` in the message
- [x] the two `pending` calls in `probe/verify.sh` are `check` calls and the harness prints `0 fail · 0 pending`
- [x] `bash resources/doctor.sh` still reports `questions ok` on this repo's board

## Verify and Proof

```sh
D=$(mktemp -d); python3 prds/the-board-runs-itself/transitions-are-commands/probe/fixture.py "$D" >/dev/null
python3 resources/questions.py check "$D/prds"; rm -rf "$D"
bash prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh | tail -1
```
