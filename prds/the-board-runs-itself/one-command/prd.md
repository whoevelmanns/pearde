---
state: done
origin: requested
actual: 1.1h
commit: 8ad8d79
priority: 70
complexity: 46
blast-radius: mid
repo: pearde
workflow: probe-then-spec
footprint:
  - resources/pearde.py
  - resources/memos.py
  - resources/doctor.sh
  - resources/install.sh
  - skills
  - references/parts/handles.md
  - references/install.md
  - index.md
  - references/files.md
---

# one-command — `pearde` is the whole surface, and every tool is a subcommand of it

When this is done, `python3 resources/pearde.py <cmd>` answers every handle in
@references/parts/handles.md, every skill file names that one line, and a
person learns one word.

## Contract

| `pearde …` | runs today's | notes |
|---|---|---|
| `scan` `plan` `reconcile` `gantt` `calibrate` `status` `members` | `board/plan.py` | argument order unchanged |
| `view` | `board/serve.py ensure` then opens the URL | `view status` · `view stop` · `view wait` pass through |
| `memo list` · `memo check` · `memo add <subject>` | `memos.py` | `add` is new: slug the subject, write from the template, print the path |
| `workflow list` · `show` · `brief` · `check` | `workflows.py` | |
| `questions` | `questions.py check` | |
| `index` | `index.py check` | |
| `doctor [--fix]` | `doctor.sh` | |
| `install [--apply] <dir>` | `install.sh` | |
| `help` | — | one line per command, read from each script's docstring |
| *(none)* | `scan` | the board on one page is the default answer |

`add` `claim` `release` `answer` `defer` `retry` `unblock` `set` `specced`
`refine` `collect` `brief` `sweep` `init` `vision` `settings` arrive with the
children that build them. This PRD reserves the names in `handles.md` and
prints `not yet — <child>` for each until a module claims it.

**Discovery.** `pearde.py` imports every `resources/board/*.py` that exposes
`COMMANDS = {"<name>": <callable>}` and routes by name. A child adds a
module; no child edits the dispatcher. Two modules claiming one name is a
`doctor` failure under `skills`.

## Rules

- **A dispatcher, not a home.** No logic moves into `pearde.py`. It resolves
  the board the way `plan.py find_board` does, forwards the arguments, and
  passes the exit code through.
- **The board argument is optional everywhere** and resolved the same way:
  the nearest `prds/` walking up from the working directory, or the path
  given.
- Python 3 stdlib. `doctor.sh` and `install.sh` stay shell and are called as
  such.
- **The command line is the handle.** `handles.md` gains a third column,
  the exact `pearde` line, and the chat spelling stays as it is. Every
  reserved name gets its row now, marked `pending`; `the-loop-is-commands`
  clears the marks in one edit, so no other child touches the file.
- `install.sh --apply` prints one alias line the reader may add to their
  shell — `alias pearde='python3 <repo>/resources/pearde.py'` — and writes
  nothing outside the skills directory.

## Files

| file | change |
|---|---|
| `resources/pearde.py` | new — the dispatcher and `help` |
| `skills/*.md` | each command block becomes the one `pearde` line |
| `references/parts/handles.md` | the command column |
| `references/install.md` | the alias, one line |
| `resources/install.sh` | print the alias on `--apply` |
| `index.md` · `references/files.md` | rows for the new file; `@@handles` gains it |

## Verify

- For every row of the handles table with a command: `pearde <cmd> --help`
  exits 0.
- `pearde` and `pearde scan` print byte-identical output on the example
  board.
- `pearde help` lists every subcommand once, and no line is longer than 80
  characters.
- `python3 resources/index.py check` silent · `bash resources/doctor.sh`
  reports `skills ok`.
