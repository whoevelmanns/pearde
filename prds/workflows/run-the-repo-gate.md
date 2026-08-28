---
atomic: run-the-repo-gate
subject: run the map check and the install check, and account for every line
date: 2026-08-28
runs: 13
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
