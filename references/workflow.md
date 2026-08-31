# Workflows

A PRD says what to build. A memo says what was decided. A **workflow** says
how a kind of job is done, and gets better every time it is followed. The
board keeps state and memos keep decisions; without this folder every worker
re-derives the *how*, and what the last one learned dies with its context.

```
prds/workflows/<slug>.md
```

| kind         | file says      | is                                                                    |
|--------------|----------------|------------------------------------------------------------------------|
| **atomic**   | `atomic: <slug>`   | one unit of work — what to do, how to tell it worked, how it is known to fail |
| **workflow** | `workflow: <slug>` | an ordered list of atomics — why each is there, and which earlier step to return to when one fails |

Exactly one of the two slug keys. The key says the kind, and the filename
equals the slug.

- No `state`. Never claimed, specced, or dispatched.
- `workflows/` holds no `prd.md`, so scan walks past it as it walks past
  `memos/`, and the progress line never counts it.
- One flat directory, no nesting. A file is found by its slug.
- `workflows:` in `prds/settings.md` points elsewhere, default `workflows/` —
  several boards share one library.

A PRD or a spec routes itself by carrying `workflow: <slug>` in its own
frontmatter. The key holds **one slug** — a single scalar naming one file in
the library. Any other shape is a **break, not an absence**: a list, a
mapping, or anything that is not a slug reports exactly as a dangling slug
does, because a key that cannot be read is a route that cannot be taken. A
key that is simply absent is silence, and silence is fine — a PRD needs no
route.

The library does **not** merge. Only the refs do: on a master board the check
crosses into every board named in `members:`, and each slug resolves against
its own board's library first and the master's second — the order `needs:`
resolves in, set by @references/parts/workers.md. The libraries are asked in
turn, never flattened into one set.

## Atomic

Frontmatter, a **closed** set:

```
---
atomic: reproduce-the-failure
subject: turn a reported break into a command that fails on this tree
date: 2026-08-28
updated: 2026-09-02
runs: 4
---
```

| key       | required | is                                                       |
|-----------|----------|-----------------------------------------------------------|
| `atomic`  | yes      | the slug — equals the filename without `.md`              |
| `subject` | yes      | one line: the unit of work                                |
| `date`    | yes      | the day it was written. ISO 8601, written never stamped   |
| `updated` | no       | the day the text last changed from a run                  |
| `runs`    | no       | runs the file was in — one collect, one count. Integer ≥ 0, default 0 |

Body — `@references/templates/atomic.md` is the shape:

| section                             | holds                                                                                     |
|-------------------------------------|--------------------------------------------------------------------------------------------|
| `# <slug> — <the unit in a phrase>` | the title                                                                                  |
| `## Do`                             | numbered imperative steps naming commands and files. Small enough to close in one sitting  |
| `## Done when`                      | bullets, each a check that can fail                                                        |
| `## Fails when`                     | table `\| seen \| means \| do \|` — what a run hit, what it meant, what closed it. Grows from runs. Empty at `runs: 0` |

One unit. An atomic that needs "and then" is two.

## Workflow

Frontmatter, the same closed set with `workflow` as the slug key:

```
---
workflow: fix-a-reported-break
subject: a reported break, from the report to the verified fix
date: 2026-08-28
runs: 0
---
```

Body — `@references/templates/workflow.md` is the shape:

| section                            | holds                                                        |
|------------------------------------|---------------------------------------------------------------|
| `# <slug> — <the job in a phrase>` | the title                                                     |
| `## Use when`                      | bullets: the jobs this fits, and the near-miss it does not    |
| `## Steps`                         | table `\| # \| atomic \| why \| on failure \|`                |

### Steps grammar

- `#` counts from 1, contiguous.
- `atomic` is a slug in the same directory, written `` `<slug>` ``.
- `why` is one clause — what this step buys the job. Never the atomic's
  `subject` restated.
- `on failure` is `→ N` with N < `#`, or `stop`. No forward jump — a step
  that may be skipped is not a step.
- A back-edge is taken at most twice per run. The third failure at one step is
  `stop`.
- `stop` means report BLOCKED or FAILED per the brief, naming the step.

## The report section

One fixed shape, defined here and never per workflow. A worker handed a
workflow carries it in its report:

```
## Workflow <slug>

| # | atomic            | outcome              | note                                      |
|---|-------------------|----------------------|--------------------------------------------|
| 1 | read-the-contract | passed               |                                            |
| 2 | reproduce         | failed → 1 · passed  | the fixture named in ## Do does not exist  |

### Edits

**<slug>** — `## <section>` — <the replacement text, paste-ready>
```

`outcome` is `passed`, `failed → N`, or `stopped`. A step run twice lists both,
`·` separated.

An edit names the file, the section, and the text that replaces what is there
— the orchestrator pastes it or refuses it, and does not rewrite it. An edit
is from a run, never from reading.

## The check

@resources/workflows.py is the only reader of this format, and the `doctor`
row `workflows` is that check. It fails on:

- no `---` fence, or one unterminated
- neither or both of `atomic:` and `workflow:`
- a slug that disagrees with its filename
- a required key missing, or a key nobody declared
- a date that is not ISO 8601, an `updated` preceding its `date`, or `runs`
  that is not an integer ≥ 0
- an atomic with no `## Do` or no `## Done when`
- a workflow with no `## Steps` table
- a step row whose `#` is not contiguous from 1, whose `atomic` names no file
  in the directory, or whose `on failure` is neither `stop` nor `→ N` with
  N < `#`
- `workflow:` on a `prd.md` or a spec naming no **workflow** in the
  library — an atomic is a file, so naming one is this same failure:
  a route was asked for and a single step was found
- `workflow:` on a `prd.md` or a spec holding anything but one slug — a list
  is neither a slug nor an absence, and passing it over makes a broken PRD a
  silent one
- on a master board, either of those on a **member's** PRD or spec, addressed
  `@<member>/<rel>` — the master's check reads its members, or a green
  `workflows` row is evidence only about the master's own PRDs
- a board named in `members:` that is not on disk — a member that cannot be
  read is not a member that is clean

Checked against the real library, never a fixture — a brief with a dangling
atomic is a worker sent nowhere.

## How the text changes

- **No log.** A lesson is folded into `## Do` or `## Fails when`, and
  `updated` moves. Git holds what it replaced.
- **No agent, tool, hook or vendor name.** Commands and files.
- **The board language**, per @references/language.md.
- `runs` counts the runs the file was in, not the traversals inside one — a
  step a back-edge returns to counts once, and so does the atomic it landed
  on. `updated` moves only when the text changed.

## Why the board, and the shapes rejected

`prds/workflows/` is one directory deeper on a path the session already walks
— the argument @references/memo.md makes for `memos/`. A `workflow:` on a PRD
then names a sibling the check can verify.

Rejected:

- **A `kind:` key beside one slug key** — the slug key already says the kind,
  and two fields that must agree are one field that can disagree.
- **`atomics/` as a subfolder** — one flat directory found by slug is one
  check, and a step names a slug rather than a path.
- **A dated log section** — history lives in version control. A file carrying
  its own log grows past the one page a worker reads before starting.
