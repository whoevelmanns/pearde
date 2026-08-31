---
atomic: settle-the-key-in-the-contract
subject: give a new frontmatter key its contract row and its default
date: 2026-08-28
runs: 0
---

# settle-the-key-in-the-contract — one home for what the key means

## Do

1. Add the key's row to the right table in `references/parts/contract.md` —
   the `prd.md` table, the `specNN.md` table, or both: `| key | written by |
   read for |`.
2. Add its row to the defaults table, saying what a missing key reads as. A
   key with no stated default is read differently by every reader.
3. When the key exists in both a PRD and a spec, say in the row which one
   overrides the other, and for what scope.
4. `grep -n '<key>' references/parts/contract.md` and read every hit.

## Done when

- The key has a row in at least one contract table, naming who writes it and
  what reads it.
- The key has a row in the defaults table, or the row says it is required.
- No sentence about the key's meaning was added to a second file.

## Fails when

| seen | means | do |
|------|-------|----|
