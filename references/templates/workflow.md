---
workflow: <slug>   # equals this filename without .md
subject: <one line — the job this routes>
date: <YYYY-MM-DD> # the day it was written. Written, never stamped
# updated:         # the day the text last changed from a run
# runs: 0          # times followed. Integer >= 0, default 0
---
<!-- The keys are a CLOSED set, and exactly one slug key: `workflow` here,
     `atomic` in @references/templates/atomic.md. An undeclared key is a typo
     and the check fails on it. @references/workflow.md is the format. -->

# <slug> — <the job in a phrase>

## Use when

- <A job this fits, named the way a request arrives.>
- <The near-miss it does NOT fit, and the slug that does — this is the
  lookup, so the boundary earns its bullet.>

## Steps

| # | atomic | why | on failure |
|---|--------|-----|------------|
| 1 | `<slug>` | <one clause: what this step buys the job> | `stop` |
| 2 | `<slug>` | <…> | `→ 1` |

<!-- `#` counts from 1, contiguous. `atomic` is a slug in this directory.
     `why` is what the step buys the job — NEVER the atomic's `subject`
     restated.
     `on failure` is `→ N` with N earlier than this row, or `stop`. No
     forward jump: a step that may be skipped is not a step. A back-edge is
     taken at most twice per run; the third failure at one step is a stop.
     `→ 1` on every row is a list, not a workflow. -->
