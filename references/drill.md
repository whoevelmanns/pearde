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

## The mechanism the round is put through

The mapping onto that mechanism, stated once: the **header** is the `### Qn:`
title, the **question** is the fork, the **three options** are the prepared
answers with their labels, and the mechanism's own free-text choice is *write
your own*. The HTML comment under the third answer is the technical anchor and
is never shown — it is what the orchestrator reads when it acts on the answer.
At a terminal with no such mechanism, print the round in the same words, with
*or write your own* as the fourth line.

Stated here rather than in @references/parts/loop.md, whose contract is the
seven commands and nothing a command does not enforce — a mapping onto a
rendering mechanism is neither, and putting it there took that file over the
120-line cap its own harness holds it to.

## The shape of a question

A question is a **fork**, not a briefing: **two sentences, then the question
mark** — what is being chosen, and what it changes for the person answering. A
question that restates the PRD body is not a question. The user already has the
PRD. The fork is what they lack.

Every question carries **exactly three prepared answers**, each **one plain
sentence of what they get** — never how it is built:

- Each answer is a complete decision — picking it settles the question with no
  further words.
- The three are genuinely different outcomes, not three phrasings of one.
- Mark one `(recommended)`.
- Writing them is your work. The user's job is one keypress, or their own
  sentence when all three are wrong.

The last line under every question is the open door: **or write your own**. The
numbering is how the three readers parse the round; those words are how it is
said to a person.

### What a question may never say

Write for the person who asked for this, not for the orchestrator. In the fork,
the answer labels and the answer text:

| never                                    | because                                                    |
|------------------------------------------|------------------------------------------------------------|
| a backtick, a path, a file extension     | the reader has no tree open                                |
| a PRD slug of this board, a `Q<n>` cross-reference | a name is a ticket number to someone who did not write it |
| board vocabulary — a state name, a frontmatter key, a worker or persona word | that vocabulary is the orchestrator's |
| more than 60 words in the fork, 25 in an answer | past that it is a briefing, and this file already forbids one |
| "should we also…", a fact a build could find | a fact is dispatched, never asked — *Facts vs decisions* below |

`python3 @resources/questions.py check [board]` is that table as a mechanism:
one line per row it catches, naming the word it caught. `pearde release <prd>
question` runs it, so a round that fails is refused rather than written.

Round format — this exact shape, in the PRD's `## Questions` and in the round
put to the user. The view parses it.

```
### Q1: <question title>

<the fork, two sentences, ending in "?">

1. **<label>** — <complete answer, paste-ready as the decision> (recommended)
2. **<label>** — <a genuinely different complete answer>
3. **<label>** — <a third direction, not a compromise of 1 and 2>
```

Worked, and this is what a passing question looks like:

```
### Q1: What the page shows first

You are choosing what a person sees first when they open the board: the work
in progress, or the questions waiting on them. Whichever is first is what they
will act on; the other needs a click?

1. **Questions first** — the page opens on what is waiting on you; the work is one click away. (recommended)
2. **Work first** — the page opens on what is happening; your questions are one click away.
3. **Ask each time** — the page remembers whichever you opened last.

<!-- for the board: serve.py `/` default route; the-page-shows-the-round spec02 -->
```

The technical anchor — which files, which slug, which spec the answer lands in
— goes in an HTML comment directly under the third answer, and **nothing that
shows a question to a person shows it**. The orchestrator reads it when it acts
on the answer; the checker never sees it, and the view strips it.

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

A blocked board is a drill whose questions are already written down. Step 8 of
@references/parts/loop.md is that entry point: nothing dispatchable means every
remaining PRD waits on a person, and the round's last act is one drill round
over all of them rather than a report naming them.

The count on the scan is the second entry point: when `pearde scan` prints the
**drill** section — more than one unanswered question on the board, the header
saying `asking N over M PRDs` — the round opens on that drill before anything
is dispatched, even though the rest of the board is moving. The drill is the
orchestrator's, so `pearde claim` refuses with `asking N — drill first` until
the questions are out; one question standing is not a gate, and is put as any
round is. Zero prints nothing.

Round one's frontier is the board itself — every unanswered `## Questions`,
every PRD parked on a person with no round written, every `refine` with no
usable split, every `failed`, every `blocked` whose `needs:` only a person can
land. From there the rules above are unchanged: the frontier is recomputed
after every answer, and the drill ends when it is empty.

- **One round for the board, never one per PRD.** Five stuck PRDs are one
  numbered round, not five conversations.
- **A question already out is carried, not re-put** — `## Asked` in
  `.pearde/.state/round.md` is what is out. Widen instead: ask what the stalled question
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
workflow is the analyst's, at spec time — `## Route` in its report, `runs: 0`
from `specced` — never the drill's.
