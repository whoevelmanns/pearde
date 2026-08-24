---
state: open        # open|analyzing|refine|question|specced|claimed|blocked|done|failed
origin: requested  # requested = the user asked | derived = the board found it
# from:            # derived only — the PRD whose work surfaced this one
priority: 0        # higher first
complexity: 0      # analyst, at spec time — 1-100. THE WEIGHT the board schedules by
blast-radius:      # analyst, at spec time — high|mid|low. What breaks if this is wrong
repo:              # the sub-repo the code lands in; delete if n/a
time:              # OPTIONAL, and read by no decision. See README, Weight and order
  est:             # a record only — nothing on the board schedules on time
  actual:          # a record only
  # claim: <worker> <started>   # orchestrator-only, present while a worker holds this PRD
---
<!-- Ordering reads three axes and no clock: dependency (needs + footprint),
     vision importance (priority), and complexity/blast-radius. Add your own
     keys freely, at any nesting; nothing outside state, origin, from,
     priority, complexity, blast-radius, claim, repo, needs and footprint is read, and
     nothing you add is ever dropped.
       needs:     — list of PRD dir names this one depends on; `plan` wave order
       footprint: — list of paths this PRD touches; the overlap check

     A derived PRD states, in the body, which requested PRD it would otherwise
     get wrong. If it cannot, it is filed `state: deferred` — and if fixing it
     would change only how loudly the board notices, it is a memo, not a PRD.
     See README, Derived work. -->

# <Title — what exists when this is done>

<The request, for an analyst who knows the codebase but not this conversation:

- what exists when the PRD is done, and why it matters
- constraints and non-goals — what must NOT change
- pointers: relevant files, docs, prior PRDs

One contract per PRD. "And also…" is a second PRD — write it separately, or
let the analyst split it via refine.>

## Questions
<!-- analyst-only, when blocked on the user: one round in the format of
     drill.md — numbered, each with the analyst's recommended answer. Only real
     forks the user must settle (naming, scope, cost) — never facts a worker
     could look up. -->

## Answers
<!-- orchestrator-only, written after asking the user; numbers match the
     questions above. Analysts read these before speccing. -->

## Failure
<!-- implementer-only, after a FAILED attempt: what broke, what was tried.
     `retry` moves this into the body as history and reopens the PRD. -->
