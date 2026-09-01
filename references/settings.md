# Settings

Every board-wide knob. Per-PRD values — `priority`, `est`, `repo` — live in
each `prd.md`, not here.

The live copy is `.pearde/settings.md`. This file is its template. The skill
folder is shared across installs, so **never write values here** — they leak
into every board.

```yaml
---
language: English
workers: 3
pipeline: 3
weight-default: 50
gantt-day: 8h
context-budget: 100k
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
| `language`    | English      | the language every PRD, spec and report is written in. `pearde init` writes it by name and says so on its first line; `pearde settings language=<l>` changes it — `.pearde/memos/init-defaults-the-language.md` |
| `workers`     | 3            | implementer slots, loop step 5                                    |
| `pipeline`    | 3            | `specced` PRDs kept ahead, loop step 4                            |
| `weight-default` | 50        | weight of an unscored PRD while no PRD on the board has `complexity` |
| `gantt-day`   | 8h           | weight one calendar day represents in the view's `dates` mode. The timeline is decoration; nothing schedules on it |
| `memos`       | `memos/`     | where decision records live, relative to `.pearde/`. Point it at another system's memo dir to mirror it read-only — the strict gate then applies only to the board's own `memos/`, per @references/memo.md |
| `workflows`   | `workflows/` | where the workflow library lives, relative to `.pearde/`. Unlike `memos:`, elsewhere is not a foreign system mirrored read-only — it is **the** library, shared by several boards and written by all of them, so it gets the whole check wherever it sits. @references/workflow.md |
| `harnesses`   | `off`        | run the board's own `verify.sh` harnesses as part of `doctor` — `on` runs them on every `doctor` run, and `doctor --harnesses` runs them whatever this key says. Off by default because the row costs tens of seconds where every other row answers in one. Read by `doctor` alone; no other reader on the board looks at it. @references/parts/doctor.md |
| `members`     | none         | the boards this one merges — `- <path>` or `- <name>: <path>`, relative to `.pearde/`. Present means **master board**: every member's PRDs join the scan as `@<member>/<rel>`, one plan spans them. @references/parts/master.md |
| `gate`        | none         | one command, run in the repo root by `collect` after the specs' verify blocks and before the commit. Red is exit 1 and no commit, like a red verify — measured against the output `claim:` recorded under `.pearde/.claims/<prd>/gate`: a line already there is known, a new line is red. With no record, red is any non-zero exit. @references/parts/commits.md |
| `context-budget` | 100k      | the ceiling on one round's context window, in tokens — `off` removes it, `160k` moves it. Context is billed on every turn, so a window is paid for as many times as the round has turns left; a round that grew past this is cheaper to end and resume from `.pearde/.state/round.md` than to continue. `resources/guard.py` is the only reader: it notes the crossing at 70% and 85%, and at the ceiling refuses everything but the round file, @references/parts/loop.md, @references/parts/round.md and the board's own commands. @references/parts/loop.md |
| `claim-ttl`   | `30m`        | how long a held PRD's files may stand still before its claim is **silent** — the newest mtime over the PRD directory and its footprint union in `repo`, the same union `collect` commits. `30m`, `2h`, `1d`; a bare number is minutes. `plan.py`'s `silent_of` is the one reader; `scan`, the page and `sweep` print and act on its word. @references/parts/view.md |
| `split-above` | 40           | a spec set whose `complexity` sums above this is REFINE, not SPECCED. The analyst brief carries the number as `<split_above>`, and `pearde specced` refuses the set — `over split-above: 58 > 40 — REFINE it` — so a verdict that ignored the brief cannot land. A limit, never a floor: a REFINE under it is still allowed. A master board reads each member's own |
| `specs-above` | 6            | a spec set with more files than this is REFINE, not SPECCED — the same two readers, `<specs_above>` in the brief and `over specs-above: 7 > 6 — REFINE it` from `specced`. A child over either limit is REFINEd in its turn; depth is unbounded |
| `name`        | inferred     | what the board calls itself — the view's title and `/board/<name>` URL. Inferred from the directory on a plain board, from the member names on a master — a placeholder: the first round meeting an unnamed master asks the user and writes it |
| `jira-sync`   | off          | mirror every `state` write onto the matching Jira issue's status. Also needs `JIRA_BASE_URL`/`JIRA_EMAIL`/`JIRA_API_TOKEN` in the environment — either missing, `jira_sync.py` no-ops. `resources/jira/README.md` |
| `jira-projects` | leer       | additive Ergänzung zum aus PRD-Ordnernamen abgeleiteten Projekt-Scope für `jira_sync.py import-new` — Liste oder Komma-Scalar, z. B. `AB, HAMA`. `resources/jira/README.md` |
| `jira-selected-status` | `Selected` | Name des Jira-Status, der als "bereit, nicht begonnen" für `jira_sync.py import-new` gilt — exakter Namensabgleich, nicht `statusCategory`. `resources/jira/README.md` |
| `jira-done-status` | leer/keiner | pro Board überschreibbarer Zielstatus für `done` — überschreibt `STATE_TARGET` nur für dieses Board, nie global. `resources/jira/README.md` |

A key missing from the live copy reads at its default.

**The persona is not here, and there is no key for it.** Who is working is
session state — it starts as `engineer`, is switched by saying so, and ends
with the session. @references/parts/personas.md says why a persisted one is
worse than none. A `persona:` key someone adds by hand is an unknown key like
any other: preserved, and read by nothing.

## Read

Read `.pearde/settings.md` in loop step 1, once per session, and after writing
it.

## Write

The orchestrator is the only writer, same as PRD state.

| case                       | do                                                                    |
|----------------------------|------------------------------------------------------------------------|
| no `.pearde/settings.md`      | first run — `pearde init`, see below                                   |
| `members:` and no `name:`  | ask the user what the group is called, write `name:`, then run the round |
| a board joins or leaves    | append or remove its `members:` entry. Nothing in the member changes   |
| `workers=N` / `pipeline=N` | `pearde settings workers=N`, then run with it                          |
| any other setting stated   | `pearde settings <key>=<value>` — one key written, one line printed    |

First run: `pearde init` — @resources/board/init.py writes `.pearde/settings.md`
with every knob above by name, `language: English` unless `--language <l>`,
and says so on its first line. It asks nothing: the language is a default
that is printed, not a guess, per `.pearde/memos/init-defaults-the-language.md`.

Ask `name` the first time `members:` is read with no `name:`, in the same
round — a group of projects is named for what it owns, not a join of directory
names.

Unknown keys in the live copy are the user's: preserve them, same as PRD
frontmatter.
