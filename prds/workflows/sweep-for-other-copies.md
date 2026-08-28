---
atomic: sweep-for-other-copies
subject: find the copies of a claim you corrected in one place
date: 2026-08-28
updated: 2026-08-28
runs: 3
---

# sweep-for-other-copies — one fix is not a fixed claim

## Do

1. Take a distinctive phrase from the text you replaced — five to eight words,
   not the whole sentence, and not a word the tree uses everywhere. For a file
   that moved, the phrase is the old path, and a second one is the mark its old
   row carried (`pending · <prd>`, `not yet — <prd>`).
2. `grep -rn "<phrase>" --include='*.md' --include='*.py' --include='*.sh' .`
   Do the same for the shape of the claim rather than its wording when the
   phrase is short: a table row, a key name, an enumeration of a closed set.
3. Correct each hit inside your `footprint:`. Each hit outside it goes in the
   report as a finding, naming the file, the line and what it would get wrong
   — it is not yours to edit.
4. Say the count: how many hits before, how many corrected, how many named as
   out of scope.

## Done when

- The grep is quoted in the report with its full hit list.
- Every remaining hit is either the corrected text or named as out of scope
  with a line number.
- The before and after counts are both stated, and they add up.

## Fails when

| seen | means | do |
|------|-------|----|
