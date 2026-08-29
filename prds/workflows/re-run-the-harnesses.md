---
atomic: re-run-the-harnesses
subject: re-run the recorded harnesses and account for every changed count
date: 2026-08-28
updated: 2026-08-29
runs: 44
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
| a count went **up** on a harness you did not touch | every row here reads a count that dropped; a count that rose is the same evidence that the tree moved under you, and a worker that only checks for drops will quietly take credit for a neighbour's landing | quote both counts, say the rise is not yours and name the file whose change explains it — a harness whose baseline you recorded red and that is now green is a finding about the other session, not about your unit |
| `find prds -name verify.sh` lists a harness that was not there at step 2 | a parallel session landed a PRD mid-run, with its own probe | run it, record it as new with no baseline, and do not compare it to anything; a harness you never had a baseline for cannot regress |
| a count moved on a harness whose inputs you did not touch | the harness's own text changed between the two runs | quote both counts, say the text moved and whose it is; it is not yours to explain |
| a count moved on a path you never wrote | another live session landed files under `resources/` mid-run | name the paths and say they are not yours; the baseline stands for your own paths |
| a count dropped on a harness whose failing line is a repo-root `git status` or `git diff` | the check measures the workspace, not this PRD's footprint; a parallel worker's untracked file reddens it | quote the line, list the untracked files it saw and whose they are, leave the harness alone — the rule did not move |
| `index.py check` or `doctor` prints a line naming a file you did not touch | another session moved the tree under you | `git diff <file>` proves whose it is; report it with the path, do not fix it |
| a committed harness outside your footprint goes red on a count the contract itself moves | the matcher is honest and the file is not yours | leave it red, quote it beside its baseline, and put the file in the spec's `footprint:` with the one-line matcher change as that spec's work |
| a count dropped, and every failing line names a file outside your footprint that `git status` shows a live sibling modified after your baseline | the neighbour moved, not your unit | quote the failing lines, the file, and its mtime against your baseline time; report it as a finding and do not back-edge — there is nothing in your footprint that closes it |
| a needle fails on a sentence you kept | the sentence was re-wrapped across a line; the needle is one line | re-wrap so the sentence reads whole on one line and say the rule did not move |
| a needle names a sentence the contract deleted | the rule now lives in a command | quote the needle, name the command and its line, propose the harness edit — the count is a finding, not yours to repair |
| a harness has no `cd` and one line runs a transition with no `--board` | it acts on whatever board is above the caller's cwd — the real one, from the repo root | run it from the scratch dir, where `find_board` refuses and the line fails without writing; quote the count and name the line |
| a state file in `resources/board/state/guard/` you were told not to write moves its mtime during the re-run | a harness in the set calls `doctor.sh` with no `PEARDE_GUARD_STATE`, and `doctor.sh`'s own guard probe carries no session | name the harness by `grep -c doctor.sh` and `grep -c PEARDE_GUARD_STATE`, compare the file's mtime to your start, remove it only if it did not exist before you, and report the writer's line |
| doctor's `view` row is `off` after the run and `serve.py status` says not running | a harness in the set runs `serve.py stop` with no port and reaches the live daemon | name the harness line, do not restart it yourself — the coordinator owns the service |
