---
state: open        # open|analyzing|refine|question|specced|claimed|blocked|done|failed
origin: requested  # requested = the user asked | derived = the board found it
# from:            # derived only — the PRD whose work surfaced this one
priority: 60        # higher first
complexity: 0      # analyst, at spec time — 1-100. THE WEIGHT the board schedules by
blast-radius:      # analyst, at spec time — high|mid|low. What breaks if this is wrong
repo: pearde
# workflow:        # OPTIONAL — how this kind of job is done: a slug in
#                  #   prds/workflows/. @references/workflow.md.
#                  #   Absent = the brief alone, as before workflows
time:              # OPTIONAL. See @references/parts/order.md
  est:             # the weight, only when complexity is absent. Not a duration
  actual:          # a record. Nothing reads it
  # claim: <worker> <started>   # orchestrator-only, present while a worker holds this PRD
needs:
  - a-question-in-plain-words
footprint:
  - references/drill.md
  - references/parts/loop.md
  - references/parts/round.md
  - references/parts/guard.md
  - resources/questions.py
  - resources/board/plan.py
  - resources/board/transitions.py
---
<!-- Ordering reads three axes and no clock: dependency (needs + footprint),
     vision importance (priority), and complexity/blast-radius. Add your own
     keys freely, at any nesting. Nothing outside state, origin, from,
     priority, complexity, blast-radius, claim, repo, workflow, needs and
     footprint is read, and nothing you add is ever dropped.
       needs:     — PRD dir names this one depends on. A hard gate in `plan`
       footprint: — paths this PRD touches. The overlap check
       workflow:  — the route a worker is handed, expanded into its brief

     One sitting is the limit: specs summing `complexity` above `split-above`
     or counting above `specs-above` (both in prds/settings.md, default 40 and
     6) make the analyst's verdict REFINE, and `pearde refine` lands the split
     under `## Children` here — the contract above it stays as written.

     A derived PRD states, in the body, which requested PRD it would otherwise
     get wrong. If it cannot, it is filed `state: deferred` — and if fixing it
     would change only how loudly the board notices, it is a memo, not a PRD.
     See @references/parts/derived.md. -->

# two questions start a drill

When this is done, a session that scans a board holding more than one
unanswered question opens with a drill round over all of them — put to the
person in one go, in the words @references/drill.md now requires — and claims
nothing until that round is out. One unanswered question is put as step 2
puts it today; none, and the loop runs as before.

## The count

An **unanswered question** is a `### Qn:` under `## Questions` with no
matching `**Qn**` under `## Answers`, on any PRD whose state is not `done`,
`deferred`, `superseded` or `out-of-scope`. `pearde questions list` already
walks this; the count becomes one function both readers call.

`pearde scan` prints it in the header line — `asking 3 over 2 PRDs` — and
when it is over one, a section **drill** stands first, above *collect*,
listing every question by PRD and title with `out` beside the ones
`prds/.round.md` `## Asked` already lists. Zero prints nothing.

## The trigger

| unanswered | step 2 is                                                                              |
|------------|-----------------------------------------------------------------------------------------|
| 0          | nothing                                                                                 |
| 1          | that question, put as today                                                             |
| ≥ 2        | one drill round over all of them per @references/drill.md *The board's own frontier* — before step 3, before any claim; the questions already `out` are carried, the rest are put |

The drill is the orchestrator's — a worker has no user to ask. While it is
open nothing is dispatched: `pearde claim` refuses with `asking N — drill
first` when two or more unanswered questions are not yet in `## Asked`. Once
they are out — the round has been put, answered or not — claiming resumes;
a question waiting on a person does not stop the rest of the board, only an
unput one does.

Answers land as step 2 lands them: `pearde answer <prd> Q<n> "<text>"`, the
PRD `open` on its last. The round returns to step 1. Step 7 is unchanged:
it is the same drill, reached because nothing else was left rather than
because two questions were.

## Where it lands

| where                              | change                                                                     |
|------------------------------------|----------------------------------------------------------------------------|
| @resources/questions.py            | `unanswered(board)` — the list `list` prints and `scan` counts, one reader |
| @resources/board/plan.py           | the header count and the *drill* section, `out` read from the round file   |
| @resources/board/transitions.py    | the `claim` gate                                                           |
| @references/parts/loop.md          | step 1 names the count; step 2 is the table above; step 7 says it is the same drill |
| @references/drill.md               | *The board's own frontier* gains its second entry point: the count on the scan |
| @references/parts/round.md         | `## Asked` is what the gate reads — said there                             |
| @references/parts/guard.md         | where the guard is wired, a claim over an unput frontier is a refusal it names |

## Done when

- A fixture board with two `question` PRDs: `pearde scan` prints `asking 2
  over 2 PRDs` and a *drill* section first; `pearde claim <other> w --as
  engineer` is refused naming `asking 2`; after both titles are written to
  `## Asked`, the same claim goes through.
- The same board with one question: no *drill* section, the claim goes.
- A `done` PRD with an old unanswered round counts zero.

## Non-goals

- No timer, no wakeup. The drill starts on a scan; `pearde view wait` already
  wakes the round when an answer is written in the view.
- The threshold is not a setting. Over one is the rule; a board that wants
  every question drilled has no second question to wait for.

<!-- Three more headings exist, and none of them is a slot to copy down. Each
     is a claim about the state of this PRD, so an empty copy of it is a false
     one: an empty `## Questions` stops the board on nothing, an empty
     `## Answers` reads as answered, an empty `## Failure` reads as a failed
     attempt. Write the heading when it has content; until then it is absent,
     which is the honest state. @resources/questions.py reports the empty
     ones, and `doctor`'s `questions` row runs it. -->

<!-- `## Questions` — analyst-only, when blocked on the user: one round in the
     format of drill.md — `### Q1: <title>`, the fork in 1-3 sentences ending
     in "?", then exactly three prepared answers, each a complete decision,
     one `(recommended)`. Only real forks the user must settle (naming, scope,
     cost) — never facts a worker could look up, never the PRD restated. A PRD
     parked on the user with no such round never says what it is asking. -->

<!-- `## Answers` — orchestrator-only (or the view), written after asking the
     user: `**Q1** — <the picked answer verbatim, or the user's own words>`,
     numbers matching the round above it. Analysts read these before speccing.
     An `## Answers` with no `## Questions` above it answers nothing. -->

<!-- `## Failure` — implementer-only, after a FAILED attempt: what broke, what
     was tried. `retry` moves this into the body as history and reopens the
     PRD. -->
