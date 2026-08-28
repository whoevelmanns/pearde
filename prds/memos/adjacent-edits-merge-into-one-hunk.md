---
memo: adjacent-edits-merge-into-one-hunk
kind: decision
status: open
subject: Two workers editing adjacent lines produce one `-U0` hunk, and `collect` cannot tell whose it is
date: 2026-08-28
prds:
  - the-board-runs-itself/collect-is-a-command
  - the-board-runs-itself/hunks-land-where-they-came-from
---

# adjacent-edits-merge-into-one-hunk — a hunk with two authors has no baseline to match

## Decision

Open. Recorded here rather than as a PRD: it was found by the analyst of a
derived PRD, and @references/parts/derived.md folds a derived finding on a
derived PRD into the first rather than filing a third.

## Why

`collect`'s step 3 classifies a hunk as inherited when its body was in the
claim's baseline and as the worker's otherwise. `git diff -U0` merges changes
on adjacent lines into one hunk. When a foreign edit and the worker's touch
adjacent lines, the merged hunk's body is in neither baseline, `new_hunks`
returns `all`, and the whole file — foreign lines included — is committed as
the worker's. Reproduced by the `hunks-land-where-they-came-from` analyst on
its first fixture (both edits appended at EOF), 2026-08-28.

## Alternatives considered

**Diff with context (`-U1`) and split by content.** Adjacent changes still
merge; the split would have to know which lines are whose, which is the
baseline's job.

**Match the baseline line by line, not hunk by hunk.** Every `+` line of a
merged hunk that appears in the baseline's diff is inherited; the rest is the
worker's. Sound where the two authors' lines do not interleave; the case where
they do is the one no diff can settle and the worker must say so.

**Refuse the file.** A hunk whose body matches neither the baseline nor the
claim-time working file is refused with `two authors on one hunk`, and the
worker widens with `--widen` or leaves one untouched line between the edits.
The cheapest honest answer; it costs a refusal where today a wrong commit
lands silently.

## Consequences

- Until settled, a worker told to keep its edits disjoint from a sibling's is
  told to leave one untouched line between them — the library row
  `attempt-the-build` now carries it.
- Whoever takes this decides between line-level matching and refusal; the
  third road is not on the table.
