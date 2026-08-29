---
state: done
origin: requested
actual: 0.9h
commit: 6d47021
priority: 66
complexity: 36
blast-radius: mid
repo: pearde
workflow: probe-then-spec
needs:
  - transitions-are-commands
footprint:
  - resources/board/collect.py
  - references/parts/commits.md
  - references/settings.md
---

# collect-is-a-command — a finished PRD is closed by one call: verify, commit, done

When this is done, the seven mechanical actions of loop step 6 are one call.
The orchestrator reads the worker's report and decides; `pearde collect` does
the rest, and never takes the worker's word for the verify.

## Contract

`pearde collect [<prd>…] [--dry] [--fail] [--widen] [--trust]`

For each PRD named, or every PRD in `scan`'s **collect** section when none is:

| # | does | stops when |
|---|---|---|
| 1 | reads the finished condition off both files — `standing()` in `plan.py` | a box is open: exit 1 naming the file and box |
| 2 | runs every spec's `## Verify and Proof` block in `repo`, captures output and exit code | any non-zero: prints the output, exit 1, writes nothing. `--fail` instead writes the output under `## Failure` and sets `failed` |
| 3 | computes the paths: the union of every spec's `footprint:`, the PRD's own, and the PRD directory. A dirty path outside the union is **inherited** — listed once, never added, per @references/parts/commits.md — unless `--widen <path>` names it as the worker's, and then the message names it too | a dirty path *inside* the union that the PRD's `claim:` predates — the worker wrote onto someone's diff: listed, exit 1, `--widen` to take it |
| 4 | commits those paths with the message of @references/parts/commits.md — subject, one line per spec, `prd:` — one commit per repo the PRD wrote | the tree is clean: nothing to commit is not an error; `commit:` is written as `none` |
| 5 | writes `commit: <sha>`, `actual: <elapsed since claim>`, clears `claim:`, sets `done` | |
| 6 | `POST /report` to the daemon when it is up, the verify output under `## Report` | the daemon is down: says so, continues |
| 7 | prints the progress line, appends the history row | |

`--dry` prints what 3 and 4 would do — the paths it will add, the inherited
paths it will leave — and stops. On this repo today that is 19 inherited files
and no exit 1. `--trust` skips step 2 and
prints `trusted` on the line — for a report whose output the orchestrator has
already read and chosen to believe.

DONE 23/23 · commit 6d47021 · harness 133/133 · 47/47 73/73 39/39

## Rules

- **Never push.** The commit is the board's; the push is the user's.
- **`git add` by path, never `-A`.** The paths are the union above and
  nothing else.
- A `## Workflow <slug>` in the report is the orchestrator's to read and
  apply per @references/parts/workflows.md before it calls `collect`;
  `--also <path>` puts an edited library file on the commit, named in the
  message as `workflow: <slug> — <what the run taught>` from `--also-note`.
- `collect` runs the board's gate before committing — `gate:` in
  `settings.md`, a command, default none, a new key in
  @references/settings.md. This board sets it to the three commands
  `prds/settings.md` § Deliverable already names in prose — `index.py check`,
  `memos.py check`, `doctor.sh`. A red gate is exit 1 and no commit, like a
  red verify; `doctor.sh`'s known `index` line is the baseline, so the gate
  compares against a recorded baseline rather than demanding silence.
- `.round.md` is still the session's. The line says `round file owed`.

## Files

| file | change |
|---|---|
| `resources/board/collect.py` | new — the seven steps |
| `references/parts/commits.md` | opens with the command; the path rules stay as the spec of step 3 |
| `resources/board/collect.py` | registers `collect` through `COMMANDS` |

## Verify

On a copy of the example board under `git init`, with a `repo` that holds a
one-line verify script:

- `collect finished` → one commit whose paths equal the footprint union;
  `prd.md` carries `commit:` and `actual:`; state `done`; the progress line
  printed once;
- the verify made to exit 1 → exit 1, the output printed, `git log`
  unchanged, `prd.md` unchanged; with `--fail` → `failed` and `## Failure`
  holds the output;
- a file dirtied outside the footprint → listed as inherited, not added,
  exit 0; with `--widen <that path>` → committed and named in the message;
  a file inside the footprint whose diff predates the claim → exit 1;
- `collect` with no argument on the copy → one PRD collected, `building` left
  alone;
- `git log -1 --format=%B` matches the message shape of `commits.md` line
  for line.
