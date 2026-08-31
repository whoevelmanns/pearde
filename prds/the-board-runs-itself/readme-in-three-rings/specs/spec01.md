---
complexity: 6
footprint:
  - README.md
---

# spec01 — the README, to the contract's table, true to the code

`README.md` is the one document with a human reader: seven sections in the
contract's order, under 200 lines, and every claim in it is what the command
prints today. The probe wrote it and left it in the tree; this unit is the
check that it still holds, and the correction when the code has moved.

## What stands from the probe

- `README.md` at 173 lines: **In sixty seconds** (five lines, and a table of
  what each prints, copied from a run), **What is on disk** (six paths),
  **The nine states** (one Mermaid state diagram, a `pearde` command on every
  arrow, no prose beside it), **The round** (the seven rows of
  @references/parts/loop.md, byte for byte, and one sentence), **Three
  rings** (core carries the "One question, one file" table and the scope
  table unchanged; advisors and tools end in their `@@` scopes),
  **Glossary** (twenty rows), **Addressing** (the two lines).
- The quickstart's third line is `pearde add --as engineer "…"` — `add`
  refuses without `--as <id>` or `PEARDE_AS`, by design in
  @resources/board/transitions.py, so the contract's bare `pearde add "…"`
  was corrected against the command.
- `probe/verify.sh` sections A–F check the shape and each claim;
  `probe/quickstart.sh` runs the five lines on a temp dir (an isolated copy
  of the tracked tree, a fresh skills dir, a spare daemon port, the live
  registry proven untouched).

## What is left

Run the probe. When a check fails on a line the code moved — a changed
progress line, a renamed band, a new port — correct the README to what the
command prints now, never the other way round.

## Acceptance

- [x] `wc -l README.md` prints a number ≤ 200
- [x] `bash prds/the-board-runs-itself/readme-in-three-rings/probe/verify.sh --no-run` ends `0 fail`
- [x] `bash prds/the-board-runs-itself/readme-in-three-rings/probe/quickstart.sh` ends `0 fail`, and the five outputs it prints under `$` match the **In sixty seconds** table
- [x] the Mermaid block names exactly the nine states of `references/parts/states.md` — section C of the probe prints no `FAIL`
- [x] `README.md` holds no emoji and no numbered marker outside the seven-row round table

## Verify and Proof

```sh
wc -l README.md
bash prds/the-board-runs-itself/readme-in-three-rings/probe/verify.sh --no-run
bash prds/the-board-runs-itself/readme-in-three-rings/probe/quickstart.sh
```
