---
memo: the-install-is-live-symlinks
kind: note
status: decided
subject: The installed skill is file-by-file symlinks into this repo, so a pearde round on any board on the machine edits this working tree
date: 2026-08-29
prds:
  - the-tool-keeps-its-word
---

# the-install-is-live-symlinks — there was never a third writer on this board

## Decision

Recorded, not changed: `install.sh --apply` builds links, and
`readlink ~/.claude/max/skills/pearde/README.md` resolves into this repo. A
session working any other board — `dotfiles`, the master, a repo that only
runs `pearde scan` — that corrects a sentence in the skill writes here, in a
working tree the sessions on this board are staging by hunk. Two days of
signatures attributed to "a third writer" (row moves in `settings.md` and
`files.md`, a `.gitignore` dedup, the `asked`→`done` rename across six files)
were this, and the rename's author was a `dotfiles` session that ended
before committing. Counted on 2026-08-29 from the `Claude-Session:` trailers
of every commit since 2026-08-27: **seven sessions** wrote this repo — two
that talked to each other (16 and 4 commits), the master board's (1), and
four one-commit strangers, one of which filed a whole PRD tree
(`the-board-asks-for-itself`, 7a6f6f9) that both sessions on this board
assumed the other had written.

## Why

@references/install.md chose links over copies so that editing this repo
updates every install at once — one source of truth. The same property runs
the other way: every install is a door into this repo's working tree, and no
footprint negotiated between two sessions here can see a third that never
joined it. `doctor` and every harness on this board measure a tree that a
session on another board can move under them mid-run; the `## Fails when`
rows about counts moving on paths a worker never wrote are all right, and the
mechanism is wider than "another session on this board".

## Alternatives considered

**Copies at install.** Rejected in @references/install.md — a copy drifts and
nothing says it happened. It would isolate the tree at the price the design
refused.

**A skill session refuses to edit under `resources/` or `references/` unless
the board it works is this repo's.** A guard row — `guard.py` already sees
every Edit/Write and knows the board's root — that denies a write into the
skill tree from a round on another board, naming this memo. The cheapest
honest fix; it keeps the links and closes the door.

**Live with it and name it.** What this memo does today.

## Consequences

- A `pearde` round elsewhere that wants a skill change files a PRD on
  **this** board, or hands the edit to a session working it — the rule
  `commits.md` already applies to another repo's library.
- Until a guard row exists, `git status` here is not evidence of what the
  sessions on this board did; the `Claude-Session:` trailer on a commit is,
  and an uncommitted change is nobody's until claimed.
