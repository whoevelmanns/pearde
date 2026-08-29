---
atomic: edit-inside-the-footprint
subject: confine the change to the paths the contract names
date: 2026-08-28
updated: 2026-08-29
runs: 22
---

# edit-inside-the-footprint — the change, and nothing beside it

## Do

1. Edit only paths listed in the contract's `footprint:`. A file you need
   that is not listed is a finding for the report, not a widening — see
   @references/parts/workers.md.
2. Leave every path someone else already modified alone. When one is both
   inherited-dirty and in your footprint, add your hunks and nothing else,
   and say so in the report so the commit can be staged hunk by hunk.
3. `git status --short` and `git diff --stat`. Compare against the list you
   recorded before the first edit. A footprint of files not yet tracked shows
   nothing in `git diff` — account for those with `git status --short` and
   `wc -l` on each new file instead.

## Done when

- `git status --short` names no changed path outside `footprint:` that was
  not already changed before you started.
- Every inherited-dirty file is either untouched by you, or its added hunks
  are listed in the report by file and section.
- Every tracked footprint path is accounted for line by line in
  `git diff --stat`, and every untracked one by its path and line count.

## Fails when

| seen | means | do |
|------|-------|----|
| a hunk you wrote in a shared file is gone from `git diff` | a sibling staged the whole file and committed your lines with theirs | `git show HEAD:<path>` to confirm they landed, name that commit in the report, and stage nothing twice |
| a path outside your footprint is dirty at step 3 that was clean in the step-1 list | a sibling session wrote it while you ran | `git diff <path>` to confirm none of its hunks are yours, quote the path as inherited beside the baseline list, and do not touch it |
| the wired guard denies a heredoc edit script with "The board is not walked by hand" | the `Bash` hook matches the hand-walk literal inside your script's text, not only in a command you run | write the script to the scratch dir and run it by path; nothing about the edit changes |
