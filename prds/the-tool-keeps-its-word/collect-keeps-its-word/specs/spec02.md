---
complexity: 8
footprint:
  - resources/board/collect.py
  - references/parts/commits.md
  - prds/memos/adjacent-edits-merge-into-one-hunk.md
  - prds/the-tool-keeps-its-word/collect-keeps-its-word/probe/verify.sh
---

# spec02 — a hunk with two authors is refused, never committed whole

Two edits on adjacent lines merge into one `-U0` hunk whose body is in
neither the claim's baseline nor the worker's own diff. `collect` refuses the
file — `two authors on one hunk: <file>:<line>`, exit 1, nothing staged —
and the worker widens with `--widen <file>` or leaves one untouched line
between the edits. Line-level matching is not attempted. Reproduced first on
`e8b262d`: a foreign edit on line 10 and the worker's on 11 were one hunk,
`new_hunks` said `all`, and `line10-theirs` landed as the worker's (probe
section B1).

## What already stands (built in place)

- `resources/board/collect.py`: `hunk_sides()`, `sublist()` and
  `two_authors()` beside `hunk_body()`; `new_hunks()` inside `sort_paths()`
  computes `gone` — the baseline hunks no current hunk matches by body — and
  raises `Stop` naming the working line of the first kept hunk whose `+`
  and `-` sides hold a gone hunk's lines as a contiguous run. A baseline hunk
  that is simply gone (undone before collect) is not a refusal (B5). The
  PRD's own folder never reaches this check (spec01's rule comes first, B6).
- `references/parts/commits.md`: the sentence **A hunk with two authors is
  refused, never committed whole.** with its paragraph.
- The probe: B1 (reproduction), B2 (refusal, index at HEAD, nothing
  committed, state still `claimed`, then `--widen` takes the file whole and
  says `widened`), B3 (one untouched line between: the worker's line in
  `HEAD~1`, the foreign one not, `by hunk` on the line), B4 (a foreign
  insertion right above the worker's change is refused at the working
  line), B5.

## What is left

1. `prds/memos/adjacent-edits-merge-into-one-hunk.md`: `status: decided`,
   and the `## Decision` paragraph replaced by, paste-ready:

   > Decided 2026-08-29, built in `collect-keeps-its-word`: **refuse the
   > file.** A kept hunk whose sides hold a vanished baseline hunk's lines
   > as a contiguous run is a hunk with two authors; `collect` exits 1 with
   > `two authors on one hunk: <file>:<line>` before anything is staged,
   > and `--widen <file>` or one untouched line between the edits is the
   > worker's answer. Line-level matching was not taken: the interleaved
   > case is the one no diff can settle. Known residual: a baseline
   > insertion whose lines legitimately recur inside the worker's own
   > insertion (a lone `}`) is refused too — the cost is one `--widen`.

## Acceptance

- [x] `bash prds/the-tool-keeps-its-word/collect-keeps-its-word/probe/verify.sh` prints every `B` line as `ok` and ends `0 fail`
- [x] on the probe's B2 fixture `collect finished` exits 1, prints `two authors on one hunk: src/util.py:10`, `git diff --cached --stat` is empty, `git rev-list --count HEAD` is unchanged, and `prds/finished/prd.md` still reads `state: claimed`
- [x] `grep -c 'two authors on one hunk' references/parts/commits.md` prints `1`
- [x] `grep -c '^status: decided' prds/memos/adjacent-edits-merge-into-one-hunk.md` prints `1` and its `## Decision` opens with `Decided 2026-08-29`

## Verify and Proof

```sh
python3 -m py_compile resources/board/collect.py
bash prds/the-tool-keeps-its-word/collect-keeps-its-word/probe/verify.sh
grep -c 'two authors on one hunk' references/parts/commits.md
grep -c '^status: decided' prds/memos/adjacent-edits-merge-into-one-hunk.md
```
