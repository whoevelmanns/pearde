# Drilldown

Interview the user until you reach a shared understanding. Record it as a **PRD
tree**: every decision branches into the decisions that hang off it.

## Rounds

The **frontier** is every decision whose prerequisites are settled — the
questions askable now without guessing at answers not yet heard.

1. Compute the frontier.
2. Ask all of it in one round, numbered, each with your recommended answer.
3. Wait for the user's answers.
4. Answers reshape the tree: settled decisions push the frontier outward.
   Recompute and repeat.

A question whose answer depends on another question still open in this round
belongs to a later round.

Round format:

```
Question *Q1*: **<question title>**:
<question body, may be multiple paragraphs, may offer choices>

Recommendation <your recommended answer>

---

Question *Q2*: **<question title>**:
<question body>

Recommendation <your recommended answer>
```

## Facts vs decisions

| kind         | whose job | how                                                     |
|--------------|-----------|----------------------------------------------------------|
| **fact**     | yours     | dispatch a worker to find it in the environment. Never ask the user for anything you could look up |
| **decision** | the user's | put it to them and wait                                  |

Do not block on a fact. A running exploration is an unsettled prerequisite, so
only the questions downstream of it wait — ask the rest of the frontier now.

## Done

The session is done when the frontier is empty: every branch visited, nothing
silently assumed. Do not act on it until the user confirms the shared
understanding.

## Output

The tree is the board's own shape, per `README.md`: one directory per decision
holding a `prd.md`, the decisions hanging off it as subdirectories with their
own. Write it there — settled contract as the body, `state: open` — and the
loop takes it from there.
