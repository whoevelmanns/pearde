---
atomic: capture-the-harness-baseline
subject: record what every committed harness prints before the tree is touched
date: 2026-08-28
updated: 2026-08-29
runs: 44
---

# capture-the-harness-baseline — the numbers as they were before you

## Do

1. `find prds -name verify.sh | sort` — every committed harness on this board, at
   whatever depth it sits. A fixed glob list aborts on the first depth that
   has no match, and under a shell with `nomatch` it prints nothing at all.
2. Run each one that reads a path in your `footprint:` — grep each harness
   for the footprint paths spelled from the repo root (`references/settings.md`,
   not `settings.md`: a bare board filename matches every fixture that writes
   one) — each one whose PRD is named in `needs:`, and each one that runs
   `git status` or `git diff` at the repo root, because that reads every
   footprint. Record the exact count it prints, verbatim, and `git status
   --short` beside it: the untracked files a root-level check sees are the
   only way to tell your drop from a neighbour's later. Save each harness's
   whole output to a scratch file, not only its count — when a count moves you
   need the FAIL line, and the machine may sleep before you can re-run it. Write them under a subdirectory named for this run — the scratch directory is shared across sessions, and a bare `grep FAIL <scratch>/*` sweeps another worker's outputs in with yours. Record the mtime and `git diff -U0 | grep -c '^@@'` of every file outside your footprint that a spec says it stands on — a predicate in a sibling's file moves during the run, and the number beside each run is the only way to say which plan.py a count was taken against.
3. Record `python3 resources/index.py check` and `bash resources/doctor.sh`
   the same way — **their exit codes as well as their lines** — the lines they print now, plus any line the contract itself
   adds (a new doctor row, a new file the map will name), are the lines you are
   allowed to still see at the end; name each added one in the report.
4. A harness that is already failing is recorded as failing before your first
   edit. It is a finding, not yours to fix.

## Done when

- Each harness that touches a footprint path has a recorded count, quoted.
- The recording happened before any file was written — `git status --short`
  at this point lists nothing you added.
- Any pre-existing failure is written down with the words "before the first
  edit" beside it.

## Fails when

| seen | means | do |
|------|-------|----|
| the baseline `git status --short` list is *shorter* at step 5 than at step 2, and a footprint path you never staged is now clean | a sibling session committed while you ran; those paths are theirs, landed | `git log --oneline` for the new HEAD and `git log -1 -- <your footprint path>`; if your path's last commit predates your run, your hunks are intact and uncommitted. Record the new HEAD in the report — a shrinking dirty list is another session finishing, not your edits vanishing |
| `index.py check` or `doctor` prints lines at step 4 that were not there at step 2 and name files outside your footprint | parallel workers moved the baseline under you | count as yours only the lines naming your footprint; quote the rest beside the baseline as inherited |
| `no matches found` or `No such file or directory` from the listing | a glob names a depth this board has no harness at | list with `find prds -name verify.sh` — it prints what exists and exits 0 |
| the listing is empty on a board that has harnesses | the shell aborted the whole command on the first empty glob | same |
| `doctor` at step 4 differs from step 2 only on the `statusline` row | that row carries the tree's dirty-file count, which every live session moves | compare doctor's rows without `statusline`; the count is nobody's finding |
