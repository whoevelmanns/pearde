# Frontmatter contract

The keys the tools read, and what happens when one is missing. Every other key
is yours and no tool touches it.

`prd.md`:

| key         | written by                     | read for                                          |
|-------------|--------------------------------|---------------------------------------------------|
| `state`     | orchestrator                   | the loop, the status line                         |
| `priority`  | user                           | **vision importance** — dispatch order, higher first |
| `complexity`| analyst, at spec time          | **weight** — the progress line, `plan`'s ordering. 1-100 |
| `blast-radius` | analyst, at spec time       | **what breaks if it is wrong** — `high` \| `mid` \| `low`. Breaks ties, and decides what a round leads with |
| `est`       | analyst, optional              | the weight of a PRD with no `complexity`. See @references/parts/order.md |
| `actual`    | orchestrator, optional         | a record. The plan never schedules by it; `plan.py calibrate` fits real hours from it |
| `claim`     | orchestrator                   | the sweep, elapsed on `done`                      |
| `repo`      | user                           | the worker brief. Optional                        |
| `workflow`  | user · the drill, on the tree it writes · orchestrator on `specced`, from the analyst's report | the worker brief, `@resources/workflows.py check`, the scan line. A slug in `prds/workflows/`. Optional |
| `needs`     | user                           | a hard gate in `plan`'s order. PRD dir names. Optional |
| `footprint` | user / orchestrator            | the overlap check in step 5, `plan`'s pairwise `after` edges when specs carry none. Paths. Optional |
| `origin`    | whoever creates the PRD        | the split in the progress line, the tripwire in @references/parts/derived.md. `requested` \| `derived` |
| `from`      | orchestrator                   | which PRD's work surfaced a `derived` one         |

`specNN.md`:

| key         | written by | read for                    |
|-------------|------------|------------------------------|
| `complexity`| analyst    | summed into the PRD's `complexity` |
| `footprint` | analyst    | the overlap check in step 5        |
| `workflow`  | analyst    | overrides the PRD's `workflow`, for that unit only |
| `est`       | analyst    | optional. Read as the weight only when `complexity` is absent |
| the file    | analyst · the orchestrator, narrowly | the analyst writes the specs. The orchestrator may add one, and only to close a rule the PRD's own body already states; a requirement the PRD does not make is REFINE and stays the analyst's — `prds/memos/the-orchestrator-may-write-a-spec.md` |

`state` is the only key the loop cannot run without. The rest default:

| missing      | reads as                                                          |
|--------------|--------------------------------------------------------------------|
| `priority`   | 0                                                                  |
| `complexity` | the average of scored PRDs, or `weight-default` if none is scored  |
| `blast-radius` | `mid`                                                            |
| `origin`     | `requested` — saying so is the only way to count as derived        |
| `workflow`   | none — the brief is as it was before workflows existed             |

- Match a key by name, at any indentation, anywhere in the frontmatter — a
  `time:` map holding `est` reads the same as top level. Names are unique
  within one file.
- Writing frontmatter preserves what you did not write — unknown keys, order,
  comments, nesting.

Body sections are contract too: `## Questions`, `## Answers`, `## Failure` in a
PRD; `## Acceptance` and `## Verify and Proof` in a spec. Sections beside them
are yours.
