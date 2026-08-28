---
memo: the-tool-moves-the-states
kind: decision
status: decided
subject: Every transition is a command that checks its own gate, and the prose becomes the spec of the tool
date: 2026-08-28
prds:
  - the-board-runs-itself
  - the-board-runs-itself/transitions-are-commands
  - the-board-runs-itself/collect-is-a-command
  - the-board-runs-itself/the-loop-is-commands
---

# the-tool-moves-the-states — a rule the model can skip is not a gate

## Decision

Every write of a PRD's state goes through `pearde <transition>` — `claim`,
`release`, `answer`, `specced`, `refine`, `collect`, `set` — and each command
checks the gate @references/parts/states.md names before it writes. The
orchestrator decides what to do; the tool does it, prints the progress line,
and refuses what the table forbids. The sentences in `references/parts/` that
stated those gates are deleted as each command lands, and the parts become the
spec of the commands. The guard refuses a `state:` written by hand.

## Why

The 2026-08-27 measurement in `report.md` — 318,584 output tokens in one round
— was two things at once: a proxy model whose thinking hit a 32,000-token
output cap five times and emitted nothing, and a model with every rule on disk
and in context, ignoring them for the rest. `MAX_THINKING_TOKENS` bounds the
first; `the-scan-is-one-call` and `the-guard-enforces-the-loop` fixed the
reading half of the second: the board is read by one call and a redundant
read is refused. The writing half is untouched: a collect
is still ~12 hand edits with the gate a sentence the model is trusted to have
read, a split is still a model making directories, and `complexity` is still a
number the model sums. Each of those is a place the rule can be skipped, and
each was skipped at least once on this board — `finished-counts-both-files`
exists because the code and the prose disagreed on what finished meant, and
the round file of 2026-08-28 records a `runs` rule shipped at four sites with
different wording.

A command cannot be skipped. It has one gate, in one function, tested against
one example board, and it prints the same line every time. The prose then has
one job left — say what the command does, for the reader who has to change it.

## Alternatives considered

**A better model reading better prose.** `report.md` itself recommends it —
the same work finished in 17,982 tokens after the model switch — and it is
right about the capped thinking. It is not a bound on the hand edits: the
session model is a setting anyone can lower, and a stronger model ignores a
sentence less often. The prose was already good; it was read and not followed.

**A `PreToolUse` hook that checks the gate at the write.** The mechanism the
reading half used, one function, no new surface. It is taken — `the-loop-is-
commands` adds the matcher that refuses a hand-written `state:` — but as the
backstop, not the path: a hook can refuse an edit, and it cannot sum a
complexity, compute a footprint union, or write a commit. The commands do the
work; the hook makes going around them cost a `--force`.

**The daemon's `POST /edit` as the one write API.** `serve.py` already
validates the board and the PRD and writes through `edit.py`. Rejected because
the board has to run with no daemon — `plan.py` plans without it — and because
the view's writes are a person's and are not gated; the commands call the same
function the daemon calls, with the daemon passing `force`.

**A `Stop` hook that audits the board after the round.** It catches the wrong
state after the tokens were spent and the commit landed. A gate at the write
is the cheapest place to refuse, and the only place a refusal costs nothing.

**A workflow engine or an external tracker.** Plane was tried and removed —
`view — the board is its own board now, and Plane is gone` — because the
files stopped being the truth. The commands here write the same files the
model wrote, through `edit.py`, one line at a time. Nothing runs a step for a
worker, and a board with no tool is still a board.

## Consequences

- `references/parts/loop.md` shrinks to the calls and the judgement between
  them. Every rule a command enforces is deleted from the prose in the commit
  that lands the command — two statements of one rule is the drift this board
  has already paid for twice.
- The orchestrator loses a freedom: a transition the table forbids needs
  `--force`, and `--force` says so on the line.
- The view and the commands share one code path, so a drag in the kanban and
  a `pearde set` refuse the same things.
- A command cannot tell who called it. A worker's shell passes every gate a
  command has, so "never edit frontmatter, never run a transition" stays a
  sentence in the brief — the hooks fire for subagents and the matcher
  refuses the hand edit, but a worker that runs `pearde set` is not refused.
  One writer is a mechanism for the hand edit and a rule for the command.
- `transitions.py` must be in the daemon's `SOURCES`, or the page keeps the
  old gate after an edit and a drag and a command diverge.
- It does **not** decide who wears which persona, whether a worker's report is
  believed, or whether a workflow edit was the atomic's fault. Those stay the
  orchestrator's, and `the-loop-is-commands` writes them down as the
  right-hand column of the round.
