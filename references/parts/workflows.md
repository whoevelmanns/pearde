# Workflows

How a kind of job is done, kept where the next session looks.

A PRD says what to build and a memo says what was decided. A **workflow** says
how a job is done, and gets better every time it is followed.
@references/workflow.md is the format, the closed frontmatter set, the steps
grammar and the report section.

```
prds/workflows/<slug>.md
```

| kind         | file says          | is                                                |
|--------------|--------------------|----------------------------------------------------|
| **atomic**   | `atomic: <slug>`   | one unit — `## Do`, `## Done when`, `## Fails when` |
| **workflow** | `workflow: <slug>` | `## Use when`, then `## Steps` — an ordered list of atomics with a back-edge per row |

- No `state`. Never claimed, specced, or dispatched — invisible to scan and to
  the progress line, yet on the board.
- One flat directory, one file per slug, no nesting. `workflows:` in
  `prds/settings.md` points elsewhere, default `workflows/`.
- Frontmatter is a **closed set**, and exactly one of the two slug keys.
- `## Do` and `## Done when` are never empty. `## Fails when` is empty until a
  run fills it.

## When a file is written

| moment              | what happens                                                        |
|---------------------|----------------------------------------------------------------------|
| a job repeats       | a new file, by hand or from the drill's tree, at `runs: 0`           |
| a run hits a wall   | the text changes — a lesson folded into `## Do` or `## Fails when`, `updated` moved |

An edit is from a run, never from reading. The text carries the current
lesson; git holds every earlier one.

```sh
python3 @resources/workflows.py list  [board]        # slug · kind · runs · updated · subject
python3 @resources/workflows.py show  <slug> [board] # the file
python3 @resources/workflows.py brief <slug> [board] # the workflow as one page, atomics inlined
python3 @resources/workflows.py check [board]        # what doctor reports for `workflows`
```

`brief` is what a worker is handed: the `## Use when`, then each step's row
with that atomic's body under it, in order — one page read once, instead of
a workflow and N atomics opened one at a time. It exits 1 on an atomic slug:
an atomic is shown, not briefed.

## The two shapes this is not

- **A workflow engine.** Nothing runs a step. A worker reads one page and
  follows it, and `on failure` is a route it walks rather than a handler that
  fires.
- **A searchable index.** No ranking, no tags, no cross-library query. `list`
  and `## Use when` are the whole lookup — a library too large to skim is a
  library of workflows nobody follows.
