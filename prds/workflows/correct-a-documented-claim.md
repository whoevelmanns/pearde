---
workflow: correct-a-documented-claim
subject: a wrong or ambiguous claim, corrected everywhere it is copied
date: 2026-08-28
runs: 2
---

# correct-a-documented-claim — the claim, and its copies

## Use when

- A settled decision contradicts a sentence that still ships in `references/`,
  a template or a script comment.
- A claim is ambiguous enough that two readers write different values into one
  field.
- Not when a new page or a new key is being added — those are
  `add-a-file-to-the-skill` and `add-a-contract-key`.
- Not when the code is wrong and the text describes it correctly: that is an
  ordinary spec, and the route is `implement-a-spec`.

## Steps

| # | atomic | why | on failure |
|---|--------|-----|------------|
| 1 | `read-the-contract` | says which reading was settled and which file now holds it | `stop` |
| 2 | `capture-the-harness-baseline` | a committed harness may already assert the sentence you are about to rewrite | `→ 1` |
| 3 | `edit-inside-the-footprint` | a correction is worth nothing if it lands on a path the contract did not clear | `→ 1` |
| 4 | `sweep-for-other-copies` | one corrected site beside three stale ones is a claim that still ships wrong | `→ 3` |
| 5 | `re-run-the-harnesses` | tells a rule you broke from a table row you merely re-padded | `→ 4` |
| 6 | `run-the-repo-gate` | proves the manual and the map moved together | `→ 3` |
