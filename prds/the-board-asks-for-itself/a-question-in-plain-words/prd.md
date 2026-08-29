---
state: done        # open|analyzing|refine|question|specced|claimed|blocked|done|failed
origin: requested  # requested = the user asked | derived = the board found it
# from:            # derived only — the PRD whose work surfaced this one

## Settled 2026-08-29 — the nine, read narrowly

This PRD's table forbids "one of the nine state names" in a question, and its
own worked example says *"when they open the board"* — `open` is one of the
nine. The contract refuses the example it ships as correct.

Its author is a session that committed once and left, so the fork could not be
put to them. **The user settled it: catch only the board-only words.**

`analyzing`, `specced`, `claimed`, `refine` and `deferred` are refused as bare
words — nobody says those about their own work, so one appearing in a question
means the board's vocabulary leaked into it. `open`, `question`, `blocked`,
`done` and `failed` are ordinary English about one's own work and are caught
only in their board spelling, which the backtick row already refuses.

Why this rather than the literal nine: the literal reading refuses *"is this
done?"* and *"should it stay open?"* — questions a person would actually be
asked — and would require rewriting this PRD's own example. Why not
backticks-only: that turns the rule back into guidance a worker can forget,
which is the failure this board has spent the week closing.

The deviation from the table is deliberate and pinned by a box in spec01, so an
implementer cannot silently widen it back.
priority: 60        # higher first
complexity: 32      # analyst, at spec time — 1-100. THE WEIGHT the board schedules by
blast-radius: high
repo: pearde
# workflow:        # OPTIONAL — how this kind of job is done: a slug in
#                  #   prds/workflows/. @references/workflow.md.
#                  #   Absent = the brief alone, as before workflows
time:              # OPTIONAL. See @references/parts/order.md
  est:             # the weight, only when complexity is absent. Not a duration
  actual:          # a record. Nothing reads it
  # claim: <worker> <started>   # orchestrator-only, present while a worker holds this PRD
footprint:
  - references/drill.md
  - references/parts/workers.md
  - references/parts/loop.md
  - references/templates/prd.md
  - resources/questions.py
  - resources/board/transitions.py
  - resources/board/view.js
actual: 1.6h
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

# a question in plain words

When this is done, every question put to a person — at a terminal, through
the ask mechanism, on the view's asks page — reads as: *this is what you are
choosing, this is why it matters; do you want a, b or c — or write your own.*
A round that does not read that way is refused before it reaches them.

## The rule

The fork is **two sentences, then the question mark**: what is being chosen,
and what it changes for the person answering. The three answers are each
**one plain sentence of what they get**, not how it is built. The last line
under every question is always the open door: *or write your own.*

In the fork, the answer labels and the answer text:

| never                                   | because                                                    |
|-----------------------------------------|------------------------------------------------------------|
| a backtick, a path, a file extension    | the reader has no tree open                                |
| a PRD slug of this board, a `Q<n>` cross-reference | a name is a ticket number to someone who did not write it |
| one of the nine state names, a frontmatter key, a worker or persona word | board vocabulary is the orchestrator's |
| more than 60 words in the fork, 25 in an answer | past that it is a briefing, and @references/drill.md already forbids one |
| "should we also…", a fact a build can find | the analyst brief already forbids it; the checker now catches it |

The technical anchor — which files, which slug, which spec the answer lands
in — is written in an HTML comment directly under the third answer:

```
### Q1: What the page shows first

You are choosing what a person sees first when they open the board: the work
in progress, or the questions waiting on them. Whichever is first is what
they will act on; the other needs a click?

1. **Questions first** — the page opens on what is waiting on you; the work is one click away. (recommended)
2. **Work first** — the page opens on what is happening; your questions are one click away.
3. **Ask each time** — the page remembers whichever you opened last.

<!-- for the board: serve.py `/` default route; the-page-shows-the-round spec02 -->
```

Nothing that shows a question to a person shows the comment. The
orchestrator reads it when it acts on the answer.

## Where it lands

| where                              | change                                                                                  |
|------------------------------------|-----------------------------------------------------------------------------------------|
| @references/drill.md               | *The shape of a question* becomes the rule above, with the worked example. Numbers stay in the file; the words *a, b or c — or write your own* are how it is said |
| @references/parts/workers.md       | the analyst brief's QUESTION verdict cites the rule and shows the example; one line: *write for the person who asked for this, not for the orchestrator* |
| @resources/questions.py            | `check` reports every row of the table above, per question, naming the word it caught — the slug, the state, the path. Comments are stripped before the check and never reported |
| @resources/board/transitions.py    | `release <prd> question` and `answer` run that check — a round that fails is refused with the line, not written |
| @references/parts/loop.md step 2   | the ask mapping, stated once: the header is the `### Qn:` title, the question is the fork, the three options are the answers with their labels, the mechanism's own free-text choice is *write your own*. At a terminal with no mechanism, the round is printed in the same words with *or write your own* as the fourth line |
| @resources/board/view.js           | the asks page and the inspector strip the comment and print *or write your own* over the own-answer box |
| @references/templates/prd.md       | the `## Questions` comment says the rule in one line and points at drill.md |

## Done when

- `pearde questions` on a fixture board with one question naming a PRD slug,
  one naming `specced`, one with a path, one with a 70-word fork, and one
  clean question reports exactly four lines and names the caught word in each.
- `pearde release <prd> question` on the slug-naming fixture exits 1 and the
  PRD's state is unchanged.
- The clean fixture question, rendered by the view's asks page, shows no
  comment and shows *or write your own*.
- Every `## Questions` already on this board that is unanswered passes — or
  is rewritten by this PRD, listed in its report.

## Non-goals

- The numbering does not change. `**Q1**`, `1.`/`2.`/`3.` stay as the three
  readers parse them.
- No translation layer: the analyst writes it plain, the check holds it plain.
  Nothing rewrites a technical question into a plain one at ask time.

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
