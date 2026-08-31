---
workflow: probe-then-spec
subject: an open PRD, from its contract to specs written from a build
date: 2026-08-28
updated: 2026-08-28
runs: 24
---

# probe-then-spec — build it first, then write down what it takes

## Use when

- A PRD is `open` and needs specs before anyone can be sent at it.
- A PRD came back `refine` and a child now needs its own specs.
- Not when the specs already exist — that is `implement-a-spec`.
- Not when the contract is still a title and a hope: nothing here interviews a
  person, and a build against a vague contract produces questions nobody asked
  for.
- The three verdicts, and the rule that a question must be a fork the build
  actually hit, are @references/parts/workers.md. This route orders the steps
  and restates none of that.

## Steps

| # | atomic | why | on failure |
|---|--------|-----|------------|
| 1 | `read-the-contract` | the answers already on the PRD close forks you would otherwise ask back | `stop` |
| 2 | `capture-the-harness-baseline` | the probe moves the tree, and nothing afterwards can tell you which edit moved a number | `→ 1` |
| 3 | `attempt-the-build` | a question asked before the build is a guess, and the board pays for it in a round-trip | `→ 1` |
| 4 | `re-run-the-harnesses` | a probe that reddens a committed harness is a failed run rather than a finding | `→ 3` |
| 5 | `write-the-specs` | the probe's knowledge is in one worker's head and nowhere else until this step, and the next worker gets the file, not the head | `→ 3` |
