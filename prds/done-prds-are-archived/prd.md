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

When this is done: a `done` PRD older than a configurable threshold moves out
of the working tree into `prds/.archive/`, swept by a separate command that
runs automatically once per round. `scan` reads only the active tree — counts,
sections and the progress line never include an archived PRD. History is
intact through git; nothing is deleted.

A new **archive** tab in the view (@references/parts/view.md) lists every
archived PRD — name, when it archived, when it was `done`. Picking one moves
its directory back to the working tree after a confirmation step, the same
flow `retry` uses when it reaches into the archive.

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
- The archive tab lists, never edits — the only write it triggers is the move
  back, behind the same confirmation Q4 decided. No other field is editable
  from that tab.
- `⌘1–6` and the six existing views (@references/parts/view.md) are
  unchanged; the archive tab is a seventh, added to the same switcher.

## Pointers

- `@resources/board/plan.py` — reads every `prd.md` under `prds/`, walks the
  tree, prints `scan`.
- `@references/parts/states.md` — what `done` means and what it triggers.
- `@references/parts/commits.md` — what a transition's commit carries.
- `@references/parts/order.md` — how `plan` and the view order PRDs; an
  archived PRD must not appear on the timeline.
- `@references/parts/view.md` — the six views and the `⌘1–6` switcher the
  archive tab joins; the seams/replace mechanism, if the tab is built as one.

## Questions

### Q1: Where does an archived PRD live?

Once moved out of the working tree, where does its directory land?

1. **Same tree, hidden prefix** — `prds/.archive/<same relative path>`, in
   this repo, on the same branch. Structure is unchanged, only the prefix
   moves. (recommended)
2. **Deleted from the working tree, kept only in git history** — no archive
   directory at all; a `done` PRD's files stop existing on disk and are
   reached only through `git log` / `git show`.
3. **A separate branch** — `done` PRDs move to e.g. an `archive` branch, main
   stays PRD-free of finished work entirely.

### Q2: What triggers the move?

1. **Automatic, same commit as `done`** — `collect` (loop step 6) moves the
   directory and commits it in the same act that sets `done`. (recommended)
2. **A separate sweep command** — `done` PRDs sit in the working tree until a
   new handle (e.g. `archive`) is run, manually or as a periodic step.
3. **Automatic, but one round later** — `done` this round, moved on the next
   round's step 1, so a freshly `done` PRD is still visible for one round
   before it disappears.

### Q3: Do the `done` PRDs already on disk get archived now, or only future ones?

52 PRDs on Chordino's board and 7 on pearde's own are already `done` and
sitting in the working tree today.

1. **Backfill now** — this PRD's implementation also moves every existing
   `done` PRD into the archive, so the board is clean the moment it ships.
   (recommended)
2. **Forward-only** — only PRDs that transition to `done` after this ships
   get archived; the ones already `done` stay where they are, permanently,
   unless someone moves them by hand.
3. **Forward-only, with a one-time sweep offered separately** — same as
   forward-only, but this PRD also adds a `sweep-archive` handle a person can
   run later to backfill on their own schedule.

### Q4: How does `retry <prd>` reach a PRD once it has moved to the archive?

1. **`retry` searches the archive when the name is not in the working tree**,
   and moves the match back automatically before reopening it. (recommended)
2. **The user moves it back first** — `retry` is unchanged, and archiving is
   invisible to it; a person `git mv`s the directory back before typing
   `retry`.
3. **Archived PRDs are never retried** — a regression against `done` work
   files as a new PRD instead of reopening the old one; `retry` only ever
   sees the working tree.

## Answers

**Q1** — Same tree, hidden prefix: `prds/.archive/<same relative path>`, in
this repo, on the same branch. Structure is unchanged, only the prefix moves.

**Q2** — A separate sweep command. `done` PRDs sit in the working tree until
the sweep runs — not on the same commit as `done`.

**Q3** — The sweep moves every `done` PRD older than a configurable age
threshold, default one week. The threshold is a setting (e.g. `archive-after:`
in `prds/settings.md`); set to `0` it disables automatic archiving entirely.
This age rule covers both the backfill and the forward case with one
mechanism: a `done` PRD already a week old the first time the sweep runs is
swept then, and a freshly `done` one is swept once it crosses the same age.
The sweep itself runs automatically — once per round, as loop step 1 already
sweeps dead-session leftovers — not as a command the user types each time.

**Q4** — Like Q1's recommended answer — `retry` searches the archive when the
name is not in the working tree — but with a confirmation step first: the
match and what moving it back entails are shown before the directory actually
moves and the PRD reopens.
