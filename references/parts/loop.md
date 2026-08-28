# The loop

The seven steps, in order. Run until the board is drained, or everything left
is blocked on the user. `once` = one round. `status` = step 1 plus the progress
report, changing nothing.

**Every step is a fixed set of tool calls, not an analysis.** The loop's work
is choosing the next call and making it; a step that turns into a page of
reasoning has left the loop. Three rules keep it in:

- **Read the board with one call, and read it through the tool.**
  `@resources/board/plan.py scan` is step 1 — the whole board on one page,
  including the box counts. Walking the tree by hand or opening a `prd.md` for
  its state is the same information at a hundred times the tokens.
- **Write down what the tool cannot know.** `prds/.round.md`, rewritten at
  every transition — @references/parts/round.md. Context does not survive a
  compaction; that file does, and re-deriving a round costs more than the
  round.
- **An established fact is cited, never re-established.** A count verified at
  12:19 is in the round file with the time on it. Re-running the check buys
  nothing and costs the check. The same holds for a document's claim: check it
  once, write the correction, move on — reconciling it again is not diligence.

Where @references/parts/guard.md is wired, these three are not advice: a
hand-walked board, a board-reading command repeated over an unchanged board,
and a third read of an unchanged file are refused, and a PRD moved without the
round file rewritten says so. A refusal names the call that answers instead.

**1. Scan**

- **One call: `python3 @resources/board/plan.py scan`.** It reads
  `prds/settings.md`, every `prd.md`, every member board and every spec's
  acceptance boxes, and prints the board on one page: the counts, every term
  of the progress line, what is finished and waiting to be closed, what is
  asking, what a worker holds, what is dispatchable now in dispatch order,
  and what gates the rest. Each PRD appears in exactly one section.
- **The five sections come out already in the order to work them** — the
  pressure order, @references/parts/order.md: collect, waiting on you, in
  flight, ready, gated, which is steps 6, 2, 5 and the queue. The cut is after
  `waiting on you`: above it is this round's to act on, below it is already
  somebody's. The timeline stacks its rows by the same ranking, so the top of
  the chart and the top of the scan are one claim, and the route forward is
  read rather than re-derived.
- **Open a file only for what the scan does not print, and only when you are
  about to act on it** — a `## Questions` you are asking, a `## Failure` you
  are retrying, the contract you are briefing a worker with. Never open a
  `prd.md` to learn its state and never open a spec to count its boxes: the
  scan already read both, and re-reading them is what a compaction then
  charges you for twice.
- Read `prds/.round.md` — what this session already decided, verified and
  asked. Missing means the round has not started yet. @references/parts/round.md.
- Missing `prds/settings.md` means first run: `bash
  @resources/doctor.sh --fix`, print every line it printed, create
  `settings.md` per @references/settings.md, asking the user for the board
  language.
- `master of <n>` on the scan's first line means a **master board** — every
  member is already scanned and its PRDs addressed `@<member>/<prd>`. No
  `name:` on it: ask the user and write it before the round goes on.
- No board: create `prds/`, report it empty, stop.
- **Nothing to read for the persona.** It is session state, not a setting:
  the session is `engineer` until it is switched, and the first round with a
  job matching another signal row asks — @references/parts/personas.md. Every
  round's line carries the active id, per @references/parts/progress.md.
- Once per session, sweep a dead session's leftovers — `analyzing` with no
  live worker → `open`, `claimed` with no live worker → `failed`. Partial code
  may exist, and a human look is cheaper than a blind retry.
- Read the worker's **output** before sweeping, off the scan rather than off
  the disk. A PRD in the scan's **collect** section is an implementer that
  finished — collect it per step 6, and only then is anything left over a
  leftover. `analyzing` with spec files on disk is an analyst that finished:
  the transition is `specced` with the specs' `complexity` summed, not `open`.

A worker its infrastructure killed — API error, lost network, full disk — is
not a failed attempt:

- Resume THAT worker if it can be resumed — it holds the context, and its
  acceptance boxes are usually empty because the evidence died with it.
- First establish whether the tree is **deliberately** broken: a spec that
  watches a break fail leaves the break applied, and a worker killed in that
  window leaves broken code `claimed` does not hint at.
- Ask the worker which edit was in flight. It knows. The board does not.

**2. Answer**

- A PRD whose `## Answers` grew, or one a person moved in the view, is the
  user talking to the board — the view writes those directly.
- Collect `## Questions` from every `question` PRD, and from every **parked**
  PRD whose state or `mode:` names a human — parked is not asked, and a PRD
  waiting on someone with no round is waiting on nothing. Put them to the user
  as one round per @references/drill.md — the whole frontier, numbered, each
  with its three prepared answers so answering is a pick, not an essay. Use the
  ask-user-question mechanism where one exists, the three answers as the
  options. A question depending on one still open waits for the next round. A
  `## Questions` section that is a fork with no three answers is not askable
  yet: write the three yourself, or send the analyst back for them.
- Write answers under `## Answers` (`**Q1** — <text>`), set those PRDs
  `open`. No reply: leave them `question`, work the rest — the **asks** view
  shows the same round with the same three answers as buttons.
- What goes under `## Answers` is the **decision**, in the user's words or the
  picked option's, and nothing else. A remark about the question is not an
  answer to it: if the user's reply says the question was wrong, the round is
  what changes — rewrite it or delete it — and the answer records what was
  settled. `python3 @resources/questions.py check` is this paragraph as a
  mechanism, and it runs in `doctor`'s `questions` row.

**3. Refine**

- The analyst left the proposed split in its report. Create each child dir +
  `prd.md` (`state: open`, the child's contract as body), set the parent
  `open`.
- No usable split proposal: drill per @references/drill.md, then write that
  tree as the children. Never invent a split to keep the board moving.

**4. Spec ahead**

While count(*dispatchable* `specced`) < **pipeline** and dispatchable `open`
PRDs exist (leaf, unclaimed, priority desc): mark each `analyzing` +
`claim: <worker> <started>` and dispatch analysts in one parallel batch.

Dispatchable is the same test as step 5 — `needs:` all `done`, no footprint
clash with a `claimed` PRD. A `specced` PRD nobody can be handed is not
pipeline — counting it starves the analyst stage exactly when the board is
most stuck.

**5. Implement**

While count(`claimed`) < **workers** and `specced` PRDs exist: pick by
priority, skip any whose `needs:` are not all `done`, skip any whose footprint
overlaps a `claimed` PRD, mark `claimed` + `claim: <worker> <started>`,
dispatch an implementer.

- Both skips are real work. A footprint clash makes two workers edit one file.
  An unmet `needs:` sends a worker at code its dependency has not written.
- A skipped PRD stays `specced`. Say which of the two holds it, so a stalled
  board reads as a queue rather than a bug.
- The footprint is the union of the specs' `footprint:` and the PRD's own.

**6. Collect**

On each finished worker: validate the result (specs on disk / verify output
present), write the transition, commit per @references/parts/commits.md, clear
`claim:`, print the progress line, rewrite `prds/.round.md`, post the report
with `POST /report` per @references/parts/view.md, return to step 2.

**A collect is a checklist, not an analysis.** Those are six mechanical
actions on a result you already have — issue them as one batch, in one turn.
The worker's report is the evidence; the scan's `boxes c/t` is the count. If
something in the result genuinely needs deciding — a red check that may be
yours, a defect outside the worker's scope — it gets one short paragraph and a
decision, and the decision goes in the round file. It never becomes a
re-derivation of the round.

**Collect on the transition, never at the end of the round.** A PRD whose work
is done and whose state still says `claimed` blocks every PRD that `needs:` it
and every PRD its footprint clashes with — the board holds a finished thing and
schedules around it. One worker's result is one collect.

A PRD is **finished** when every acceptance box in its specs is `[x]` and
`prd.md` carries no open box of its own. That is not a state — it is a
condition read off **both files** on disk, which is why the scan reads it for
you: a PRD in its **collect** section is finished, and `boxes c/t` on any
other line is how far a live one has got. Counting boxes by opening the specs
yourself is the same number for the price of the whole file.

`- [x]` and `- [~]` are both closures, in either file: a struck box is a
contract term withdrawn with a reason beside it, never work still owed. And a
box is whatever a tree's own `done` gate calls a box — any of `-`, `*` or
`+`, or an ordered marker, with any run of spaces before the bracket — so
that a PRD the board offers for collection is never one a gate would reject.

**`boxes c/t` and the collect line answer different questions, and are meant
to disagree.** `c/t` is the specs' number and stays the specs' number:
`specs/*.md` under `## Acceptance`, the only thing that moves while a worker
works, which is what the lane bar is drawn from. Collect is the stricter
question and reads `prd.md` whole-file as well. A bar at 100% beside a PRD
that is not in **collect** is correct output, not a bug — the specs are
closed and `prd.md` is not. Folding several hundred static `prd.md`
requirement boxes into `c/t` would swamp the one live signal the plan has.

**Before `done` on work this session implemented, call the skeptic** — one
question, on your own judgment, no permission needed:
@references/parts/consult.md. You are checking your own work, which is the
one check you cannot run from inside your own frame. What it finds is advice;
the transition is still yours, and the gates below do not move.

| what is true                                                      | do                          |
|-------------------------------------------------------------------|------------------------------|
| every box `[x]`, verify output in the report, spot-checks run      | commit, `done`               |
| every box `[x]`, no verify output on record                        | run the verify commands yourself, then commit and `done` |
| boxes open, the worker is live                                     | leave it — this is progress, not a stall |
| boxes open, no live worker                                         | the sweep in step 1: `failed` |

`plan` prints the finished set before the queue, and the view leads its
frontier with it — see @references/parts/view.md.

A worker reports defects outside its own scope and never fixes them. What each
report becomes is the orchestrator's call, per @references/parts/derived.md — a
consequence for a requested PRD becomes a derived PRD with `origin: derived`
and `from:`, an instrument defect becomes a memo. Neither is `open` by default.
Check the tripwire before filing.

A finished analyst refills the pipeline. A finished implementer frees a slot.
Do not poll where results are pushed to you.

**7. Drill, then stop**

Nothing in flight and nothing dispatchable means the board is blocked on a
person, and a report is not what unblocks it. **A blocked board drills.** The
round's last act is one drill round over the whole open frontier —
@references/drill.md — not a list of what is stuck.

- **Assemble one frontier from the whole board**, never one PRD's. Each row is
  a fork with three prepared answers, numbered in one round:

  | what is stuck                                   | the fork put to the user                                  |
  |-------------------------------------------------|------------------------------------------------------------|
  | `question` whose `## Questions` are unanswered   | those questions, as the analyst wrote them                  |
  | parked on a person with no round written         | what it waits for, written as a fork — @references/parts/states.md |
  | `refine` with no usable split proposal           | the split itself: the children, and where the line falls    |
  | `failed`                                         | retry as it stands, redefine the contract, or drop it       |
  | `blocked` whose `needs:` only a person can land  | whether the event is coming, and what the board does meanwhile |

- **Ask what has not been asked.** `## Asked` in `prds/.round.md` says what is
  already out; a question out and unanswered is carried, never re-put. The
  drill widens instead — what the stalled question depends on, and what it
  would take to answer it.
- **It is a drill, not a status list.** Every fork carries three complete
  answers with one `(recommended)`, in the round format of
  @references/drill.md, through the ask-user-question mechanism where one
  exists. A fork with no prepared answers hands the board back to the user.
- **The orchestrator runs it.** A worker has no user to ask, so a drill is
  never dispatched, and nothing else is dispatched while one is running.
- **Answers land as step 2 lands them** — `## Answers`, then `open`, then the
  children a `refine` answer implies. Anything answered, and the round returns
  to step 1: a drill that unblocks work is a round that continues, not a round
  that ended.

Stop when the whole frontier is already out and nothing came back: report
per-state counts, every `question` / `refine` / `failed` PRD by name with what
it needs, and the final progress line.

- Rewrite `prds/report.md` per `@@report` — a round that moved anything owes
  the reader the new state, in their words rather than the board's.
- Rewrite `prds/.round.md` — what the next session would otherwise re-derive:
  what was decided, what was verified and when, what is out to the user.
  @references/parts/round.md.
- Everything left waiting on the user, and the live service up? Park
  `@resources/board/serve.py wait` in the background before stopping, per
  @references/parts/view.md — an answer written in the view then wakes the
  round that acts on it.

Report the two origins separately. Name what remains of the **deliverable**
first — requested PRDs not `done`, with `complexity`. List every `deferred`
derived PRD by name in the same breath, so parking is visible.
