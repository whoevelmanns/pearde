---
state: done
origin: requested
actual: 0.42h
commit: 80e3169
priority: 50
complexity: 24
blast-radius: mid
repo: pearde
needs:
  - workflow-format
footprint:
  - resources/workflows.py
  - references/workflow.md
  - references/parts/workflows.md
  - resources/doctor.sh
  - references/parts/doctor.md
  - references/settings.md
  - references/parts/board.md
  - references/files.md
  - index.md
---

# workflow-reader — one reader of the format, and a doctor row

When this is done, `python3 resources/workflows.py check` reports every
problem a malformed library can have, `brief <slug>` prints a workflow as one
page with every atomic inlined, and `doctor` carries a `workflows` row.

## Files

| file                          | change                                                                                        |
|-------------------------------|------------------------------------------------------------------------------------------------|
| `resources/workflows.py`      | new. Python 3 stdlib only. Imports `parse` from @resources/memos.py — one frontmatter parser on the board |
| `resources/doctor.sh`         | a `workflows` row after `memos`, same shape                                                     |
| `references/parts/doctor.md`  | the row in the table, and its bullet                                                           |
| `references/settings.md`      | the `workflows` key: default `workflows/`, relative to `prds/`. Unlike `memos`, a dir elsewhere is not a mirror — it is the library, shared, written by every board's collect |
| `references/parts/board.md`   | `workflows/` in the layout, walked past like `memos/`                                          |
| `references/files.md`, `index.md` | the rows; `workflows.py` joins `@@workflows`                                              |
| `references/workflow.md`      | `## The check`'s bare `resources/workflows.py` becomes `@resources/workflows.py` — the struck box of `workflow-format`'s spec01, carried here because only this PRD puts the file on disk |
| `references/parts/workflows.md` | the reader's four verbs in a `sh` block, the way @references/parts/memos.md carries its own                                              |

## Verbs

| verb                    | prints                                                                                                     |
|-------------------------|-------------------------------------------------------------------------------------------------------------|
| `list [board]`          | `slug · kind · runs · updated · subject`, workflows first, then atomics                                      |
| `show <slug> [board]`   | the file                                                                                                    |
| `brief <slug> [board]`  | the workflow's `## Use when`, then per step its row and the atomic's body under `### N — <atomic>`. One page a worker reads once. Exit 1 when `<slug>` is an atomic — an atomic is shown, not briefed |
| `check [board]`         | one problem per line, silent when clean. Exit 1 on any line                                                 |

`[board]` defaults to `prds/` under the working directory, resolved the way
@resources/memos.py resolves it.

## `check` fails on

- no `---` fence, or one unterminated
- neither or both of `atomic:` / `workflow:`
- the slug disagreeing with the filename
- a required key missing; a key outside the closed set
- `date` not ISO 8601; `updated` before `date`; `runs` not an integer ≥ 0
- an atomic with no `## Do` or no `## Done when`
- a workflow with no `## Steps` table; a row whose `#` is not contiguous from
  1, whose `atomic` names no file in the directory, or whose `on failure` is
  neither `stop` nor `→ N` with N < `#`
- `workflow:` on any `prd.md` or spec on this board naming no workflow file —
  the board half, as `prds:` is checked for memos

A library outside `prds/` (`workflows:` pointing elsewhere) gets the whole
check — it is this contract's, not a foreign system's. A brief with a
dangling atomic is a worker sent nowhere, whichever dir the file lives in.

## The `doctor` row

| part        | `off`            | `broken`                          |
|-------------|------------------|------------------------------------|
| `workflows` | no `workflows/`  | a file fails `check`               |

Not `--fix`-able — what a step should name is its author's to say.

## Verify

- A scratch library holding one clean workflow with two atomics, and one
  file per failure shape above: `check` prints each shape's line exactly
  once, and nothing for the clean files.
- `brief` on the clean workflow prints both atomics' bodies in step order.
- `bash resources/doctor.sh` on this board prints `workflows off` while
  `prds/workflows/` is absent.
- `python3 resources/index.py check` names no line for
  `references/workflow.md` once the anchor is written — the box
  `workflow-format` struck, closed here.
