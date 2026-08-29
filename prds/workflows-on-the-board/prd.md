---
state: done
origin: requested
priority: 50
complexity: 0
blast-radius:
repo: pearde
footprint:
  - references
  - resources/workflows.py
  - resources/doctor.sh
  - resources/board/plan.py
  - skills/pearde-workflow.md
  - index.md
  - README.md
  - SKILL.md
  - prds/workflows
actual: 4.24h
commit: 7e5250f
---

# workflows-on-the-board — a folder of how-to files a worker is handed, and improves on every run

When this is done, a board carries `prds/workflows/`: markdown files that say
how a kind of job is done. Two kinds of file live there:

| kind         | is                                                                                         | file                                          |
|--------------|--------------------------------------------------------------------------------------------|-----------------------------------------------|
| **atomic**   | one unit of work — what to do, how to tell it worked, how it is known to fail               | `prds/workflows/<slug>.md`, `atomic: <slug>`   |
| **workflow** | an ordered list of atomics — why each is there, and which earlier step to return to when it fails | `prds/workflows/<slug>.md`, `workflow: <slug>` |

A PRD or a spec names one in `workflow:`. The worker's brief then opens with
the workflow expanded — every step with its atomic inlined, one page — so the
worker starts with the route instead of deriving it. When the worker returns,
its report says what each step did, and every failure the atomic caused
becomes an edit to the atomic. The next run starts from the better file.

The board keeps state, memos keep decisions. Nothing keeps the *how* — every
worker re-derives it, and what the last one learned dies with its context.
This folder is where the how accumulates.

## The contract

### Where

- `prds/workflows/`, flat, one file per slug, on the board — the argument
  @references/memo.md makes for memos: on a path the session already walks,
  and `workflow:` on a PRD names a sibling the check can verify.
- `workflows:` in `prds/settings.md` points elsewhere, default `workflows/` —
  several boards share one library, or a master's members share the parent's.
- Nothing under it is a PRD: no `prd.md`, no `state`, never claimed, never
  scheduled. Scan walks past it as it walks past `memos/`.

### The files

- Frontmatter is a closed set, checked: `atomic` or `workflow` (the slug,
  equal to the filename), `subject`, `date`, `updated`, `runs`. Exactly one
  of the two slug keys — the key says the kind.
- An atomic body: `## Do` (numbered, imperative, names commands and files),
  `## Done when` (checks that can fail), `## Fails when` (table: what is
  seen · what it means · what closed it).
- A workflow body: `## Use when`, then `## Steps` as `| # | atomic | why |
  on failure |`. `on failure` is `→ N` with N an earlier step, or `stop`. A
  back-edge is taken at most twice per run; the third failure at one step is
  a stop.
- `runs` counts the runs a file was in — one collect, one count, never the
  traversals inside one run. `updated` moves only when the
  text changed. No log section — git holds the history, the text holds the
  current lesson.
- Written per @references/language.md, in the board language.

### Attached

- `workflow:` on `prd.md` — written by the user, by the drill when it writes
  a tree, or by the orchestrator on `specced` from the analyst's report.
  `workflow:` on a spec overrides it for that unit. Missing: the worker works
  from its brief alone, as today.
- The brief gains one block when a workflow is attached — follow the steps
  in order, go back where the row says, report per step.

### Improved

- The worker report carries `## Workflow <slug>`: per step `passed` /
  `failed → N` / `stopped`, and under `### Edits` the replacement text for
  every failure the atomic caused.
- The orchestrator applies the edits on collect — one writer per file; two
  workers editing one atomic race. In solo mode the orchestrator is the
  worker and writes at the step.
- An edit is from a run, never from reading. A new file may be written by
  the drill or by hand, at `runs: 0`.
- The edit rides the PRD's commit: the commit's paths grow by the workflow
  files touched.

### Read and checked

- `resources/workflows.py` is the only reader: `list`, `show`, `brief`,
  `check`. `doctor` grows a `workflows` row.
- `pearde-workflow` is the skill. `workflow`, `workflow <slug>`, `workflow
  add …`, `workflow attach <prd> <slug>`, `workflow check` are the handles.

## Constraints

- **Nothing names an agent, a tool, a hook or a vendor.** An atomic names
  commands and files. @references/install.md names no agent; a workflow
  names none either.
- The briefs in @references/parts/workers.md stay the contract — verdicts,
  gates, what a worker may write. A workflow orders the how and restates no
  rule of the brief.
- The nine states, the gates, one orchestrator per board — unchanged.
- A workflow is not a persona. A persona is who reads; a workflow is what is
  done. Neither file mentions the other.

## Non-goals

- No workflow engine. The worker reads a page and follows it; nothing runs a
  step for it.
- No search or ranking across the library — `list` and `## Use when` are the
  lookup.
- No sharing mechanism beyond `workflows:` pointing at a directory.

## Children

Work flows to the leaves; this PRD is done when every child is.

| child               | delivers                                                                     | needs                  |
|---------------------|------------------------------------------------------------------------------|------------------------|
| `workflow-format`   | the two shapes, the templates, the format reference                          | —                      |
| `workflow-reader`   | `workflows.py`, the `doctor` row, the `workflows:` setting, the board layout | format                 |
| `workflow-attach`   | `workflow:` in the contract, the brief block, the drill's attachment, the scan line | format, reader   |
| `workflow-improve`  | the report section read at collect, edits applied, `runs`/`updated`, the commit rule | attach          |
| `workflow-skill`    | `skills/pearde-workflow.md`, the handles, every registration                 | reader                 |
| `workflow-seed`     | the first library, written from this repo's own recurring jobs               | format, reader         |

## Pointers

- @references/memo.md · @references/parts/memos.md · @resources/memos.py —
  the precedent: a non-PRD folder on the board, a closed frontmatter set, one
  reader, a `doctor` row.
- @references/parts/workers.md — the briefs the workflow block joins.
- @references/parts/loop.md step 6 — where the edits are applied.
- @references/personas/INDEX.md — the precedent for a registered file kind
  with a fixed format and a `create` path.

## Report

container: every child done — pearde collect closes it

children: workflows-on-the-board/workflow-improve, workflows-on-the-board/workflow-skill, workflows-on-the-board/workflow-format, workflows-on-the-board/workflow-attach, workflows-on-the-board/workflow-seed, workflows-on-the-board/workflow-reader
