# Drilldown

Interview the user until you reach a shared understanding. Record it as a **PRD
tree**: every decision branches into the decisions that hang off it.

## Rounds

The **frontier** is every decision whose prerequisites are settled — the
questions askable now without guessing at answers not yet heard.

1. Compute the frontier.
2. Ask all of it in one round, numbered, each with three prepared answers.
3. Wait for the user's picks — or their own answers.
4. Answers reshape the tree: settled decisions push the frontier outward.
   Recompute and repeat.

A question whose answer depends on another question still open in this round
belongs to a later round.

## The shape of a question

A question is a **fork**, not a briefing — one to three sentences ending in a
question mark: what splits, and what each side costs. A question that restates
the PRD body is not a question. The user already has the PRD. The fork is what
they lack.

Every question carries **exactly three prepared answers**:

- Each answer is a complete decision — picking it settles the question with no
  further words.
- The three are genuinely different outcomes, not three phrasings of one.
- Mark one `(recommended)`.
- Writing them is your work. The user's job is one keypress, or their own
  sentence when all three are wrong.

Round format — this exact shape, in the PRD's `## Questions` and in the round
put to the user. The view parses it.

```
### Q1: <question title>

<the fork, 1-3 sentences, ending in "?">

1. **<label>** — <complete answer, paste-ready as the decision> (recommended)
2. **<label>** — <a genuinely different complete answer>
3. **<label>** — <a third direction, not a compromise of 1 and 2>
```

Put the round through the ask-user-question mechanism where one exists — one
question per fork, the three answers as the options. A pick and the user's own
words are equally an answer.

Answer format, written under `## Answers`, numbers matching:

```
**Q1** — <the picked option's text verbatim, or the user's own words>
```

The view writes the same line with the moment it was settled — `**Q1**
*(answered 2026-08-28 14:22)* — …` — and orders its answered panel by it. The
stamp is optional when a round is answered at a terminal: the id and the
decision are the contract, the date only buys a place in that order.

## The heading is the claim

Neither heading is a slot to leave empty. `## Questions` says a round is
waiting on the user, and `## Answers` says one came back — so an empty
`## Questions` stops the board on nothing, and an empty `## Answers` reads as
answered when it is not. **Write the heading when it has content, and delete
it when it does not.** The same goes the other way: an `## Answers` section
with no `## Questions` above it is an answer to a question nobody wrote down,
and a PRD parked on the user that carries no round never says what it is
asking — both are indistinguishable, from outside, from a board with nothing
to ask.

`python3 @resources/questions.py check [board]` is that paragraph as a
mechanism, and `doctor`'s `questions` row runs it. It reports a heading with
nothing under it, a question that asks nothing or carries no recommended
answer, an answer to nothing, and a parked PRD that never asked. An answered
round is history and is left alone.

## The board's own frontier

A blocked board is a drill whose questions are already written down. Step 7 of
@references/parts/loop.md is that entry point: nothing dispatchable means every
remaining PRD waits on a person, and the round's last act is one drill round
over all of them rather than a report naming them.

Round one's frontier is the board itself — every unanswered `## Questions`,
every PRD parked on a person with no round written, every `refine` with no
usable split, every `failed`, every `blocked` whose `needs:` only a person can
land. From there the rules above are unchanged: the frontier is recomputed
after every answer, and the drill ends when it is empty.

- **One round for the board, never one per PRD.** Five stuck PRDs are one
  numbered round, not five conversations.
- **A question already out is carried, not re-put** — `## Asked` in
  `prds/.round.md` is what is out. Widen instead: ask what the stalled question
  depends on. A frontier that is entirely already out is where the round stops.
- **Answers go back where they were asked** — `## Answers` in each PRD, numbers
  matching, then `open`; a `refine` answer becomes children per step 3 of the
  loop. The tree below is for a drill that starts from a request, not from a
  board that already holds one.
- **The orchestrator runs it.** A worker has no user to ask, so a drill is
  never dispatched, and nothing else is dispatched while one runs.

## Facts vs decisions

| kind         | whose job | how                                                     |
|--------------|-----------|----------------------------------------------------------|
| **fact**     | yours     | dispatch a worker to find it in the environment. Never ask the user for anything you could look up |
| **decision** | the user's | put it to them and wait                                  |

Do not block on a fact. A running exploration is an unsettled prerequisite, so
only the questions downstream of it wait — ask the rest of the frontier now.

## Done

The session is done when the frontier is empty — every branch visited, nothing
silently assumed. Do not act on it until the user confirms the shared
understanding.

## Output

Write the tree in the board's own shape, per @references/parts/board.md: one
directory per decision holding a `prd.md`, the decisions hanging off it as
subdirectories with their own — and write it through the commands, never by
hand. The root is `pearde add "<title>" --body -` with the settled contract on
stdin; each branch is `pearde refine <prd> < split`, a `## Split` table of the
decisions hanging off it (`| child | contract | needs |`), repeated per
level. Every PRD arrives `state: open` from the template. A hand-made
`state:` is the edit @references/parts/guard.md refuses.

Attach a workflow while the tree is being written, not later. `python3
@resources/workflows.py list` is the library; when a workflow's `## Use when`
fits a branch, write `workflow: <slug>` on that child, so the worker that
eventually takes it is handed the route with its brief. A branch nothing fits
carries no key — the brief alone is the honest state, and writing a new
workflow is `workflow add`, an act of the orchestrator's at `runs: 0`, never
the drill's.
