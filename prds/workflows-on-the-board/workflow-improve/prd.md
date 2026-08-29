---
state: done
origin: requested
actual: 0.7h
commit: 7e5250f
priority: 50
complexity: 22
blast-radius: mid
repo: pearde
needs:
  - workflow-attach
footprint:
  - references/parts/loop.md
  - references/parts/commits.md
  - references/parts/solo.md
  - references/parts/round.md
  - references/parts/workers.md
  - references/parts/workflows.md
---

# workflow-improve — the run edits the file, so the next run is shorter

When this is done, every collect applies the worker's `### Edits` to the
library, counts the run, and commits the changed workflow files with the PRD.
The library improves because it is used, not because someone maintains it.

## The collect, extended — loop step 6

On a worker whose report carries `## Workflow <slug>`, in the same batch as
the actions step 6 already lists:

1. Read the rows. The PRD's transition is the verdict's, as today — a
   `stopped` row changes nothing about it. Whether the stop was the
   atomic's fault is rule 2's question, answered per edit.
2. Per edit: apply it when the failure was the atomic's — a wrong command, a
   stale path, a check that cannot fail, an unlisted failure shape. Refuse it
   when the failure was the code's or the PRD's, and say which in the round.
3. `runs` +1 on the workflow and on every atomic that ran. `updated:
   <today>` on every file whose text changed.
4. `python3 resources/workflows.py check` before the commit — an edit that
   breaks the format is refused, not repaired.
5. Add the changed files to the PRD's commit. The PRD's own `footprint:`
   does not change — the library is the board's, not the PRD's. A library in
   another repo (`workflows:` pointing there) commits there, same subject —
   the one-commit-per-repo rule in @references/parts/commits.md.

One writer: the orchestrator. Two workers proposing edits to one atomic in
one round is two collects; the second reads the file as the first left it.

## Solo

@references/parts/solo.md step 5: the orchestrator follows the brief itself,
so it follows the workflow itself and writes the edit at the step it failed,
not at a collect.

## Rules

- **From a run, never from reading.** An edit cites the step and the PRD
  that ran it. A reading that finds an atomic "could be clearer" is not an
  edit.
- **Fold, do not log.** The lesson replaces the sentence that was wrong. No
  dated lines in the body; `updated` is the date.
- **An atomic stays one unit.** An edit that adds a second job splits the
  atomic, and the workflow gains a row.
- **A workflow's order may change from a run.** A step that always fails
  until a later one has run is in the wrong place; the report says so, the
  orchestrator moves the row.
- **`runs` is evidence, not a score.** `list` prints it so a reader sees
  which files are exercised and which stand at `0`.

## Files

| file                             | change                                                                                     |
|----------------------------------|---------------------------------------------------------------------------------------------|
| `references/parts/loop.md`       | step 6: the five actions above as one bullet block; step 1: a swept worker's `## Workflow` rows are read with its report |
| `references/parts/commits.md`    | the scope sentence — workflow files a collect edited are added with the rest, named in the message |
| `references/parts/solo.md`       | one line at step 5                                                                          |
| `references/parts/round.md`      | `prds/.round.md` records edits applied and refused this round                               |
| `references/parts/workers.md`    | the on-return table: `## Workflow` present → the five actions                               |
| `references/parts/workflows.md`  | the improve row filled                                                                      |

## Verify

- A dry run on this board: one worker report with two edits, one the
  atomic's fault and one the code's. The collect applies one, refuses one
  and says which, `runs` goes 0 → 1 on the files that ran, `check` is
  silent, and the commit lists the edited file.
