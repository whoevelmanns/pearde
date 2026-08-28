# Settings

Every board-wide knob. Per-PRD values — `priority`, `est`, `repo` — live in
each `prd.md`, not here.

The live copy is `prds/settings.md`. This file is its template. The skill
folder is shared across installs, so **never write values here** — they leak
into every board.

```yaml
---
language: <language>
workers: 3
pipeline: 3
weight-default: 50
gantt-day: 8h
---
```

A master board adds its identity and what it merges:

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
| `weight-default` | 50        | weight of an unscored PRD while no PRD on the board has `complexity` |
| `gantt-day`   | 8h           | weight one calendar day represents in the view's `dates` mode. The timeline is decoration; nothing schedules on it |
| `memos`       | `memos/`     | where decision records live, relative to `prds/`. Point it at another system's memo dir to mirror it read-only — the strict gate then applies only to the board's own `memos/`, per @references/memo.md |
| `workflows`   | `workflows/` | where the workflow library lives, relative to `prds/`. Unlike `memos:`, elsewhere is not a foreign system mirrored read-only — it is **the** library, shared by several boards and written by all of them, so it gets the whole check wherever it sits. @references/workflow.md |
| `members`     | none         | the boards this one merges — `- <path>` or `- <name>: <path>`, relative to `prds/`. Present means **master board**: every member's PRDs join the scan as `@<member>/<rel>`, one plan spans them. @references/parts/master.md |
| `gate`        | none         | one command, run in the repo root by `collect` after the specs' verify blocks and before the commit. Red is exit 1 and no commit, like a red verify — measured against the output `claim:` recorded under `prds/.claims/<prd>/gate`: a line already there is known, a new line is red. With no record, red is any non-zero exit. @references/parts/commits.md |
| `name`        | inferred     | what the board calls itself — the view's title and `/board/<name>` URL. Inferred from the directory on a plain board, from the member names on a master — a placeholder: the first round meeting an unnamed master asks the user and writes it |

A key missing from the live copy reads at its default.

**The persona is not here, and there is no key for it.** Who is working is
session state — it starts as `engineer`, is switched by saying so, and ends
with the session. @references/parts/personas.md says why a persisted one is
worse than none. A `persona:` key someone adds by hand is an unknown key like
any other: preserved, and read by nothing.

## Read

Read `prds/settings.md` in loop step 1, once per session, and after writing
it.

## Write

The orchestrator is the only writer, same as PRD state.

| case                       | do                                                                    |
|----------------------------|------------------------------------------------------------------------|
| no `prds/settings.md`      | first run — see below                                                  |
| `members:` and no `name:`  | ask the user what the group is called, write `name:`, then run the round |
| a board joins or leaves    | append or remove its `members:` entry. Nothing in the member changes   |
| `workers=N` / `pipeline=N` | write the key, then run with it                                        |
| any other setting stated   | write it, confirm in one line                                          |

First run:

1. `bash @resources/doctor.sh --fix` — repair a broken install before the board
   is written.
2. Copy the block above into `prds/settings.md`.
3. Ask the user for `language` — stated by the user, never guessed. Write the
   answer over `<language>`.
4. Ask nothing else. The rest have defaults.

Ask `name` the first time `members:` is read with no `name:`, in the same
round — a group of projects is named for what it owns, not a join of directory
names.

Unknown keys in the live copy are the user's: preserve them, same as PRD
frontmatter.
