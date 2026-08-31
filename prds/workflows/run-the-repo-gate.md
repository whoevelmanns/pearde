---
atomic: run-the-repo-gate
subject: run the map check and the install check, and account for every line
date: 2026-08-28
updated: 2026-08-29
runs: 22
---

# run-the-repo-gate — the two commands that read the whole tree

## Do

1. `python3 resources/index.py check`. Silent is clean. Every line it prints
   is a file on disk with no row in `references/files.md`, or a row naming
   nothing.
2. `bash resources/doctor.sh`. Read every row. `off` is a part that is absent,
   `broken` is a part that is present and wrong — only the second is yours.
3. Compare both against what you recorded before the first edit. A line that
   was there before is not yours to clear; a line that is new is.

## Done when

- `python3 resources/index.py check` prints nothing it did not print at
  baseline.
- `bash resources/doctor.sh` shows no `broken` row that was not `broken` at
  baseline.
- Every line still printed is quoted in the report with the word "pre-existing"
  or a fix beside it.

## Fails when

| seen | means | do |
|------|-------|----|
| a row that was `broken` at step 2 is `ok` at step 6, and the file that cleared it is in your `footprint:` | your change closed a pre-existing failure — the gate's **exit code** moved with it, from 1 to 0 | quote both rows and both exit codes, name the hunk that cleared it, and re-run any check of yours that compares exit codes against this board: a box reading "the exit code is the one the same board gives with the row off" was measured against the old 1 and must be re-taken against the new 0 |
| `doctor` at step 4 prints a row that was not there at step 2, and it is `off`, not `broken` | a sibling's `resources/doctor.sh` added a part between the two runs — `off` is absent, not wrong | `git diff --stat resources/doctor.sh` and its mtime against your baseline time; quote the row as inherited and do not clear it |
