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
subdirectories with their own. The settled contract is the body. Set
`state: open`.
