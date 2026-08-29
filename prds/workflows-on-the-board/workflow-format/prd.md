---
state: done
origin: requested
actual: 0.22h
commit: 3f47f16
priority: 50
complexity: 22
blast-radius: mid
repo: pearde
footprint:
  - references/workflow.md
  - references/parts/workflows.md
  - references/templates/atomic.md
  - references/templates/workflow.md
  - references/language.md
  - references/files.md
  - index.md
---

# workflow-format — the two file shapes, written down once

When this is done, a cold reader writes a valid atomic and a valid workflow
from the templates, and @references/workflow.md is the one home of the
format — what @references/memo.md is to memos.

## Files

| file                                | is                                                                                                         |
|-------------------------------------|-------------------------------------------------------------------------------------------------------------|
| `references/workflow.md`            | the format: both frontmatter sets, both bodies, the steps grammar, the report section, the check list, why the board |
| `references/parts/workflows.md`     | the folder on one page — what it holds, when a file is written, the two rejected shapes. `workflow-attach` and `workflow-improve` add their own sections when they land; nothing here stands in for them |
| `references/templates/atomic.md`    | one atomic, commented the way @references/templates/memo.md is                                              |
| `references/templates/workflow.md`  | one workflow, same                                                                                          |
| `references/language.md`            | two rows in the shape table: atomic — a worker, mid-step — a checklist · workflow — a worker, cold — a route |
| `index.md`                          | a `@@workflows` scope: `references/workflow.md` · `references/parts/workflows.md` · the two templates. The skill and the reader join it when they exist |
| `references/files.md`               | one row per file above                                                                                      |

## Atomic

Frontmatter, closed:

| key       | required | is                                                        |
|-----------|----------|------------------------------------------------------------|
| `atomic`  | yes      | the slug — equals the filename without `.md`               |
| `subject` | yes      | one line: the unit of work                                 |
| `date`    | yes      | the day it was written. ISO 8601, written never stamped     |
| `updated` | no       | the day the text last changed from a run                   |
| `runs`    | no       | times followed. Integer ≥ 0, default 0                     |

Body:

| section                          | holds                                                                                   |
|----------------------------------|------------------------------------------------------------------------------------------|
| `# <slug> — <the unit in a phrase>` | the title                                                                             |
| `## Do`                          | numbered imperative steps naming commands and files. Small enough to close in one sitting |
| `## Done when`                   | bullets, each a check that can fail                                                     |
| `## Fails when`                  | table `| seen | means | do |` — what a run hit, what it meant, what closed it. Grows from runs. May be empty at `runs: 0` |

One unit. An atomic that needs "and then" is two.

## Workflow

Frontmatter: `workflow`, `subject`, `date`, `updated`, `runs` — same
meanings, `workflow` the slug.

Body:

| section                           | holds                                                              |
|-----------------------------------|---------------------------------------------------------------------|
| `# <slug> — <the job in a phrase>` | the title                                                         |
| `## Use when`                     | bullets: the jobs this fits, and the near-miss it does not         |
| `## Steps`                        | `| # | atomic | why | on failure |`                                 |

Steps grammar:

- `#` counts from 1, contiguous.
- `atomic` is a slug in the same directory, written `` `<slug>` ``.
- `why` is one clause — what this step buys the job. Never the atomic's
  subject restated.
- `on failure` is `→ N` with N < `#`, or `stop`. No forward jump — a step
  that may be skipped is not a step.
- A back-edge is taken at most twice per run. The third failure at one step
  is `stop`.
- `stop` means report BLOCKED or FAILED per the brief, naming the step.

## The report section

One fixed shape, defined here and never per workflow, in the worker report:

```
## Workflow <slug>

| # | atomic            | outcome              | note                                   |
|---|-------------------|----------------------|-----------------------------------------|
| 1 | read-the-contract | passed               |                                         |
| 2 | reproduce         | failed → 1 · passed  | the fixture named in ## Do does not exist |

### Edits

**<slug>** — `## <section>` — <the replacement text, paste-ready>
```

`outcome` is `passed`, `failed → N`, or `stopped`; a step run twice lists
both, `·` separated. An edit names the file, the section, and the text that
replaces what is there — the orchestrator pastes it or refuses it, and does
not rewrite it.

## Rules this PRD writes down

- **No log.** A lesson is folded into `## Do` or `## Fails when`; `updated`
  moves; git holds what it replaced.
- **No agent, tool, hook or vendor name.** Commands and files.
- **The board language**, per @references/language.md.
- **The roads not taken**, in `references/workflow.md` the way
  @references/memo.md closes with *Why the board, not a docs folder*: a
  `kind:` key beside one slug key — rejected, the slug key already says the
  kind; `atomics/` as a subfolder — rejected, one flat dir found by slug is
  one check; a dated log section — rejected, history lives in version
  control.

## Verify

- `python3 resources/index.py check` is silent after the rows land.
- Both templates parse with `parse` from @resources/memos.py — the dialect
  is the one `prd.md` already uses.
