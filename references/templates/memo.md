---
memo: <slug>       # equals this filename without .md
kind: decision     # decision | note
status: decided    # open | decided | superseded
subject: <one line — what this memo settles>
date: <YYYY-MM-DD> # the day the call was recorded. Written, never stamped
# updated:         # only on a substantive revision; never for a path fix
# prds:            # board-relative PRD dirs this memo governs
#   - <prd-dir>
# supersedes:      # the slug this replaces
# superseded_by:   # the slug that replaced this
---
<!-- Unlike a prd.md, a memo's keys are a CLOSED set: an undeclared key is a
     typo and doctor.sh fails on it. references/memo.md is the format. -->

# <slug> — <the decision in a phrase>

## Decision

<What was settled, in the present tense. The rule as it now stands, not the
story of arriving at it. Short enough to quote.>

## Why

<The argument. This is the part that has to survive — a reader six months out
should be able to reconstruct the reasoning without you in the room. Name the
forces: what was breaking, what constraint bit, what the cheap option cost.>

## Alternatives considered

**<The other road>** — <what it was, and the count it lost on. Be specific:
"slower" is not a reason, "it re-reads the whole board on every state change,
which is the thing the progress line is called from" is.>

**<Another>** — <…>

<!-- NEVER empty. A memo with no alternatives is a claim, not a decision, and
     nobody can later tell whether the other road was walked and rejected or
     never seen. If nothing else was considered, that is the finding: say so,
     and say why the choice was forced. -->

## Consequences

- <what this now costs, in work or in freedom given up>
- <what it deliberately does NOT fix — the next memo's problem, named>
