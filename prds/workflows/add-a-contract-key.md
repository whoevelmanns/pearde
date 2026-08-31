---
workflow: add-a-contract-key
subject: a new frontmatter key, from the contract row to the check that fails on it
date: 2026-08-28
runs: 0
---

# add-a-contract-key — a key the tools read, wired end to end

## Use when

- A contract adds a key to `prd.md`, to `specNN.md`, or to a format with its
  own reader under `resources/`.
- An existing key gains a value the check must reject, or a default it did not
  have.
- Not when the key is yours alone and no tool reads it — the contract says
  every other key is yours and no tool touches it, so there is nothing to wire.
- Not when only the wording of an existing key's row is wrong — that is
  `correct-a-documented-claim`.

## Steps

| # | atomic | why | on failure |
|---|--------|-----|------------|
| 1 | `read-the-contract` | names which files already read frontmatter, so the key gets one reader and not a second | `stop` |
| 2 | `settle-the-key-in-the-contract` | one home for the meaning, or every reader invents its own default | `→ 1` |
| 3 | `teach-the-reader` | a row in the manual with no check behind it is a note | `→ 2` |
| 4 | `sweep-for-other-copies` | the closed set is enumerated in the templates and the briefs, and a key missing from one of them reads as a typo | `→ 2` |
| 5 | `run-the-repo-gate` | catches the check that was added and never reached from a row a person runs | `→ 3` |
