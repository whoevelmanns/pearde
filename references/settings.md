# Settings

Every board-wide knob. Per-PRD values — `priority`, `est`, `repo` — live in
each `prd.md`'s frontmatter, not here.

The live copy is `prds/settings.md` on the board; this file is its template.
The skill folder is shared across installs, so **never write values here** — a
value written here leaks into every board.

```yaml
---
language: <language>
workers: 3
pipeline: 3
est-default: 4h
gantt-day: 8h
---
```

A master board adds two keys — its identity, and what it merges:

```yaml
---
name: master
members:
  - ../mitosys/prds
  - model: ../model/prds
---
```

| key           | default      | meaning                                                          |
|---------------|--------------|-------------------------------------------------------------------|
| `language`    | none — asked | the language every PRD, spec, and report is written in            |
| `workers`     | 3            | implementer slots, loop step 5                                    |
| `pipeline`    | 3            | `specced` PRDs kept ahead, loop step 4                            |
| `est-default` | 4h           | weight of an unestimated PRD while no PRD on the board has `est`  |
| `gantt-day`   | 8h           | est-hours one calendar day represents in the view's `dates` mode. Lower it to stretch a small board's timeline |
| `memos`       | `memos/`     | where the board's decision records live, relative to `prds/`. Point it at another system's memo dir (`../.mi/docs/memos`) to mirror those read-only — the strict format gate then applies only to the board's own `memos/`, per `references/memo.md` |
| `members`     | none         | the boards this one merges — `- <path>` or `- <name>: <path>`, one per line, relative to `prds/`. Present means this is a **master board**: every member's PRDs join the scan as `@<member>/<rel>`, and one plan spans them. README, **Master boards** |
| `name`        | inferred     | what the board calls itself — the view's title and its `/board/<name>` URL. Inferred from the directory on a plain board and from the member names on a master (`mitosys+model`), which is a placeholder: the first round that meets an unnamed master board asks the user and writes the answer here |

A key missing from the live copy reads at its default.

## Read

Read `prds/settings.md` in loop step 1, once per session, and after writing it.

## Write

The orchestrator is the only writer, same as PRD state.

| case                       | do                                                                    |
|----------------------------|------------------------------------------------------------------------|
| no `prds/settings.md`      | first run — see below                                                  |
| `members:` and no `name:`  | a master board nobody named: ask the user what the group is called, write `name:`, then run the round |
| a board joins or leaves    | append or remove its `members:` entry. Nothing in the member changes — that is the whole join |
| `workers=N` / `pipeline=N` | write the key, then run with it                                        |
| any other setting stated   | write it, confirm in one line                                          |

First run:

1. `bash <skill>/doctor.sh --fix` — repair a broken install before the board is
   written.
2. Copy the block above into `prds/settings.md`.
3. Ask the user for `language` — English, German, Spanish, any language,
   stated by the user, never guessed. Write the answer over `<language>`.
4. Ask nothing else. The rest have defaults.

`name` is the second thing ever asked, and only on a master board: a group of
projects is named for what it owns, and a join of directory names is not that.
Ask it the first time `members:` is read with no `name:` beside it — one
question, in the same round, then carry on.

Unknown keys in the live copy are the user's: preserve them, same as PRD
frontmatter.
