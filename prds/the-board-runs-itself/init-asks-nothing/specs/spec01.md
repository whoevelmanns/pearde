---
complexity: 12
workflow: add-a-file-to-the-skill
footprint:
  - resources/board/init.py
  - prds/the-board-runs-itself/init-asks-nothing/probe/
  - references/files.md
  - index.md
---

# spec01 — `init` and `settings` land as `resources/board/init.py`, and the map points at it

The probe built the whole command: `prds/the-board-runs-itself/init-asks-nothing/probe/init.py`
is the module, written at the shape `resources/board/` expects — it imports
`edit` and `plan` from beside itself, calls `serve.py` beside itself and
`doctor.sh` one level up, and exposes `COMMANDS = {"init": …, "settings": …}`.
The harness beside it runs the module from an isolated copy of `resources/`
on a spare port and prefers the landed path once it exists. This unit moves
the file to where the dispatcher discovers it and writes the two rows the map
needs; nothing in the module is left to write.

## What stands from the probe

- `probe/init.py` — 89 checks pass in `probe/verify.sh`: the five keys by
  name, `vision.md` from the template, the four names in `.gitignore` only
  inside a git repo, `ensure` on the isolated daemon, `doctor` printed,
  the three closing lines, idempotence, `--language`, `--name`, `--example`,
  the daemon-down path, every `settings` refusal, and `pearde.py` discovery.
- `references/settings.md` already anchors `@resources/board/init.py` — the
  one line `python3 resources/index.py check` prints today, red until the
  file and its manifest row exist.

## What is left

1. `git mv prds/the-board-runs-itself/init-asks-nothing/probe/init.py resources/board/init.py`.
   The harness stays in `probe/` and now tests the landed file.
2. One row in `references/files.md` under `resources/board/`, beside
   `transitions.py`: `| @resources/board/init.py | \`init\` and \`settings\` — a board after one command, no question; one key of settings.md |`.
3. `index.md`: add `@resources/board/init.py` to the `@@settings` row and to
   the `@@board` row — a reader asking how a board starts finds the command.
4. `python3 resources/pearde.py help` shows `pearde init` and `pearde settings`
   with their docstring lines and no `not yet — init-asks-nothing`.

## Acceptance

- [x] `resources/board/init.py` exists, `probe/init.py` does not, and `bash prds/the-board-runs-itself/init-asks-nothing/probe/verify.sh` ends `89 checks · 89 pass · 0 fail`
- [x] `python3 resources/pearde.py help` prints a `pearde init` line and a `pearde settings` line and no line containing `not yet — init-asks-nothing`; stderr is empty
- [x] `python3 resources/index.py check` prints nothing
- [x] `grep -c 'resources/board/init.py' references/files.md` is `1`, and `grep -c 'resources/board/init.py' index.md` is at least `2`

## Verify and Proof

```sh
bash prds/the-board-runs-itself/init-asks-nothing/probe/verify.sh | tail -1
python3 resources/pearde.py help 2>&1 | grep -E 'pearde (init|settings)|not yet — init|^pearde:'
python3 resources/index.py check                       # reads references/files.md and index.md — silent is green
grep -c 'resources/board/init.py' references/files.md index.md
```
