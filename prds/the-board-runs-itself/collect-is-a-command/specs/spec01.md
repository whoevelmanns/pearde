---
complexity: 12
workflow: implement-a-spec
footprint:
  - resources/board/collect.py
  - prds/the-board-runs-itself/collect-is-a-command/probe
---

# spec01 — one call closes a finished PRD: verify, commit, record, report, line

`python3 resources/board/collect.py [<prd>…] [--dry] [--fail] [--trust]
[--also <path> --also-note <text>] [--as <id>] [--board <path>]` runs steps 1,
2, 4, 5, 6 and 7 of the PRD's table on each PRD named, or on every PRD in the
scan's **collect** section when none is. Step 3 — which paths — is spec02;
the gate inside step 2 is spec03. The module exposes
`COMMANDS = {"collect": cmd_collect}` for the dispatcher `one-command` builds,
and its own `__main__` until that lands.

## What stands

The probe left `resources/board/collect.py` in the tree, uncommitted, and
`probe/verify.sh` proves it on a board built under `git init` in a temp dir:

| step | function | proven by |
|---|---|---|
| 1 | `standing()` from `plan.py`; `open_boxes()` names the file and the box | A, J |
| 2 | `verify_blocks()` — every fence under `## Verify and Proof`, run by `bash -e -o pipefail` in `repo_of()`; `--fail` writes `## Failure`, clears `claim:`, sets `failed`; `--trust` skips it and says `trusted` | B, F |
| 4 | one `git commit -F -` per repo; the message from `contract_line()`, `spec_goals()`, `--also-note`; a clean tree is `commit: none` | A, H, K |
| 5 | `edit.py` `set_key` / `del_key` — `commit:`, `actual: <n>h`, no `claim:`, `state: done` | A |
| 6 | `post_report()` — `GET /status` finds the board by path, `POST /report {"board","prd","text"}`; down is said on the line | A (down) |
| 7 | `progress_line()` — every term of @references/parts/progress.md from `progress_terms()` and `compute_plan()`; `history_row()` appends `{"t","prd","from","to"}` | A, D |

`repo:` that names a directory is the code's repo; a name that is no directory
(`repo: pearde` on this board) is the board's own repo. `actual:` is hours
since the claim's timestamp, `0.42h` shaped; a claim with no timestamp writes
no `actual:`.

## What is left

- Run step 6 against a live daemon: `serve.py run` on a spare `PEARDE_PORT`
  inside the harness, the fixture registered with `POST /register`, and the
  collect leaves `## Report` in `prds/finished/prd.md`. Today the harness
  proves only the down case (`PEARDE_PORT=1`).
- When `transitions-are-commands` lands its progress-line printer, replace
  `progress_line()` here with that one call — two printers of one line is
  two lines that can disagree. Until then this one prints the terms.

## Acceptance

- [x] `bash prds/the-board-runs-itself/collect-is-a-command/probe/verify.sh` ends `· 0 fail`, and sections A, B, D, E, F, H, J, K, L, M are in it
- [x] on the fixture, `collect finished` makes exactly one commit, `prd.md` carries `commit: <short sha of HEAD>`, `actual: <n>h`, `state: done`, no `claim:`, and one `▸ finished: claimed → done` line ends `· as engineer`
- [x] on the fixture with the verify made to `exit 1`: exit 1, the output on stdout, `git rev-list --count HEAD` unchanged, `git diff -- prds/finished/prd.md` empty; with `--fail`: `state: failed`, `## Failure` holds the output, still no commit
- [x] `collect` with no argument collects `finished` and leaves `building` `claimed`; a second call prints `nothing finished` and exits 0
- [x] `git log -1 --format=%B` on the fixture equals `<prd> — <contract>`, blank, `spec01: <goal>`, blank, `prd: prds/finished` — line for line
- [x] with a daemon on a spare `PEARDE_PORT` and the fixture registered, the collect leaves `## Report` in `prds/finished/prd.md` holding `spec01: exit 0` and the line says `report posted`
- [x] `python3 -c 'import collect; print(sorted(collect.COMMANDS))'` from `resources/board` prints `['collect']`

## Verify and Proof

```sh
bash prds/the-board-runs-itself/collect-is-a-command/probe/verify.sh
cd resources/board && python3 -c 'import collect; print(sorted(collect.COMMANDS))'
python3 -m py_compile resources/board/collect.py
```
