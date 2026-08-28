---
complexity: 14
workflow: implement-a-spec
footprint:
  - resources/board/collect.py
  - prds/the-board-runs-itself/collect-is-a-command/probe
---

# spec02 — step 3: the paths, the inherited tree, the baseline at claim, and what rides

Step 3 sorts every dirty path of each repo the PRD wrote into one of five
bins, and the commit takes exactly the first three. "The claim predates it"
is answered by a record `claim:` leaves under `prds/.claims/<prd>/`, written
by `snapshot()` in `collect.py`; without the record a file's mtime against the
claim's timestamp decides for the whole file.

| bin | is | does |
|---|---|---|
| add | inside the union — specs' `footprint:` ∪ the PRD's ∪ the PRD dir ∪ `--also` — and not older than the claim | `git add -- <path>` |
| by hunk | a tracked file inside the union holding hunks the baseline has and hunks it lacks | the new hunks alone, `git apply --cached --unidiff-zero`; the inherited hunks stay in the tree; `by hunk <path>` on the line |
| rides | listed in `prds/.claims/riders` by `owe()`, or, with a baseline, under `prds/` outside any held PRD's dir and newer than the claim | added, `rides <path>` on the line, settled from the file |
| stop | inside the union and older than the claim — every hunk in the baseline, or in its untracked list, or mtime before the claim | listed, exit 1, nothing written; `--widen <path>` moves it to **add** and the message gets `widen: <path>` |
| inherited | everything else | listed once under `inherited, not added`, exit 0, `inherited <n>` on the line |

The board's own dotfiles — `prds/.claims/`, `.round.md`, `.history.jsonl`,
`.plan.json` — are in no bin: skipped whole.

## What stands

`sort_paths()`, `snapshot()`, `baseline()`, `owe()`/`owed()`/`settle()`,
`split_hunks()`, `dirty_paths()` (porcelain `-z -uall`, renames read by their
new name) are in `resources/board/collect.py`. `collect --snapshot <prd>` is
the record by hand — what `claim` will call. The harness proves C
(inherited, `--widen <path>`), I (riders across two collects), N (a file with
one inherited and one new hunk lands with the new hunk only — `git show
HEAD:src/big.txt` holds `nine-ours` and not `two-theirs`, `git diff
--numstat` reads `1 1`), O (the stop, with and without a baseline), Q (a
rename).

Diffs are taken with `-U0` on both sides so two edits near each other are two
hunks. Two hunks with identical bodies at different positions read as one —
a limit, said here, not a box.

## What is left

- `transitions-are-commands`' `claim` calls `snapshot(board, rel)` — that
  PRD's edit, named in the report. Until it does, the orchestrator runs
  `collect --snapshot <prd>` at claim time or accepts the mtime rule.
- `.gitignore` gains `prds/.claims/` — outside this PRD's footprint, named in
  the report. The harness fixture has no `.gitignore`; the dotfile skip above
  is what keeps `.claims/` out of a commit there.

## Acceptance

- [x] harness section C: a file dirtied outside the footprint is listed once under `inherited, not added`, not on the commit, still dirty after, exit 0; `--widen stray.txt` puts it on the commit and `widen: stray.txt` in the message
- [x] harness section N: after `--snapshot`, a tracked file in the footprint with one older hunk and one newer lands with the newer hunk only, and the tree stays dirty by exactly the older one
- [x] harness section O: an untracked file in the footprint recorded by the snapshot, or a tracked file whose every hunk is in it, or — with no snapshot — a file whose mtime precedes `claim:`, stops with exit 1 and the path named; `--widen <path>` takes it
- [x] harness section I: the `commit:` line collect wrote rides the next collect on the board and is named `rides prds/finished/prd.md` on the line; `prds/.claims/riders` holds only what is still owed afterwards
- [x] harness section Q: a `git mv` inside the footprint after the snapshot commits under the new name
- [x] `collect --snapshot finished` writes `diff`, `untracked`, `gate`, `at` under `prds/.claims/finished/`, and `--dry` after it lists the inherited paths and writes nothing
- [x] no path under `prds/.claims/` is ever on a commit the harness makes

## Verify and Proof

```sh
bash prds/the-board-runs-itself/collect-is-a-command/probe/verify.sh
grep -n 'def snapshot\|def sort_paths\|def owe\|unidiff-zero' resources/board/collect.py
```
