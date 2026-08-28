---
state: open
origin: derived
from: workflows-on-the-board
priority: 40
complexity: 0
blast-radius:
repo: pearde
footprint:
  - resources/index.py
  - references/files.md
---

# snapshots-fold-to-one-row — a manifest row may name a directory

When this is done, `python3 resources/index.py check` is silent on a tree
where a scout sweep has just written a new snapshot, and it went silent
because the manifest names the directory once — not because somebody added a
row.

The decision and the roads it beat are in
`prds/memos/a-manifest-row-can-name-a-directory.md`. This PRD only builds it.

## The consequence, named

Every PRD on this board inherits `prds/settings.md` § Deliverable, which makes
`resources/index.py check` green part of `done`. A snapshot with no row makes
that check red for reasons no PRD owns, so each transition has to decide by
hand that this particular red is not its own. `workflows-on-the-board/workflow-format`
and `workflows-on-the-board/workflow-reader` both had to narrow their
acceptance checks from "the check is silent" to greps over their own
footprint, and write a paragraph each explaining why. That is the requested
work this gets wrong: the next PRD does the same reasoning again, and the one
after that is the one that gets it wrong.

## Files

| file                     | change                                                                                                  |
|--------------------------|-----------------------------------------------------------------------------------------------------------|
| `resources/index.py`     | `check()`'s `disk - listed` and `listed - disk` both understand a row whose anchor ends in `/`: it covers every path beneath it. A directory row that names nothing on disk is still reported — the row is a claim about the tree, and an empty claim is the same defect in the other direction |
| `references/files.md`    | `@resources/scout/snapshots/2026-08-25.tsv` becomes `@resources/scout/snapshots/`, one row, described as the sweep's dated star counts |

## Rules

- **A directory row is for data the tools write, never for source.** The row
  buys a green gate by giving up per-file review, which is a trade only worth
  making where no human decides what lands.
- The trailing `/` is the whole of the syntax. No glob, no pattern, no second
  key — a manifest that needs a matcher has stopped being a list.

## Verify

- `python3 resources/index.py check` is silent on this tree, with both
  snapshots on disk and one row naming the directory.
- **The check still fails when it should**: `touch resources/scout/nope.tsv`
  outside the covered directory prints its line; a row naming
  `@resources/nosuchdir/` prints a line for the directory that is not there.
  Remove both afterwards.
- `bash resources/doctor.sh` reports `index ok`.
