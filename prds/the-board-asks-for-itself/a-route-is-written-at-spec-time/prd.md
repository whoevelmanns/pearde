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
  - references/parts/workers.md
  - references/parts/workflows.md
  - references/parts/loop.md
  - references/drill.md
  - resources/board/specs.py
  - resources/workflows.py
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

# a route is written at spec time

When this is done, no PRD is specced without a `workflow:`. When the library
holds no route for the job, the analyst drafts one from the build it just ran
and `pearde specced` writes it to `prds/workflows/` at `runs: 0`, checks it,
and attaches it to the PRD in the same call. The implementer that follows is
handed the route with its brief, and its run improves it through the collect
@references/parts/workflows.md already describes. `workflow: none fit` stops
being a verdict the board accepts.

## The analyst's part

The analyst runs `pearde workflow list` before the build and follows the
workflow whose `## Use when` fits, as today. When none fits, the report
carries **`## Route`** after `## Scores`:

- `workflow: <new-slug>` in `## Scores` — a slug the library does not hold.
- The workflow file body per @references/workflow.md: `## Use when` written
  for the *next* PRD like this one, `## Steps` as `| # | atomic | why | on
  failure |`.
- Under it, one `### atomic <slug>` block per step whose atomic the library
  does not hold: `## Do`, `## Done when`, `## Fails when` empty. A step whose
  atomic exists names it and writes no block.

The route is the build the analyst ran, in order — never a route it imagines.
A step the build did not take is not a row.

## `pearde specced`

`pearde specced <prd> --blast <x> --workflow <slug>` gains one case: a slug
the library does not hold, with a `## Route` on stdin (`--route -`) — it
writes the files from @references/templates/workflow.md and
`atomic.md` with `date: <today>`, `runs: 0`, runs `pearde workflow check`,
refuses the whole call on red with nothing written, and only then writes
`workflow:` and `specced`. A slug the library holds with a `## Route` on stdin
is refused — the route exists; follow it. `none fit` is refused, naming
`## Route`.

The files ride the PRD's commit at collect, as edited workflow files do —
`pearde collect --also`. The PRD's own `footprint:` does not grow.

## Where it lands

| where                              | change                                                                     |
|------------------------------------|----------------------------------------------------------------------------|
| @references/parts/workers.md       | the analyst brief: *list first, follow what fits, draft what does not* — the `## Route` shape; `none fit` leaves the `## Scores` block |
| @resources/board/specs.py          | `--route -`, the write, the check, the refusals                            |
| @resources/workflows.py            | `add` — one slug, one body, written from the template, refused when taken. `specced` calls it; the skill's `workflow add` handle is the same door |
| @references/parts/workflows.md     | *When a file is written* gains the row: *nothing fits at spec time — the analyst's route, written by `specced`, `runs: 0`* |
| @references/parts/loop.md step 4/6 | `specced` reads `## Route`; the first collect counts `runs: 1` and fills `## Fails when` |
| @references/drill.md               | the drill still attaches what fits and leaves the rest keyless — the analyst writes it, not the drill; said in one line |

## Done when

- A fixture board with an empty library: an analyst report carrying `## Route`
  with two new atomics and one existing → `pearde specced` writes three files,
  `pearde workflow list` shows the workflow at `runs: 0`, and the PRD carries
  `workflow: <slug>`.
- The same call with `## Route` naming a slug the library holds: refused,
  nothing written.
- `pearde specced <prd> --workflow none`: refused naming `## Route`.
- A report whose `## Route` fails `workflow check`: refused, nothing written,
  the PRD not `specced`.
- Every PRD `specced` on this board after this lands carries `workflow:` —
  `pearde scan` shows `wf <slug>` on each.

## Non-goals

- No detection that a job recurred. One moment, one writer.
- No merge of two drafts for one slug; the second analyst is refused and
  follows the first's.
- The drill does not write workflows. It attaches what fits.

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
