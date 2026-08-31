---
state: done
origin: derived
actual: 0.9h
commit: caec40f
from: the-board-runs-itself/collect-is-a-command
priority: 64
complexity: 15
blast-radius: high
repo: pearde
workflow: probe-then-spec
needs:
  - collect-is-a-command
footprint:
  - resources/board/collect.py
  - references/parts/commits.md
---

# hunks-land-where-they-came-from — `collect` stages a hunk at the line it came from, never at the line `git apply` guesses

When this is done, `pearde collect`'s step 3 stages a PRD's own hunks out of a
file that also carries another worker's hunks by rebuilding the blob — the
working file with the foreign hunks reversed, bottom-up — and never by
`git apply --cached --unidiff-zero` on a patch with hunks left out.

## The consequence, named

`resources/board/collect.py:622` stages "by hunk" with `git apply --cached
--unidiff-zero` over a `-U0` diff from which the inherited hunks were removed.
With zero context and hunks omitted, `git apply` places a kept hunk by its
**new-file** line number, which already counts the omitted hunks above it.
The apply succeeds, the blob parses, and the hunk sits in the wrong function.

Measured on this board, 2026-08-28, `reproduced` — fixture: the working tree
of this repo, `resources/board/view.js` carrying another session's 39 hunks
and this PRD's 13: the one-line hunk `@@ -2469,0 +2656 @@` (`else if (view ===
"report") drawReport();`) landed at line 2656 of the staged blob, inside
`fetchPrd`'s callback, 187 lines below `repaintView` where it belongs. The
blob passed `node --check`; the rendered page failed on `Unexpected token
'else'` and every check after it (viewtest `15/34`). The commit landed as
0db29e9 and was rebuilt as 0f59032 by hand.

That is `collect-is-a-command` getting its own contract wrong: step 3 promises
"only the PRD's own hunks committed", and on the first shared tree it commits
them in the wrong place — silently, since the staged file still parses.

## Files

| file | change |
|---|---|
| `resources/board/collect.py` | step 3's by-hunk path: for each shared file, take the working file's lines, reverse every hunk that is not the PRD's from the bottom up (a `+N,0` hunk inserts its `-` lines after line N; any other hunk replaces its `+` lines with its `-` lines, asserting the `+` lines are what the file holds), hash the result, `git update-index --cacheinfo`. No `git apply`. |
| `resources/board/collect.py` | before the commit, the staged blob of every shared file is checked: it must parse where a parser exists (`python3 -m py_compile`, `node --check`), and every kept hunk's `+` lines must appear in the staged blob **in the order and at the offset the working file has them, minus the reversed hunks** — a misplaced hunk is a refusal, never a commit |
| `references/parts/commits.md` | the by-hunk rule says how a hunk is placed, in one sentence |

## Rules

- A hunk's home is where the working file has it. Nothing re-derives a
  position from a patch header.
- A staged blob that parses is not evidence of placement; the offset check is.
- `git apply` exiting 0 is not evidence either: on a hunk-filtered `-U0`
  patch it succeeds at the wrong line. No acceptance box may close on an
  apply's exit code; every box on placement reads the staged blob's content.
- The probe harness carries this board's own fixture: a file with a foreign
  block above a one-line kept hunk inside an `if/else` chain, staged by the
  old path and the new, the old one shown misplaced.

## Verify

- The fixture above: the old staging misplaces the line (quoted); the new
  staging puts it at its working-file position minus the foreign lines.
- `git show :<file> | node --check` and the offset check both pass on the
  fixture, and the offset check refuses a deliberately shifted blob.
- `bash prds/the-board-runs-itself/collect-is-a-command/probe/verify.sh` stays green at whatever count it then carries.

## Report

DONE 7/7 · commit caec40f · probe 47/47 · collect 133/133
