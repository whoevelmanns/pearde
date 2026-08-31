---
atomic: run-the-scoped-verify
subject: run the unit's own verify command and quote what it printed
date: 2026-08-28
updated: 2026-08-29
runs: 22
---

# run-the-scoped-verify — the unit measured, not the tree

## Do

1. Run every command in the spec's `## Verify and Proof` block, verbatim and
   in order. Do not substitute a broader one. There is no `verify:` key — the
   block in the body is the command set.
2. Read the block before running it: every command in it must name a path from
   this spec's `footprint:`. A command over the whole workspace measures the
   tree's worst neighbour and is a finding, not a gate.
3. Copy its output into the report. A count, an exit code or a file — never
   the word "passes" on its own.
4. Tick the spec's acceptance box for a check you actually ran, at the moment
   you close it. Which boxes exist and what a tick means are
   @references/parts/workers.md.

## Done when

- Every command in the block exited 0, or a non-zero exit is quoted with the
  reason it is the correct result, and the output is quoted in the report.
- Every command names at least one path from the spec's `footprint:`.
- Every ticked box has output beside it that a reader can re-run.

## Fails when

| seen | means | do |
|------|-------|----|
| a `git status --porcelain <dir>` line in the block prints `?? <dir>/` on a tree you did not write into | the directory itself is untracked, so porcelain reports the whole dir rather than your edits | quote it beside `find <dir> -newer <your newest file> \| wc -l` (0 = untouched), report the spec's line as a finding, and do not tick on the porcelain line alone |
| a check asserts a checker is silent over the whole fixture board, and the fixture holds a case the checker refuses on purpose | the check measures the fixture's worst neighbour, not the unit | filter the checker's output to the unit's own lines, and quote the refused neighbour's line as the proof it still refuses |
| a line in the block writes state or commits on the board it is run from | the spec measures a transition on the live board | run that line on a copy — `python3 resources/board/plan.py example <tmpdir>` — quote it, and report the spec's line as a finding |
| a `grep -c` line in the block exits 1 while printing `0` | zero matches is the result the box wants, and grep's exit says "nothing found" | quote the count and the exit together; the box is closed on the count |
| the block prints a small integer under a label that reads as a count | the line echoes `${PIPESTATUS[n]}` — an exit status; grep's is 1 on zero matches | quote the command's own output beside the number and read the number as an exit status; report the spec's line as a finding |
| the block writes a settings key with `>>` and the reader never sees it | `settings.md` is a frontmatter fence plus a body, and `board_settings` reads only the fence — an appended line is body text | insert the key inside the fence, quote both results, and report the spec's fixture line as a finding |
| a `--check <snapshot before this PRD>` box, and no snapshot was handed over | a snapshot built from `HEAD` predates every uncommitted hunk in the tree, not only this PRD's | take it from `git archive HEAD resources`, name the first differing token per view, and report the box as unclosable on a shared tree rather than ticking it |
| a spec's acceptance box asserts a count for a harness that reads no path in the spec's `footprint:` | the box gates on the tree's worst neighbour | run it, quote it, and leave the box open with the reason when the neighbour is red — the unit's own verdict comes from the footprint-scoped lines |
| the block prints its failure word on a tree you know is clean | a `cmd && echo BAD \|\| echo OK` line whose `cmd` exits 0 on zero matches — `find` does, `grep` does not | measure it as `[ -z "$(cmd)" ]`, quote both results, and report the spec's line as a finding |
| the block's last command exits 0 but an earlier one did not | the block is many commands and only the last one sets `$?` | run and quote them one at a time |
| a line in the block runs a command expecting a refusal (`add x` with no `--as`, a gated transition) and the run leaves a new `??` under `prds/` | the refusal was lifted under you — a sibling's uncommitted change made the probe a writer, and it wrote on the live board | `git status --short prds` right after the run; remove only what the run filed, re-point the line at a `python3 resources/board/plan.py example <tmpdir>` copy so it measures the claim rather than the refusal, and report the spec's line as a finding |
| a box asserts a file's diff is confined to named places, and `git diff` shows one more hunk in a function the spec itself says a sibling PRD is editing | the tree is shared; the box measures this unit's hunks, not the file's | list the hunks by `@@` header, name the sibling's and the untouched lines between, tick on your own hunks and quote the sibling's beside the box |
| a `grep -c '<needle>'` line in the block prints `0` while the sentence stands in the file | the reference wrapped the sentence across two lines and the needle is one line — the box was written from the answer, not run | re-wrap so the needle reads on one line, inside the footprint; quote the `0` and the `1`; say the rule did not move, and report the spec's box as never run at spec time |
| a probe line in the block matches the wording of a line another file prints, and that file is a sibling's uncommitted hunk that moved between the baseline and this run | the matcher read the sibling's format, not the rule the box asserts | re-read the sibling file (`git diff --stat`, mtime against the baseline), re-aim the matcher to the rule — the PRD listed in the band, not the words on its row — quote both outputs, and name the box clause the move made stale |
| a `grep -c` line in the block carries a `^` inside its needle and prints `0` while `sed -n <line>p` shows the text | grep read the `^` as an anchor, not the character the harness's own sed range quotes | re-run it as `grep -cF`, quote both, close the box on the `sed` line, and report the spec's line as a finding |
| a `memos.py check` line `prds: <slug> is not a PRD on this board` for a box that spells a nested PRD by its basename | the memo checker keys `prds:` on the path under `prds/`, and the spec was written from the answer, not run | write `parent/child` as every other memo does, quote the refusal and the silent re-run, and report the spec's box as never run at spec time |
