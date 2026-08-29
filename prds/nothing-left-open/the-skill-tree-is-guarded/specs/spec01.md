---
complexity: 6
footprint:
  - resources/guard.py
  - resources/doctor.sh
  - prds/nothing-left-open/the-skill-tree-is-guarded/probe/verify.sh
---

# spec01 — `guard.py pre` refuses a write into the skill tree from another board, and `status` proves it

`pre`, on an `Edit` or `Write` whose `file_path` resolves — through any install
link, or by name — to a file under this repo's root (`SKILL`, the real path of
the directory holding `resources/`), reads the session's board the way
`find_board` does (the nearest `prds/` above the hook's `cwd`) and denies when
that board's repo is not `SKILL`: the reason names the path as given and the
real path it resolves to, the session's board, the memo
`prds/memos/the-install-is-live-symlinks.md`, and the two ways out — file a
PRD on the skill's own board (`pearde add "<title>"` from `SKILL`) or hand the
edit to a session working it. No board in scope passes; this repo's own board
passes; a write under this repo's `prds/` passes from anywhere, because filing
here is the way in. `guard status` runs a second probe — an `Edit` of `SELF`
from a temp dir holding an empty `prds/`, its `PEARDE_GUARD_STATE` beside it —
and reports `broken` when it is not denied; its `ok` row ends `· skill tree
guarded`. `doctor.sh`'s own `guard` `ok` row carries the same two words on the
strength of `guard status` having that probe — one line, the widening this
PRD's footprint did not list.

## What stands from the probe

All of it, built in place in the footprint files (an edit to an existing file
cannot be staged under `probe/`): `resources/guard.py` — the docstring line,
`SKILL`, `MEMO`, `skill_file()`, `another_boards_write()`, its call in `pre`
before `state_by_hand`, the second probe and the row text in `guard_status`;
`resources/doctor.sh` line 179; the harness
`prds/nothing-left-open/the-skill-tree-is-guarded/probe/verify.sh` at
`41 checks · 41 pass · 0 fail`. Nothing is left to write; the implementer runs
the blocks below and ticks what it ran.

## Acceptance

- [x] hook JSON on stdin — `Edit` of a link `<skills-dir>/pearde/README.md` into this repo, `cwd` a temp project whose `prds/` is a copy of `resources/board/example/prds`, `PEARDE_GUARD_STATE` a temp dir — prints one PreToolUse object with `"permissionDecision": "deny"` whose reason names `/Users/feb/dev/infra/pearde/README.md` (the real path), `prds/memos/the-install-is-live-symlinks.md`, `file a PRD on the skill's own board` and `hand the edit to a session working it`
- [x] the same `Edit` with `cwd` inside this repo prints nothing; with `cwd` a directory with no `prds/` above it prints nothing; an `Edit` of a file under the temp project's own `prds/` prints nothing; a `Write` of `<this repo>/prds/memos/<new>.md` from the temp project prints nothing
- [x] an `Edit` naming the real path under `references/` from the temp project is denied the same way, and the reason names the real path once, without `resolves to`
- [x] a `Bash` command `echo x > <link>` from the temp project is not denied — the caveat `guard.md` states is true
- [x] `python3 resources/guard.py status /Users/feb/dev/infra/pearde` exits 0 and its row ends `· skill tree guarded`; the source holds a `broken` row reading `does not refuse a write into the skill tree from another board`
- [x] `bash resources/doctor.sh` prints a `guard` row `ok` ending `· skill tree guarded`, and `grep -c 'skill tree guarded' resources/doctor.sh` prints `1`
- [x] `bash prds/nothing-left-open/the-skill-tree-is-guarded/probe/verify.sh` prints `41 checks · 41 pass · 0 fail`
- [x] `resources/board/state/guard/` holds no file the harness wrote — every fixture call sets `PEARDE_GUARD_STATE`
- [x] `prds/the-board-runs-itself/the-loop-is-commands/probe/verify.sh` prints `60 checks` with its one pre-existing `FAIL loop.md is 130 lines` and no other; `tokens-per-transition` prints `42 checks · 42 pass · 0 fail`; `guard-on-is-one-command` prints `78 checks` with only its pre-existing `E this repo's settings file was never written` failing

## Verify and Proof

```sh
bash prds/nothing-left-open/the-skill-tree-is-guarded/probe/verify.sh </dev/null
python3 resources/guard.py status /Users/feb/dev/infra/pearde; echo "exit=$?"
PEARDE_GUARD_STATE="$(mktemp -d)" bash resources/doctor.sh | grep '^  guard '
grep -c 'skill tree guarded' resources/doctor.sh
python3 -m py_compile resources/guard.py && echo compiled
bash prds/the-board-runs-itself/the-loop-is-commands/probe/verify.sh </dev/null | tail -1
bash prds/the-board-runs-itself/tokens-per-transition/probe/verify.sh </dev/null | tail -1
bash prds/the-tool-keeps-its-word/guard-on-is-one-command/probe/verify.sh </dev/null | tail -1
```
