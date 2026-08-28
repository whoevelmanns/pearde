---
atomic: capture-the-harness-baseline
subject: record what every committed harness prints before the tree is touched
date: 2026-08-28
updated: 2026-08-28
runs: 1
---

# capture-the-harness-baseline — the numbers as they were before you

## Do

1. `find prds -name verify.sh` — every committed harness on this board, at
   whatever depth it sits. A fixed glob list aborts on the first depth that
   has no match, and under a shell with `nomatch` it prints nothing at all.
2. Run each one that reads a path in your `footprint:`, and each one whose
   PRD is named in `needs:`. Record the exact count it prints, verbatim.
3. Record `python3 resources/index.py check` and `bash resources/doctor.sh`
   the same way — the lines they print now are the lines you are allowed to
   still see at the end.
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
| `no matches found` or `No such file or directory` from the listing | a glob names a depth this board has no harness at | list with `find prds -name verify.sh` — it prints what exists and exits 0 |
| the listing is empty on a board that has harnesses | the shell aborted the whole command on the first empty glob | same |
