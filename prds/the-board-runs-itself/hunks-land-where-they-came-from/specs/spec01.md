---
complexity: 12
workflow: implement-a-spec
footprint:
  - resources/board/collect.py
  - prds/the-board-runs-itself/hunks-land-where-they-came-from/probe
---

# spec01 — step 3 stages a shared file by reversal, and refuses a misplaced or unparsable blob before the commit

`collect`'s step 3 stages a file that carries both inherited and the PRD's own
hunks as **the working file with the inherited hunks reversed, bottom-up** —
hashed with `git hash-object`, pointed at with `git update-index --cacheinfo`
— and, before any commit, reads the staged blob back: it must parse where a
parser exists, and every kept hunk's lines must sit at the working-file line
minus the inherited lines above it. `git apply` is gone from step 3; its exit
code was the defect (0db29e9).

## What already stands

The probe built it in the tree — `resources/board/collect.py` is modified,
uncommitted:

- `parse_hunk` — one `-U0` hunk as `old`/`new` ranges and `minus`/`plus`
  lines, `\ No newline at end of file` honoured on either side.
- `reverse_hunks(text, hunks)` — the working text with each hunk undone from
  the bottom up; a `+N,0` hunk puts its `-` lines back after line N, any
  other hunk asserts its `+` lines are what the file holds at N and replaces
  them; a mismatch or two hunks on one line is a `Stop`.
- `misplaced(staged, kept, foreign, working_len)` — the placement check:
  length, and each kept hunk's `+` lines at `N − Σ(new_len − old_len)` of
  the foreign hunks above; a kept deletion's `-` lines must not sit there.
- `parse_error(path, text)` — `python3 -m py_compile` for `.py`, `node
  --check` for `.js/.mjs/.cjs`, silent when no parser is on the machine.
- `stage_by_hunk`, `placement_refusals` — the staging and the read-back.
- `new_hunks` in `sort_paths` returns `(kept, inherited)` instead of a
  patch; the staging loop in `collect_one` calls the two above and, on any
  refusal, `git reset -q -- <the paths it staged>` and `Stop`s — nothing
  committed, the index back at HEAD, the PRD still `claimed`.
- `prds/the-board-runs-itself/hunks-land-where-they-came-from/probe/verify.sh`
  — `47 checks · 47 pass · 0 fail`: section A reproduces the old staging by
  hand (`git apply --cached --unidiff-zero` exits 0, the line lands at 11
  inside `fetchPrd`, `node --check` passes on it); B–G cover the new path,
  a deletion above and a replacement below, no newline at EOF, the check on
  a shifted blob and end to end with the index put back, the parse refusal,
  `--dry`, a kept deletion.

## What is left

Nothing in the code. The implementer reads the diff, runs the two harnesses,
ticks the boxes from their output. Every box below reads the staged or
committed blob's content — none closes on an apply's exit code, per the
PRD's rule.

## Acceptance

- [x] `bash prds/the-board-runs-itself/hunks-land-where-they-came-from/probe/verify.sh` ends `0 fail`, and its section A prints `A the old staging puts it at 11 of a blob four lines shorter — inside fetchPrd` as `ok` while section B prints `B the line sits at 7 of HEAD — working 11 minus the four foreign lines` as `ok`
- [x] `grep -c '"apply", "--cached"' resources/board/collect.py` prints `0`
- [x] `bash prds/the-board-runs-itself/collect-is-a-command/probe/verify.sh` ends `0 fail` — section N's `the worker's hunk landed` and `the inherited hunk did not` both `ok`
- [x] `python3 -m py_compile resources/board/collect.py` exits 0

## Verify and Proof

```sh
python3 -m py_compile resources/board/collect.py
bash prds/the-board-runs-itself/hunks-land-where-they-came-from/probe/verify.sh
bash prds/the-board-runs-itself/collect-is-a-command/probe/verify.sh
test "$(grep -c '"apply", "--cached"' resources/board/collect.py)" = 0
```
