---
state: done
origin: derived
actual: 0.8h
commit: b8ac8ef
from: the-board-runs-itself/init-asks-nothing
priority: 58
complexity: 13
blast-radius: low
repo: pearde
workflow: probe-then-spec
needs:
  - init-asks-nothing
  - transitions-are-commands
footprint:
  - resources/board/init.py
  - resources/board/transitions.py
  - resources/install.sh
  - references/install.md
  - references/parts/handles.md
  - references/parts/personas.md
  - README.md
  - prds/the-board-runs-itself/readme-in-three-rings/probe/quickstart.sh
  - prds/the-board-runs-itself/readme-in-three-rings/probe/verify.sh
---

# the-next-line-runs — every line a command prints as "run this next" runs as printed

When this is done, a newcomer who types the three lines `pearde init` prints,
or the `add <title>` line `handles.md` shows, gets a PRD — not a refusal
naming a flag they have never heard of.

## The consequence, named

`transitions.py` refuses every transition without `--as <id>` or `PEARDE_AS`
in the environment, on purpose: a defaulted `engineer` after a `persona
skeptic` would rewrite the only record the persona has. `init` then prints
`pearde add "<title>"` as its next line, `handles.md` lists `add <title>`, and
both are refused when typed. Measured by the `readme-in-three-rings` analyst,
2026-08-28, `reproduced`: the quickstart's third line had to become `pearde
add --as engineer "…"` to run. That gets `init-asks-nothing` wrong — "three
next lines printed" — and the README's promise of a board in sixty seconds.

## The shape

The persona is session state, stored on no board file —
@references/parts/personas.md. The environment is exactly that: per session,
gone with it, and what every shell command already reads. So:

- `install.sh --apply` prints two lines to add to the shell: the alias, and
  `export PEARDE_AS=engineer` beside it — the same default the session starts
  as, said once where the session is set up rather than guessed per command.
- `pearde persona <id>` (or the round's own switch) is `export
  PEARDE_AS=<id>`; the round line still carries `· as <id>` from the same
  variable. No file on the board moves.
- With neither `--as` nor `PEARDE_AS`, a command that files a **new** PRD
  (`add`, `init --example`'s copy) reads `engineer` and says so on the line
  — `· as engineer (default)` — a new PRD has no earlier persona line to
  rewrite. Every other transition keeps refusing.
- `init`'s three printed lines and `handles.md`'s rows run as printed; the
  quickstart in the README runs without `--as`.

## Files

| file | change |
|---|---|
| `resources/install.sh` · `references/install.md` | the `export PEARDE_AS=engineer` line beside the alias, once |
| `resources/board/transitions.py` | `add`'s default with `(default)` on the line; the refusal message names `PEARDE_AS` and the install line |
| `resources/board/init.py` | the printed lines run as printed — measured, not restated |
| `references/parts/handles.md` · `personas.md` | the env variable is where the session's persona lives; `persona <id>` sets it |

## Verify

- In a fresh shell with the alias and the export from `install.sh --apply`, the three lines `init --example` prints run in order with exit 0.
- With `PEARDE_AS` unset: `pearde add "x"` files the PRD and its line ends `· as engineer (default)`; `pearde set x analyzing` still exits 1 naming `PEARDE_AS`.
- `readme-in-three-rings`' `probe/quickstart.sh` runs its third line without `--as`.

## Report

DONE 18/18 · commit b8ac8ef · probe 96/96
