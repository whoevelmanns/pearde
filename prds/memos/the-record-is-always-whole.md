---
memo: the-record-is-always-whole
kind: decision
status: open
subject: collect must never stage a PRD's own folder by hunk, and the state it writes after staging must land in the same commit
date: 2026-08-29
prds:
  - the-board-runs-itself/collect-is-a-command
  - the-board-runs-itself/hunks-land-where-they-came-from
---

# the-record-is-always-whole — a `done` PRD whose committed record says `analyzing`

## Decision

Open. Two rules proposed by the master-board session after a collect on
2026-08-28 (mitosys `97f13b01`, committed `34bcb4f5` by hand afterwards):

1. The by-hunk path never applies under the PRD's own folder. The board's
   record — `prd.md`, its specs — is committed whole, always.
2. What `collect` writes after staging — `state: done`, `complexity`,
   `actual`, `commit`, the posted `## Report` — lands in the same commit,
   not as a rider on the next one.

## Why

The claim-time baseline snapshot held the analyst's `prd.md` body; the
implementer's three ticked boxes were the only new hunks; `collect` staged
the file "by hunk" and committed the boxes under `state: analyzing`, then
wrote `state: done`, `commit:`, `actual:` and the report to the working tree
after the commit. Nothing misplaced, gates green — and a `done` PRD whose
HEAD record says `analyzing` until the next collect carries it. The
`commit:` key cannot name the commit it is in, which is why the rider exists;
everything else in that list can, and the record is not a source file with
two authors — it is the board's, and the board has one writer.

## Alternatives considered

**Keep the riders, document them.** Cheapest; leaves every `done` PRD one
commit behind its own state in history, which is what `retry` and a reader of
`git log -- prds/<prd>` then have to know.

**Write the state before the commit and amend `commit:` in.** `commit:` is
the one key that must follow; a second, tiny commit for it alone (`prd:
<path> — record`) keeps history honest and the rider list empty.

## Consequences

- Until settled, a master-board collect commits the PRD's `prd.md` whole by
  hand afterwards, as that session did.
- The fix is in `collect.py`'s step 3 (the folder rule) and steps 4–5 (the
  order); `hunks-land-where-they-came-from`'s placement check is unaffected.
