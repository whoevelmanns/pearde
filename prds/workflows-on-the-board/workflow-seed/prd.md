---
state: done
origin: requested
actual: 1.1h
priority: 50
complexity: 48
blast-radius: mid
repo: pearde
needs:
  - workflow-format
  - workflow-reader
footprint:
  - prds/workflows
  - references/workflow.md
  - references/templates/atomic.md
  - references/templates/workflow.md
---

# workflow-seed — the first library, written from this repo's own recurring jobs

## Carried here — `runs` means one collect, one count

`workflow-improve` closed an ambiguity that this PRD is the first to meet.
`runs` is described as *"times followed"*, which a back-edge makes two answers:
the improve loop's rule counts **one per collect**, but a step re-entered by
`on failure → N` was literally followed twice. `reproduced` by that PRD's
probe, check `a back-edge does not double-count step 1`.

@references/parts/workflows.md now says one collect, one count. The loose
phrase survives at **four sites across three files**, and this PRD's footprint
has been widened to hold all three: `references/workflow.md:47` and `:147`,
`references/templates/atomic.md:6`, `references/templates/workflow.md:6`.
Correct all four sites to the settled reading.

It is carried here rather than fixed there because an author reading a template
and an orchestrator reading `parts/workflows.md` would otherwise write
different numbers into the same field — and this is the PRD that writes the
first library from those templates.

When this is done, `prds/workflows/` holds enough that the next PRD on this
board is dispatched with a `workflow:` on it, and the improve loop has
something to improve.

## What

- At least three workflows and six atomics. Every atomic is named by at
  least one workflow. Every file stands at `runs: 0`.
- Written from jobs this repo does over and over, and that its references
  already describe step by step — the source is read, the workflow orders
  it, the atomic names the commands:

| workflow                    | the job                                                                                   | the source                                          |
|-----------------------------|--------------------------------------------------------------------------------------------|------------------------------------------------------|
| `add-a-file-to-the-skill`   | a new file under `references/` or `resources/` — the file, its manifest row, its scope, the check | @references/files.md · @index.md              |
| `add-a-contract-key`        | a new frontmatter key — the contract row, the reader, the template comment, the `doctor` row | @references/parts/contract.md · @resources/memos.py |
| `implement-a-spec`          | the implementer's route — read, continue the probe, change, verify scoped, gate, report     | @references/parts/workers.md                         |
| `probe-then-spec`           | the analyst's route — read the contract with its answers, build, hit the wall or not, write specs | @references/parts/workers.md                    |

The four are the candidates. The set is the analyst's at spec time.

## Rules

- A seed restates no rule of a brief. It cites @references/parts/workers.md
  and orders the steps; verdicts, gates and what a worker may write stay
  there.
- Every `on failure` is a back-edge someone would take. `→ 1` on every row
  is a list, not a workflow.
- `## Fails when` may be empty at seed — runs fill it. `## Do` and
  `## Done when` never are.
- No tool, agent, hook or vendor name.
- **Dogfood.** The first PRD dispatched on this board after this lands
  carries `workflow: add-a-file-to-the-skill` or `workflow:
  implement-a-spec`, and its collect is the library's first `runs: 1`.

## Verify

- `python3 resources/workflows.py check prds` silent.
- `python3 resources/workflows.py brief <slug> prds` for each workflow prints
  every step with its atomic under it.
- `bash resources/doctor.sh` prints `workflows ok · N files`.
