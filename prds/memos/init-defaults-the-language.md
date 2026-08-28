---
memo: init-defaults-the-language
kind: decision
status: decided
subject: A board is created with no question — language defaults to English and says so on the first line
date: 2026-08-28
prds:
  - the-board-runs-itself/init-asks-nothing
---

# init-defaults-the-language — one question is the whole of first-run friction

## Decision

`pearde init` writes `language: English` unless `--language` says otherwise,
prints `language English — pearde settings language=<l> changes it` as its
first line, and asks nothing. The first round's progress line names the
language it writes in. The sentence "stated by the user, never guessed" in
@references/settings.md and @references/parts/loop.md is replaced by this.

## Why

The first run today is three acts — `doctor --fix`, copy a settings block,
answer one question — and the question is the only one of the three a tool
cannot do. It is also the only thing standing between "I cloned this" and "I
have a board". A default that is printed is not a guess: the reader sees it
on the line that made the board, and changing it is one key.

The rule it replaces was written for a board whose language the model would
otherwise infer from the conversation, and infer wrong. A default is not an
inference. English is the language every reference in this repo is written
in and the one every worker brief is rendered from, so a board that never
changes the key gets documents in the language its tooling speaks.

## Alternatives considered

**Ask, as today.** One question, once per board. It lost because it is the
one step of `init` that cannot be idempotent, cannot be scripted, and cannot
be run from a quickstart — and because a board registered by hand with no
`settings.md` (`racer/.mi/prds` is one, watched today) has nobody to ask.

**Infer from the locale.** `LANG=de_DE` writes `language: German`. It lost
because the locale is the machine's, not the board's, and a German developer
writing an English codebase gets German specs on an English tree — the guess
the old rule was written against, made by a tool instead of a model.

**Change the default and write no key.** @references/settings.md already says
a missing key reads at its default; make that default English and `init`
need not write `language:` at all. Taken for the default — a board with no
key now reads English rather than "none — asked" — and rejected for `init`:
the key is written anyway, so the choice is on disk where a reader sees it
and where `pearde settings language=…` has a line to replace.

## Consequences

- A board created by `init` and never touched writes English. A user who
  wanted otherwise sees the line and sets the key; the cost is one command
  after the first, not one question before it.
- `doctor`'s `board` row no longer reports "no `language`" as broken —
  `doctor.sh:200-203` does today, and `init-asks-nothing` carries that edit
  in its Files table; a hand-made board without the key reads English by
  the default above.
- It does not decide the language of a member board on a master — that stays
  the member's own `settings.md`, per @references/parts/master.md.
