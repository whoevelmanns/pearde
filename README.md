# pearde — the PRD board

One session orchestrates a board of PRDs — product requirement definitions.
All state is on disk under `prds/` at the repo root. Anything that can read
files, write files, and run commands can work it.

## The workflow

A round is seven steps, run until the board is drained or everything left is
blocked on the user. `once` runs one round. `status` runs step 1 and reports,
changing nothing. Full text: `@@loop`.

| # | step | what happens |
|---|---|---|
| 1 | **Scan** | Read `prds/settings.md`, parse every `prd.md`, sweep a dead session's leftovers |
| 2 | **Answer** | Put every `question` PRD to the user as one round. Write `## Answers`, set them `open` |
| 3 | **Refine** | Turn an analyst's split into child PRDs. Drill when there is no usable proposal |
| 4 | **Spec ahead** | Dispatch analysts on `open` PRDs until the spec pipeline is full |
| 5 | **Implement** | Dispatch implementers on `specced` PRDs until `workers` is full, skipping footprint clashes |
| 6 | **Collect** | On each finished worker: verify, commit, write the transition, print the progress line |
| 7 | **Stop** | Nothing dispatchable: report counts, name what waits on the user, park `wait` in background |

Three rules hold the loop:

- **Collect on the transition, never at the end of the round** — a finished PRD
  still marked `claimed` blocks everything that needs it.
- **Never take a worker's word for a transition** — `specced` needs spec files
  on disk, `done` needs verify output actually run.
- **One orchestrator per board** — it is the only writer of PRD state, so there
  is nothing to race and no locking.

## Who does the work

Workers do the work. The orchestrator moves the states — `@@workers` is the
split and the exact brief to hand each one, verbatim, placeholders filled. The
role is what the session does. The persona is who does it — `@@personas`.

A persona is switchable and stored nowhere: the session starts as `engineer`
and `persona <id>` re-aims it. The roster is also a set of colleagues the
board calls mid-round on its own judgment — it puts one problem to a persona
it is not wearing, talks it through, and tells you who it asked and what they
said. `ask <id> <question>` is you starting that conversation yourself.

## Where the rest of the rules live

| stage | scopes |
|---|---|
| reading the board | `@@board` · `@@states` · `@@order` · `@@derived` · `@@master` · `@@settings` |
| doing the work | `@@workers` · `@@specs` · `@@personas` · `@@drill` · `@@language` |
| leaving a record | `@@commits` · `@@memos` · `@@progress` |
| working it by hand | `@@handles` · `@@view` · `@@statusline` · `@@install` · `@@doctor` |

## Addressing

`@<path>` is one file. `@@<keyword>` is one scope. @index.md defines both
syntaxes, names the files behind every keyword, and lists every file in the
repo.
