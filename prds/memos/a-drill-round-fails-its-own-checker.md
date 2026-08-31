---
memo: a-drill-round-fails-its-own-checker
kind: note
status: decided
subject: questions.py reads each prepared answer as a question, so a well-formed drill round reports six problems
date: 2026-08-28
---

# a-drill-round-fails-its-own-checker — the format and its checker disagree

## Decision

Not decided. This records a reproduced defect and the reason it is not being
fixed today, so that whoever picks it up starts from the measurement rather
than from the argument.

`resources/questions.py check` reports a correct drill round as six problems.
It is recorded, not filed: @references/parts/derived.md's tripwire was at
parity when it was found, and the user ruled that the deliverable finishes
first.

## Why

@references/drill.md's round format gives each question three prepared
answers, written as a numbered list. `questions.py`'s `ITEM_RE` is

```python
ITEM_RE = re.compile(r"^(###\s+\S.*|\d+\.\s+\S.*)$", re.M)
```

so a top-level `1.` is read as a question head exactly like `### `. Every
prepared answer becomes its own question.

**Reproduced**, fixture: one `question` PRD with one `### Q1` head and three
numbered answers, the first carrying `(recommended)`, in a scratch board
outside the repo.

```
a-fork: question 1 (Q1: which way does the reader go?) carries no recommended answer
a-fork: question 2 (1. A new file beside the others (recommended) …) asks nothing
a-fork: question 3 (2. A section inside the existing file …) asks nothing
a-fork: question 3 (2. A section inside the existing file …) carries no recommended answer
a-fork: question 4 (3. Neither; the door is a flag …) asks nothing
a-fork: question 4 (3. Neither; the door is a flag …) carries no recommended answer
exit=1
```

Six lines, one question, and the file is correct. Note the first line: the
recommended answer *is* present — it was split off into "question 2", so the
checker then reports its absence from the question it belongs to. The defect
does not merely add noise; it inverts one verdict.

`view.js` parses the same rounds correctly, so the format is not ambiguous —
one reader of it is wrong.

The blast radius is the `questions` row in `resources/doctor.sh`. It reads
`ok` today only because no PRD on this board is currently in `question` with a
round written. The first drill round that lands turns `doctor` red and tells
the orchestrator that its correct round is malformed — at exactly the moment
the board is blocked on a person and least able to afford a false alarm.

## Alternatives considered

**File it as a derived PRD.** By @references/parts/derived.md's own test it is
one — fixing it changes what ships, not only how loudly the board notices.
It lost on timing, not on merit: three derived PRDs were already parked at the
tripwire by the user's decision, and filing a fourth is the board working on
itself, which is the thing the tripwire exists to stop.

**Fix it inline as an instrument repair.** One anchored regex; the fix is
small. It lost because `questions.py` is nobody's footprint this round, a
second session is writing this repo, and a change to a shared checker made
outside any PRD is the kind of edit that reappears as a mystery — the
`references/parts/loop.md` miscount landed exactly that way, wrong the day it
was written.

**Say nothing until it fires.** Rejected outright. It fires when the board is
already blocked on a person, and a false alarm there costs the user's
attention at the moment it is most expensive.

## Consequences

- `doctor`'s `questions` row is trustworthy only while no drill round exists
  on the board. Read it as such until this is fixed.
- The fix is one regex plus a fixture that would have caught it — a round with
  numbered answers, which no test currently has. Whoever takes it should add
  the fixture first and watch it fail.
- It deliberately says nothing about `view.js`, which reads the same rounds
  correctly. Two readers of one format is the deeper question and this memo
  does not open it.

## Closed 2026-08-29 — fixed, and this memo was stale

`3a84801` (`transitions-are-commands`) split the one matcher into `HEAD_RE`
and `ITEM_RE` and splits on heads before items, so a numbered answer is no
longer read as a question head. The defect is gone.

Verified by re-running **this memo's own fixture**, not by reading the diff —
one `question` PRD, one `### Q1` head, three numbered answers, the first
carrying `(recommended)`:

```
python3 resources/questions.py check <fixture>
exit 0, no output
```

Where this memo records six lines and exit 1.

**Kept rather than deleted**, because the shape is worth having on record: a
checker and the format it checks were written by different rounds and
disagreed, and the disagreement inverted a verdict — it reported the
recommended answer missing while it was present. The fix is in `3a84801` and
the fixture above is how to tell if it ever regresses.

**Found stale by the analyst on `a-question-in-plain-words`**, which had been
handed this memo as live context and rebuilt the fixture rather than trusting
it. A memo carried forward unverified is the same defect as a check written
from the answer, and this one was mine.
