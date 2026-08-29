---
state: done
origin: requested
actual: 0.5h
commit: f6e2134
priority: 62
complexity: 18
blast-radius: mid
repo: pearde
workflow: probe-then-spec
needs:
  - one-command
  - vision-is-first-class
footprint:
  - resources/board/init.py
  - resources/doctor.sh
  - references/settings.md
  - references/install.md
---

# init-asks-nothing — a board exists after one command, and the first round is one more

When this is done, `pearde init` in any directory leaves a board that `scan`
reads, the daemon watches and `doctor` reports `ok`, and it asked nothing.

## Contract

`pearde init [<dir>] [--language <l>] [--name <n>] [--example]`

| # | does |
|---|---|
| 1 | creates `<dir>/prds/` — default the working directory — and `settings.md` with the five knobs written by name: `language: English` unless `--language`, `workers: 3`, `pipeline: 3`, `weight-default: 50`, `gantt-day: 8h`; `name:` from `--name` when given, else nothing — inferred. Never `members:`, which would make it a master |
| 2 | with `--example`, copies `resources/board/example/prds/` instead — the quickstart's board |
| 3 | writes `prds/vision.md` from @references/templates/vision.md with `terminals:` commented out — a board with no terminals has no axis and orders as today. The template is `vision-is-first-class`'s, which is why this PRD needs it |
| 4 | appends the four machine-local names to `.gitignore` when the directory is a git repo — `prds/.plan.json` `prds/.round.md` `prds/.history.jsonl` `prds/.view.html` |
| 5 | `serve.py ensure` — the daemon up and the board registered, when Python can bind the port; says so and continues when it cannot |
| 6 | `doctor.sh` once, every line printed |
| 7 | prints three lines: the URL, `pearde add "<title>"`, `pearde` |

Idempotent: on an existing board it prints the same three lines and writes
nothing. `memos/` and `workflows/` are not created — a folder appears when the
first file does.

`pearde settings <key>=<value>` writes one key of `settings.md`, preserving
the rest, and replaces `workers=N` and `pipeline=N` as the way any key is set.

## Rules

- **The language is defaulted, and said.** `init`'s first line is `board
  <name> · language English — pearde settings language=<l> changes it`. The
  first round's line says which language it writes in. The decision is
  `prds/memos/init-defaults-the-language.md`, and the sentence "stated by
  the user, never guessed" in @references/settings.md and
  @references/parts/loop.md is replaced by it.
- Loop step 1 on a missing `settings.md` is `pearde init`. No `doctor --fix`,
  no copied block.
- `doctor`'s `board off` line names the fix: `pearde init`, and its `board`
  row no longer reads a missing `language` as broken — a missing key reads
  English, the default @references/settings.md now states.
- Nothing about `init` touches a skills directory. Installing is
  @references/install.md, unchanged.

## Files

| file | change |
|---|---|
| `resources/board/init.py` | new — the seven steps, and `settings` |
| `references/settings.md` | the first-run section is one line; the two new keys from `too-big-splits-itself` are not this PRD's |
| `references/install.md` | the first-run section |
| `resources/doctor.sh` | the fix line; `board` no longer broken on a missing `language` |
| `resources/board/init.py` | registers `init` and `settings` through `COMMANDS` |

## Verify

- In a temp dir under `git init`: `pearde init` → `prds/settings.md` with
  every default key, `.gitignore` holding the four names, the daemon's
  `status` listing the board, `doctor` reporting `board ok`, three lines on
  stdout.
- `pearde init` again → identical three lines, `git status --porcelain`
  unchanged.
- `pearde init --language German` → `language: German`; `pearde settings
  workers=5` → `workers: 5`, every other line byte-identical.
- `pearde init --example` → `scan` prints the example's five sections.

## Report

DONE 9/9 · commit 0f94dd7 · probe 89/89 · 47/47 73/73 39/39 · index silent
