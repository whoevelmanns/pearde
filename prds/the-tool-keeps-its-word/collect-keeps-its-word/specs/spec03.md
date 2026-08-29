---
complexity: 10
footprint:
  - resources/board/collect.py
  - references/parts/commits.md
  - prds/memos/a-container-cannot-reach-done.md
  - prds/the-tool-keeps-its-word/collect-keeps-its-word/probe/verify.sh
---

# spec03 — a container reaches `done` through `collect`

A parent whose every child is `done`, with no spec and no open box of its
own, is closed by `collect`: `state: done`, `actual:` the sum of its
children's, `commit:` the last child's, in one commit `<parent> — done: every
child landed` that adds its `prd.md` alone; the bare `collect` closes it
beside the held-and-finished. A parent with specs or boxes of its own is
ordinary work and its boxes decide it. Reproduced first on `e8b262d`:
`collect big` on the example's tree with both children done was refused on
`state is \`open\``, and `scan` did not list it (probe C1).

**Stands on the sibling.** The predicate is plan.py's
`dispatchable(prd, prds, board)` — `one-predicate-for-dispatchable`'s, in the
working tree since 2026-08-29 08:49 — whose word for the shape is
`container: every child done — pearde collect closes it`. `collect.py`
reads that word and adds no second definition. This spec is not
implementable on a tree without that hunk: the probe's C and Z sections are
red there, and the orchestrator should order this PRD after that one.

## What already stands (built in place)

- `resources/board/collect.py`: `container(prd, prds, board)` — `open` and
  `dispatchable` says `container:`; `last_child_commit()` — the newest of
  the children's shas by commit date, ties by depth, each resolved in the
  repo the child wrote, `none` when none resolves; `close_container()` —
  the record, the report with the phrase, one commit, the transition row,
  the line `container, N children · commit <last child's> · record <own>`;
  a `--dry` that prints the phrase, the children, the sum and the sha;
  `collect_one` step 1 takes the branch when `standing()` says not ready
  and `container()` says yes; `cmd_collect` with no argument appends every
  container of the plan's `todo` to the collect list.
- `references/parts/commits.md`: the sentence **A parent whose children are
  all `done` is closed by `collect`.** with its paragraph.
- The probe: C1 (reproduction), C2 (`scan` lists it in `dispatchable`'s
  words; `--dry`; the close — `3h`, the newer sha, one commit, `prd.md`
  alone, clean, a second collect refused), C3 (own spec: not listed,
  refused), C4 (own open box: refused), C5 (a child open: refused, not
  listed), C6 (a claimed parent whose own spec is ticked goes the ordinary
  way — two commits, never `container`), Z (the bare `collect` closes
  `finished` and `big`, two lines).

## What is left

1. `prds/memos/a-container-cannot-reach-done.md`: `status: decided`, and
   the `## Decision` paragraph replaced by, paste-ready:

   > Decided 2026-08-29, built in `collect-keeps-its-word` on
   > `one-predicate-for-dispatchable`'s predicate: **`collect` accepts a
   > container directly**, `open → done`. `dispatchable()` in plan.py is
   > the one word for the shape — children all `done`, no spec, no open
   > box of its own — `claim` refuses on it with `container: every child
   > done — pearde collect closes it`, `scan` lists it under collect, and
   > `collect <parent>` (or the bare `collect`) writes `done`, `actual:`
   > the children's sum and `commit:` the last child's in one commit
   > `<parent> — done: every child landed`. A separate `close` verb was
   > not taken: the band that lists finished work is the band that closes
   > it. A parent with specs or boxes of its own is never closed this way.

2. Nothing in `plan.py` — the clause this branch needs is already the
   sibling's `dispatchable()`. One finding for that PRD, not work here:
   `compute_plan()`'s `r["collect"]` does not hold the container (only
   `cmd_scan` appends it when printing), so `cmd_collect` computes it a
   second time through `container()`; moving the append into
   `compute_plan` makes `scan` and the bare `collect` read one list.

## Acceptance

- [x] `bash prds/the-tool-keeps-its-word/collect-keeps-its-word/probe/verify.sh` prints every `C` and `Z` line as `ok` and ends `0 fail`
- [x] on the probe's C2 fixture `python3 resources/board/plan.py scan <board>` lists `big` under `collect —` with `container: every child done — pearde collect closes it`, and `collect big` leaves `prds/big/prd.md` reading `state: done`, `actual: 3h`, `commit: <second's sha>`, with `git log -1 --format=%s` = `big — done: every child landed` and `git status --porcelain prds/big` empty
- [x] on the probe's C3 fixture (the parent carries `specs/spec01.md` with an open box) `collect big` exits 1 on `state is \`open\`` and `scan` does not list `big` under collect
- [x] `grep -c 'every child landed' references/parts/commits.md` prints `1`
- [x] `grep -c '^status: decided' prds/memos/a-container-cannot-reach-done.md` prints `1` and its `## Decision` opens with `Decided 2026-08-29`

## Verify and Proof

```sh
python3 -m py_compile resources/board/collect.py
bash prds/the-tool-keeps-its-word/collect-keeps-its-word/probe/verify.sh
grep -c 'every child landed' references/parts/commits.md
grep -c '^status: decided' prds/memos/a-container-cannot-reach-done.md
```
