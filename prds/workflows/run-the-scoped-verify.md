---
atomic: run-the-scoped-verify
subject: run the unit's own verify command and quote what it printed
date: 2026-08-28
updated: 2026-08-28
runs: 1
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
| the block prints its failure word on a tree you know is clean | a `cmd && echo BAD \|\| echo OK` line whose `cmd` exits 0 on zero matches — `find` does, `grep` does not | measure it as `[ -z "$(cmd)" ]`, quote both results, and report the spec's line as a finding |
| the block's last command exits 0 but an earlier one did not | the block is many commands and only the last one sets `$?` | run and quote them one at a time |
