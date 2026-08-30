---
state: open        # open|analyzing|refine|question|specced|claimed|blocked|done|failed
origin: requested  # requested = the user asked | derived = the board found it
priority: 0        # higher first
complexity: 0      # analyst, at spec time — 1-100. THE WEIGHT the board schedules by
blast-radius:      # analyst, at spec time — high|mid|low. What breaks if this is wrong
repo: pearde
---

# `done` PRDs move to an archive, and `scan` stops reading them

A board with years of `done` PRDs mixed into `prds/` keeps `scan` reading
every one of them on every round, and a person opening the tree wades through
finished work to find what is live.

When this is done: a `done` PRD moves out of the working tree into an archive
location, on the same commit that sets it `done`. `scan` reads only the
active tree — counts, sections and the progress line never include an
archived PRD. History is intact through git; nothing is deleted.

## Constraints — what must NOT change

- No PRD content is lost. Archiving is a move, never a delete.
- The `done` gate itself (@references/parts/states.md) is unchanged. Only
  where the file lands after `done` changes.
- `collect` (loop step 6, @references/parts/loop.md) still sets `done` and
  still commits — archiving rides the same commit, it does not replace it.
- A `done` PRD another PRD's `needs:` still names must resolve — an archived
  PRD is not a gone PRD.
- `retry` on an archived PRD (@references/parts/handles.md) must still work:
  moving it back to the working tree and reopening it.

## Pointers

- `@resources/board/plan.py` — reads every `prd.md` under `prds/`, walks the
  tree, prints `scan`.
- `@references/parts/states.md` — what `done` means and what it triggers.
- `@references/parts/commits.md` — what a transition's commit carries.
- `@references/parts/order.md` — how `plan` and the view order PRDs; an
  archived PRD must not appear on the timeline.
