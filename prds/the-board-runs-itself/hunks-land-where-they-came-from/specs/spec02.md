---
complexity: 3
workflow: implement-a-spec
footprint:
  - references/parts/commits.md
---

# spec02 — commits.md says how a by-hunk file is placed, in one sentence

`references/parts/commits.md` is the spec of step 3. Its by-hunk rule says a
shared file "is committed by hunk, and the inherited hunks stay in the tree"
— true, and silent on *how*, which is where the defect lived. One sentence
replaces it.

## What already stands

Nothing in this file. The probe did not touch `commits.md`: a sibling
analyst (`the-loop-is-commands`) has it open. This spec runs **after that
PRD's edit lands** — read the file fresh, then make the one replacement.

## What is left

Under `**Scope: the footprint, never the tree.**`, first bullet, replace

> A file holding inherited hunks and the worker's is committed by hunk, and
> the inherited hunks stay in the tree.

with

> A file holding inherited hunks and the worker's is committed by hunk: the
> staged blob is the working file with the inherited hunks reversed, each
> hunk at the line the working file has it, checked for parse and placement
> before the commit — never a patch `git apply` places — and the inherited
> hunks stay in the tree.

One sentence, no other line moves. If the sibling's landing reworded the
bullet, keep its wording and put the clause between "committed by hunk" and
"the inherited hunks stay in the tree".

## Acceptance

- [x] `grep -c 'the working file with the inherited hunks reversed' references/parts/commits.md` prints `1`
- [x] `grep -c 'committed by hunk, and the inherited hunks stay' references/parts/commits.md` prints `0`
- [x] `grep -c 'never a patch .git apply. places' references/parts/commits.md` prints `1`

## Verify and Proof

```sh
test "$(grep -c 'the working file with the inherited hunks reversed' references/parts/commits.md)" = 1
test "$(grep -c 'committed by hunk, and the inherited hunks stay' references/parts/commits.md)" = 0
test "$(grep -c 'never a patch .git apply. places' references/parts/commits.md)" = 1
```
