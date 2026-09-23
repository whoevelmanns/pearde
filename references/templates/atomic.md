---
atomic: <slug>     # equals this filename without .md
subject: <one line — the unit of work>
date: <YYYY-MM-DD> # the day it was written. Written, never stamped
# updated:         # the day the text last changed from a run
# runs: 0          # runs this file was in — one collect, one count. Integer >= 0
---
<!-- The keys are a CLOSED set, and exactly one slug key: `atomic` here,
     `workflow` in @references/templates/workflow.md. An undeclared key is a
     typo and the check fails on it. @references/workflow.md is the format. -->

# <slug> — <the unit in a phrase>

## Do

1. <An imperative step naming the command and the file. `python3
   resources/index.py check`, not "verify the index".>
2. <…>

<!-- ONE unit of work, small enough to close in one sitting. An atomic that
     needs "and then" is two atomics and a workflow ordering them.
     Name commands and files — never an agent, a tool, a hook or a vendor. -->

## Done when

- <A check that can FAIL — an output, a file, an exit code. "The check is
  silent", not "the index is tidy".>
- <…>

## Fails when

| seen | means | do |
|------|-------|----|
| <the line, the exit code, the state the run actually hit> | <what it meant> | <what closed it> |

<!-- EMPTY at `runs: 0`, and filled only from a run — never from reading the
     code and guessing. Each row is one failure a run hit and closed.
     No log section: a lesson is folded into `## Do` or into this table, and
     `updated` moves. Git holds what it replaced. -->
