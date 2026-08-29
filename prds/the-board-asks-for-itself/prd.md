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
footprint:
  - references
  - resources
  - prds/workflows
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

# the board asks for itself

When this is done, three things the board today leaves to a person happen on
their own, and the one thing that still needs a person is put to them in
words they can answer without knowing the board:

1. **A route is written when none fits.** A PRD is never specced without a
   `workflow:`. When the library holds nothing for the job, the analyst
   drafts the route from the build it just did and `pearde specced` writes it
   to the library at `runs: 0` and attaches it. The first implementer's run
   then improves it through the collect that already exists.
2. **Two open questions start a drill.** A session whose scan finds more than
   one unanswered question on the board opens with one drill round over all
   of them, before anything is claimed. One question is put as today.
3. **Every question is in plain words.** What is being decided and why it
   matters, in one or two sentences a person outside the codebase can read;
   then three complete answers, one recommended, and always the choice to
   write their own. No PRD names, no paths, no state names, no keys, no
   ticket-like ids. The technical anchor the orchestrator needs to act on the
   answer rides in a comment the reader never sees.

## Why

The board records state, decisions and how — but two of the three still
arrive by hand: a workflow is written by a person or by the drill, and a drill
over a stalled board starts only when nothing at all is dispatchable (loop
step 7). Meanwhile the questions that reach the user are written by an
analyst for an orchestrator, so they carry slugs, paths and states the user
has to translate before answering. The user's words: *explain WHAT he is
deciding and why in straightforward simple terms, no mention of the ticket
numbers or too much technical term; do you want a, b or c for this problem, or
write your own. That's it.*

## Constraints

- The nine states, the gates, one orchestrator per board — unchanged.
- The round format's skeleton (`### Qn:`, three numbered answers, one
  `(recommended)`, `**Qn** — …` under `## Answers`) stays — three readers
  parse it (`questions.py`, `transitions.py answer`, the view). What changes
  is what the prose is held to, and a check that holds it.
- A workflow is written from a run, never from reading — the analyst's route
  comes from the build it ran, and lands at `runs: 0` as every new file does.
- Nothing names an agent, a tool, a hook or a vendor.

## Non-goals

- No detection of "a job repeated" across PRDs. Creation lives at one moment:
  `specced`, when nothing fit. A route written for a one-off is pruned by the
  rule that already exists — `runs: 0` beside an old `date` is a file to
  delete.
- No change to how answers are recorded or how a `refine` answer splits.
- No new view page. The asks page renders what the file holds.

## Children

Work flows to the leaves; this PRD is done when every child is.

| child                            | delivers                                                                     | needs        |
|----------------------------------|------------------------------------------------------------------------------|--------------|
| `a-question-in-plain-words`      | the plain-words rule, the checker that holds it, the hidden anchor, the ask mapping | —      |
| `two-questions-start-a-drill`    | the count on the scan, the drill as step 2 when it is over one, the claim gate | plain-words |
| `a-route-is-written-at-spec-time`| `## Route` in the analyst's report, `specced` writes and attaches it, never `none fit` | —    |

## Pointers

- @references/drill.md — the round format and the board's own frontier.
- @references/parts/loop.md steps 2, 6, 7 — where each child lands.
- @references/parts/workers.md — the analyst brief that writes questions and names `none fit`.
- @references/parts/workflows.md — when a file is written; the collect that improves it.
- @resources/questions.py · @resources/board/specs.py · @resources/board/plan.py — the three readers that grow.

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
