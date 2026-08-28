---
atomic: re-run-the-harnesses
subject: re-run the recorded harnesses and account for every changed count
date: 2026-08-28
runs: 1
---

# re-run-the-harnesses — every number back, or explained

## Do

1. Re-run every harness whose count you recorded, in the same order, with the
   same command line.
2. Compare each count to the recorded one. A count that dropped is yours until
   you have shown otherwise.
3. When a harness fails on a line you edited, read what it matches before you
   touch the harness. A matcher written against a markdown table row often
   matched that row's column padding, so re-aligning a table breaks it while
   the rule it asserts is intact — repair the matcher to read the cell's text,
   never the spacing, and say in the report that the rule did not move.
4. Quote the final line of each harness in the report, next to its baseline.

## Done when

- Every recorded harness prints a count greater than or equal to its baseline.
- Every count that changed has one sentence saying what moved it.
- No harness was edited without the report saying which matcher changed and
  why the rule it asserts is unchanged.

## Fails when

| seen | means | do |
|------|-------|----|
