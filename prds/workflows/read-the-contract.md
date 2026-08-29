---
atomic: read-the-contract
subject: read the PRD, its answers and everything it cites, before the first edit
date: 2026-08-28
updated: 2026-08-28
runs: 44
---

# read-the-contract — the whole contract in the window before anything moves

## Do

1. `cat prds/<prd>/prd.md`. Read the body, and `## Answers`, `## Questions`
   and `## Failure` if they are there — an answer already on the file closes
   a fork you would otherwise ask again.
2. `ls prds/<prd>/specs/` and read every file it lists. A spec's own
   `workflow:` and `footprint:` override the PRD's for that unit, and its
   `## Verify and Proof` block is the command set for it.
3. Resolve every `@<path>` and `@@<keyword>` the body cites and open it. `@`
   is a path from the skill root; `@@` is a row in `index.md`, and the first
   anchor in that row is the file that answers the question.
4. `git status --short`. Write down which paths are already modified — that
   list is the only thing that later tells your hunks from someone else's.
5. Write down the `footprint:` paths and, for each, whether it exists yet.

## Done when

- Every `@` and `@@` in the body resolved to a file that exists, or the
  dangling one is named in the report.
- Every path in `footprint:` has been opened, or is stated as not yet on disk.
- The `git status --short` list is recorded before the first edit, not after.

## Fails when

| seen | means | do |
|------|-------|----|
| the coordinator reports the PRD body changed while you were building | the contract moved; the build stands on the old text | re-run this step on the new text, keep the build, name both reads in the report |
| `git status --short` lists paths the brief did not | the tree is live; other sessions wrote since the brief | record what you see now — that list, not the brief's, tells your hunks from theirs |
