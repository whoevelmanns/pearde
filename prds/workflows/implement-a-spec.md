---
workflow: implement-a-spec
subject: a specced unit, from reading it to the gates green
date: 2026-08-28
runs: 22
---

# implement-a-spec — one specced unit, finished and measured

## Use when

- A PRD is `specced` and its specs are handed to you to finish.
- A `failed` PRD is picked up again and its specs still describe the work.
- Not when there are no specs yet — that is `probe-then-spec`.
- Not when the only change is prose in `references/` — that is
  `correct-a-documented-claim`, which has no scoped verify to run.
- The verdict you return, the gates you may not skip and what you may write
  are @references/parts/workers.md. This route orders the steps and restates
  none of that.

## Steps

| # | atomic | why | on failure |
|---|--------|-----|------------|
| 1 | `read-the-contract` | the specs were written from a probe that is still uncommitted in the tree, and continuing it beats restarting it | `stop` |
| 2 | `capture-the-harness-baseline` | separates what you broke from what arrived broken | `→ 1` |
| 3 | `edit-inside-the-footprint` | keeps the change on the paths the overlap check already cleared for you | `→ 1` |
| 4 | `run-the-scoped-verify` | measures this unit rather than the tree's worst neighbour | `→ 3` |
| 5 | `re-run-the-harnesses` | a green unit beside a harness you turned red is a failure, not a finish | `→ 3` |
| 6 | `run-the-repo-gate` | the last thing a reviewer runs, so it is the last thing you run | `→ 3` |
