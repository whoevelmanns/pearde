---
complexity: 12
footprint:
  - resources/board/collect.py
  - references/parts/commits.md
  - prds/memos/the-record-is-always-whole.md
  - prds/the-board-runs-itself/collect-is-a-command/probe/verify.sh
  - prds/the-tool-keeps-its-word/collect-keeps-its-word/probe/verify.sh
---

# spec01 — the record lands whole, and `commit:` follows in a one-key commit

`collect` never stages the PRD's own folder by hunk and never stops on it:
everything under `prds/<prd>/` is added whole. `state: done`, `actual:`, the
cleared `claim:` and the daemon's `## Report` are written before the commit
that carries them; `commit:` — the one key that cannot name the commit it is
in — lands in a second, one-key commit `<prd> — record` right behind, so
nothing `collect` writes rides a later collect. Reproduced first on
`e8b262d`: the old collect said `by hunk prds/finished/prd.md`, committed
three ticks under `state: analyzing`, and left the folder dirty after its
own run (probe section A1).

## What already stands (built in place — an edit to an existing file has no
meaning outside its function)

- `resources/board/collect.py`: the folder rule in `sort_paths()` (the
  `inside(path, [prd_rel])` branch before the union branch); step 4 stages
  every repo first, writes the record, posts the report, `git add`s the
  folder again and commits — a failing commit puts `prd.md` back whole and
  resets the index; step 5 writes `commit:` and makes the `<prd> — record`
  commit; `owe()` is no longer called for the record (it stays for
  `answer`, transitions.py:323); the top docstring says all of it; `--dry`
  prints a `record:` line.
- `references/parts/commits.md`: the sentence **The PRD's own folder is
  committed whole, and its `done` is in the same commit.** with its
  paragraph, and **Board state written between transitions rides the next
  collect.** in place of the `commit:` rider paragraph.
- The probe: sections A (A1 reproduction, A2 the two commits, A3 a clean
  tree, A4 `--dry`), B6 (adjacent edits inside the folder go whole) and D
  (a daemon on a spare port; `## Report` is in `HEAD~1`).

## What is left

1. `prds/memos/the-record-is-always-whole.md`: `status: decided`, and the
   `## Decision` paragraph replaced by, paste-ready:

   > Decided 2026-08-29, built in `collect-keeps-its-word`. (1) The by-hunk
   > path never applies under the PRD's own folder: `sort_paths()` adds
   > everything under `prds/<prd>/` whole, never stops on it, never
   > classifies its hunks — the record has one writer. (2) `state: done`,
   > `actual:`, the cleared `claim:` and the posted `## Report` are written
   > before the commit and are in it; `commit:` follows in a second,
   > one-key commit `<prd> — record`, so no rider list exists for what
   > `collect` writes. The second alternative below is what was taken;
   > `prds/.claims/riders` remains for `answer`'s writes only.

2. `prds/the-board-runs-itself/collect-is-a-command/probe/verify.sh` —
   17 lines read `HEAD` where the record commit now sits; the rules they
   assert did not move. Re-aim, one matcher each:
   - `paths()` and `git log -1 --format=%B` in A, C, K, N, O, Q read
     `HEAD~1` (the code commit); A's "one commit on top" becomes two; A's
     `commit: <sha>` is `HEAD~1`'s short sha.
   - H: the record commit is made on a clean tree too — "no new commit"
     becomes two, and `commit:` is `HEAD~1`'s sha, never `none`.
   - I: the record is no longer owed — assert `prds/.claims/riders` does
     not list `prds/finished/prd.md`, that the next collect is not stopped,
     and that `finished/prd.md` is NOT on `building`'s commit; drop
     `rides prds/finished/prd.md` from the line check.
   Its `spec02.md` box text about riders is that PRD's history and stays.

## Acceptance

- [x] `bash prds/the-tool-keeps-its-word/collect-keeps-its-word/probe/verify.sh` prints every `A`, `B6` and `D` line as `ok` and ends `0 fail`
- [x] on the probe's A2 fixture `git log -2 --format=%s` reads `finished — record` then the contract subject; `git show HEAD~1:prds/finished/prd.md` reads `state: done`, `actual:`, no `claim:`, no `commit:`; `git show HEAD:prds/finished/prd.md` reads `commit: <HEAD~1 short sha>`; `git status --porcelain prds/finished` is empty
- [x] `grep -c 'committed whole, and its `done` is in the same commit' references/parts/commits.md` prints `1` and `grep -c 'rides the next collect.\*\*' references/parts/commits.md` names only the between-transitions rule
- [x] `grep -c '^status: decided' prds/memos/the-record-is-always-whole.md` prints `1` and its `## Decision` opens with `Decided 2026-08-29`
- [x] `bash prds/the-board-runs-itself/collect-is-a-command/probe/verify.sh` prints `133 checks · 133 pass · 0 fail`, its 17 re-aimed lines reading `HEAD~1` or the absence of the rider

## Verify and Proof

```sh
python3 -m py_compile resources/board/collect.py
bash prds/the-tool-keeps-its-word/collect-keeps-its-word/probe/verify.sh
bash prds/the-board-runs-itself/collect-is-a-command/probe/verify.sh
grep -c 'committed whole, and its `done` is in the same commit' references/parts/commits.md
grep -c '^status: decided' prds/memos/the-record-is-always-whole.md
```
