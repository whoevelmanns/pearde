# Archive

`prds/` accumulates every PRD it ever finishes and never sheds one — a
`done` PRD stays a live-looking directory forever, `scan` walks it on every
call, and `doctor`'s census (requested / derived / live) only ever grows.
Nothing here changes what `state: done` means; it moves the file once the
work it describes stops being current, using the same trick the board
already uses to hide `memos/` and `workflows/` from itself.

```
prds/archive/
    <name>.md             a former top-level PRD, flattened
    <parent>--<child>.md  a former child PRD, flattened, parent-prefixed
```

- One flat directory, no nesting — the same shape as `prds/memos/`
  (@references/memo.md).
- A file here is `prd.md`'s frontmatter, title and body, unchanged, just
  renamed and moved. Nothing new is required in it — no `archived_at:`, no
  new frontmatter key — because nothing ever reads this directory back.

## Why scan already ignores it

`_scan_one` (@resources/board/plan.py) finds a PRD by one test: `"prd.md" in
files`. `prds/memos/` and `prds/workflows/` are already invisible to `scan`
for the same reason `references/parts/board.md` gives — they hold no file
literally named `prd.md`. `prds/archive/` needs no line added to `scan`'s
`dirs[:] = [d for d in dirs if d not in ("specs",)]` prune, because it is
never a directory *of* PRDs, only a directory *of* their remains: every file
in it is `<name>.md`, never `prd.md`. That is also why the shape has to be a
flat file and not a moved *directory* — `prds/archive/<name>/prd.md` still
matches the same test, and the walk (and the count) go right on including it.

The consequence: nothing under `prds/archive/` is counted in the progress
line, offered to `claim`, or walked by `doctor`'s PRD census. Moving 20 done
PRDs there is 20 fewer directories `scan` opens on every round.

## What's eligible

`state: done` only, once its own commit has landed and nothing live still
needs it (see below). A `superseded` PRD (`probe-code-lives-in-the-prd-folder`,
`snapshots-fold-to-one-row`) is written to keep its evidence readable at the
top level on purpose — archive one only once whoever wrote it judges the
evidence no longer needs that visibility; the state alone isn't the
signal.

Never archive a parked state (`deferred`, or any other spelling
@references/parts/states.md calls "the user's own"). Parked is not
finished — `release <prd> open` exists precisely to bring one back
(`a-parked-prd-comes-back`), and archiving one would move the very file that
path reads.

Check first: `grep -rl '<name>' prds/*/prd.md prds/*/*/prd.md` for a
`needs:` or `footprint:` still naming it. This should rarely fire —
`dispatchable` already requires every `needs:` to be `done`
(@references/parts/states.md) — but a stale mention would go dangling
silently otherwise.

## Moving one

A leaf, done PRD:

```
git mv prds/<name>/prd.md prds/archive/<name>.md
git rm -r prds/<name>
```

`specs/` goes with it. A done PRD's specs are already history `scan` never
reads back (`resources/board/plan.py`, "boxes for live PRDs only"); the whole
tree survives forever at `git log --follow -- prds/<name>` up to the `git
rm` — the same tool `plan.py` already reaches for when a done PRD's history
(its `done_at`) is wanted but not worth a stat-cheap read on every rebuild.

A container whose children are all `done` (already `collect`ed): archive
bottom-up so `prds/archive/` never collides on a bare child name:

```
git mv prds/<parent>/<child>/prd.md prds/archive/<parent>--<child>.md
git rm -r prds/<parent>/<child>
# … repeat per child, then the parent itself:
git mv prds/<parent>/prd.md prds/archive/<parent>.md
git rm -r prds/<parent>
```

## When

By hand, when the board feels heavy — alongside a `doctor` pass, not on
every `collect`. A PRD that just landed is still the thing a fresh commit
message points at; give it a few days of top-level visibility before moving
it. No new command exists for this yet — two `git` calls is the whole
mechanism, and the smallest thing that could be true of a repo already this
prose-driven.

## Finding one again

`grep -l <name> prds/archive/*.md`, or `git log --follow -- prds/<name>` for
everything before the move.

## Rejected

- **A `pearde archive` command.** The board's existing idiom for a directory
  `scan` ignores is a naming trick, not an entry added to `plan.py`'s prune
  list — `memos/` and `workflows/` prove it out. Script the two `git` calls
  above once running them by hand gets old; don't teach `scan` a new
  directory name to skip.
- **Moving the whole directory, `prd.md` and all.** Still matches `"prd.md"
  in files` — `scan` keeps walking it, `doctor`'s count doesn't move, and
  the report's actual complaint (the walk cost) is unfixed.
- **A tenth `state:` meaning, e.g. `state: archived`.** Still a live
  directory under `prds/` either way — the walk cost this document exists to
  cut is the size of `prds/`, not the spelling of `state:`.
- **Deleting done PRDs.** Out of scope by instruction, and against the
  board's own practice — `superseded` PRDs are kept specifically for their
  evidence, not as clutter.
