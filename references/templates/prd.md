---
state: open        # open|analyzing|refine|question|specced|claimed|blocked|done|failed
priority: 0        # higher first
complexity: 0      # 1-100, higher = more complex
blast-radius:      # high|mid|low
repo:              # the sub-repo the code lands in; delete if n/a
time:
  est:             # analyst, at spec time — wall-clock hours of one implementer run
  actual:          # orchestrator, on a clean done — what that run really took
  # claim: <worker> <started>   # orchestrator-only, present while a worker holds this PRD
---
<!-- Add your own keys freely, at any nesting; nothing outside state, priority,
     est, actual, claim, repo, needs and footprint is read, and nothing you add
     is ever dropped.
       needs:     — list of PRD dir names this one depends on; `plan` wave order
       footprint: — list of paths this PRD touches; the overlap check -->

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
