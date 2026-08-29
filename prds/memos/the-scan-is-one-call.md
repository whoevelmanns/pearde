---
memo: the-scan-is-one-call
kind: decision
status: decided
subject: Step 1 is one `plan.py scan` call and one round file, never a hand-walked tree
date: 2026-08-27
---

# the-scan-is-one-call — the board is read by the tool, and what the tool cannot know is written down

## Decision

The loop reads the board with `@resources/board/plan.py scan` — one call
returning the counts, every progress-line term, what is finished and waiting
to be closed, what a worker holds, what is asking, what is dispatchable now in
order, and what gates the rest. A round never walks `prds/` by hand, never
opens a `prd.md` to learn its state, and never opens a spec to count its
boxes.

What the scan cannot know — what was decided, what was verified and when, what
is out to the user, what is owed next — is written to `prds/.round.md` at
every transition, per @references/parts/round.md. After a compaction the
recovery is that file plus one `scan`, in that order and nothing else.

## Why

The 2026-08-27 master-board round (session `aac69c59`, 97 minutes) spent
**318,584 output tokens**, of which 160,000 — half — were thinking blocks that
hit the 32,000-token output cap and emitted no tool call and no text. It made
179 tool calls across 138 responses, and auto-compacted four times, at 163.5k,
175.0k, 200.5k and 188.3k context.

Three mechanisms, all of them the loop's own text:

- **Step 1 said "`find prds -type f -name prd.md`, parse every frontmatter"**,
  which is a tree walk plus a read per PRD on a 227-PRD board — while
  `plan.py` already computed the same states, gates, footprint edges and
  acceptance counts for the plan. The round ran the identical tree sweep four
  times and a Cargo/shared-crate check three times, each with unchanged
  results.
- **"A PRD is finished when every acceptance box in its specs is `[x]` — read
  off the specs on disk"** was read as an instruction to open the specs. Six
  spec files and a learning doc, 44 KB, were read three to four times each,
  for a number `plan.py` prints as `boxes 9/9`.
- **Nothing was written down**, so each of the four compactions was followed
  by a full re-derivation of a state that fits in fifteen lines, which
  inflated the context again, which forced the next compaction. One
  reconciliation — the census against a learning doc — was re-derived eight
  times between 12:18:47 and 12:24:38 for 102,053 output tokens, and reduced
  to a five-line correction.

The same board, measured after: `scan` returns the whole 227-PRD master board
in 7.6 KB and 0.16 seconds.

## Alternatives considered

**Leave the loop and cap the model's thinking budget.** The round ran on
`deepseek-v4-flash:cloud` via a proxy, and its capped thinking is the visible
half of the bill. But the cap is the symptom: the loop asked for a page of
board state that no model should be deriving in prose, and a stronger model
pays the same re-read cost more quietly. The budget cap is a setting on the
session; this is the instrument.

**Have the orchestrator cache the scan in context and re-read nothing.** This
is what it already tried to do, and it is exactly what a compaction destroys.
Anything not on disk is gone at an unpredictable moment, so the answer has to
be on disk.

**Write a full board snapshot to `.round.md` instead of session facts.** It
would go stale the moment a worker moved a box, and a stale snapshot is worse
than none — the round would schedule around a state nothing holds. The split
is deliberate: board state comes from `scan`, every time; only what `scan`
cannot compute is written down.

## Consequences

- `plan.py` gains a `scan` command and is now on the loop's hot path, not just
  the view's. A change to `compute_plan` changes what step 1 reads.
- `prds/.round.md` is machine-local and git-ignored, like `prds/.plan.json`.
  It is one session's memory, not the board's — two sessions on one board
  would fight over it, which is already forbidden by one-orchestrator-per-board.
- It does **not** bound how much a round may think about one decision. The
  loop now says a step is a fixed set of tool calls, but nothing enforces it;
  a model that ignores the sentence will still burn a context window on a
  reconciliation. The enforcement, if it is ever wanted, is a thinking-token
  cap in the session settings.
