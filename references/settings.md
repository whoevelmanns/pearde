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
plane: auto
---
```

| key           | default      | meaning                                                          |
|---------------|--------------|-------------------------------------------------------------------|
| `language`    | none — asked | the language every PRD, spec, and report is written in            |
| `workers`     | 3            | implementer slots, loop step 5                                    |
| `pipeline`    | 3            | `specced` PRDs kept ahead, loop step 4                            |
| `est-default` | 4h           | weight of an unestimated PRD while no PRD on the board has `est`  |
| `gantt-day`   | 8h           | est-hours one day represents in the Plane Gantt. Lower it to stretch a small board's timeline |
| `plane`       | auto         | `auto` mirrors whenever Plane is reachable, bootstrapping this board on first sight. `off` never mirrors and never reports |
| `memos`       | `memos/`     | where the board's decision records live, relative to `prds/`. Point it at another system's memo dir (`../.mi/docs/memos`) to mirror those read-only — the strict format gate then applies only to the board's own `memos/`, per `references/memo.md` |

A key missing from the live copy reads at its default.

## Read

Read `prds/settings.md` in loop step 1, once per session, and after writing it.

## Write

The orchestrator is the only writer, same as PRD state.

| case                       | do                                                                    |
|----------------------------|------------------------------------------------------------------------|
| no `prds/settings.md`      | first run — see below                                                  |
| `workers=N` / `pipeline=N` | write the key, then run with it                                        |
| any other setting stated   | write it, confirm in one line                                          |

First run:

1. `bash <skill>/doctor.sh --fix` — repair a broken install before the board is
   written.
2. Copy the block above into `prds/settings.md`.
3. Ask the user for `language` — English, German, Spanish, any language,
   stated by the user, never guessed. Write the answer over `<language>`.
4. Ask nothing else. The rest have defaults.

Unknown keys in the live copy are the user's: preserve them, same as PRD
frontmatter.
