---
memo: the-guard-enforces-the-loop
kind: decision
status: decided
subject: The loop's three token rules are a PreToolUse hook, not three sentences
date: 2026-08-27
---

# the-guard-enforces-the-loop — a rule a model can ignore is not a rule

## Decision

@resources/guard.py runs as a `PreToolUse` hook on `Bash|Read` and a
`PostToolUse` hook on `Edit|Write`, in the settings file of the repo the board
lives in, with `MAX_THINKING_TOKENS` set beside it. It refuses three calls: a
board walked by hand, a board-reading command repeated while nothing on the
board changed, and a third read of a file unchanged since the first. It
comments on two more: the first spec read (the boxes are already counted) and a
`prd.md` written while `prds/.round.md` is older than it.

It is optional — the loop runs without it — and `doctor` reports it as `ok`,
`off` or `broken`. @references/parts/guard.md is the block and the reasoning.

## Why

[[the-scan-is-one-call]] moved the three mechanisms out of the loop's text and
into `plan.py scan` and `prds/.round.md`, and left one thing unfixed, in its
own words: *nothing enforces the standing rule. A model that ignores the
sentence can still spend a context window on one reconciliation.* That is not
a hypothetical — the round being fixed had the sentences available and
produced 160,000 tokens of capped thinking anyway.

The guard closes it where it can be closed provably. "Nothing changed" is the
newest mtime of any `.md` under the board and its members: 7 ms on the 227-PRD
master board, and an unchanged stamp means the repeated command returns the
bytes the round already has. That is what makes a refusal safe rather than a
guess — a board that moved lets the same command straight through, and
`plan.py` itself is never refused, because a round recovering from a
compaction has to be able to ask again.

`MAX_THINKING_TOKENS=8000` is the other half, and the half the guard cannot
reach: five responses in that session each hit a 32,000-token output ceiling
inside a thinking block and emitted nothing at all. No *productive* thinking
block in the session exceeded 7,073 tokens.

## Alternatives considered

**Leave it as prose and rely on a better model.** The measured failure is a
model ignoring three available sentences. A stronger model ignores them less
often, which is not the same as a bound, and the orchestrator's model is a
session setting that anyone can change to a weak one — as happened here.

**Deny spec reads outright.** It would have killed the largest single waste
(44 KB of specs read three to four times) but hooks fire for subagents too,
and an implementer that cannot read its own spec cannot work. The third-read
rule bounds the same waste without ever standing between a worker and its
contract.

**Have `doctor --fix` write the hooks block.** Rejected for the same reason
doctor does not wire a status line: a settings file is the reader's, and this
one decides what their tools are allowed to refuse. Doctor reports it and
prints the file it looked in.

**A `Stop` hook that audits the round after the fact.** It would catch the
waste only once it was paid for. The value of a `PreToolUse` refusal is that
the tokens are never spent.

## Consequences

- Hooks fire for subagents as well as the orchestrator, so an analyst that
  reads one spec three times in an unchanged tree gets the same refusal. That
  is intended, and it is why the limit is three rather than two.
- The guard holds one JSON file per session under
  `resources/board/state/guard/` — machine-local, like everything else there.
- A false refusal is possible if the stamp is wrong (a board edited by a
  process that preserves mtimes). The stamp is one function; the round should
  say so rather than work around it.
- It does **not** bound a single long deliberation that makes no tool calls at
  all. `MAX_THINKING_TOKENS` is what bounds that, and it is a setting the user
  owns, not something this repo can install.
