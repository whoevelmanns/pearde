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
| 1 | **Scan** | `@resources/board/plan.py scan` — the whole board on one page, box counts included. Sweep a dead session's leftovers, check Jira drift and import new tickets when `jira-sync: on` |
| 2 | **Answer** | Put every `question` PRD to the user as one round. Write `## Answers`, set them `open` |
| 3 | **Refine** | Turn an analyst's split into child PRDs. Drill when there is no usable proposal |
| 4 | **Spec ahead** | Dispatch analysts on `open` PRDs until the spec pipeline is full |
| 5 | **Implement** | Dispatch implementers on `specced` PRDs until `workers` is full, skipping footprint clashes |
| 6 | **Collect** | On each finished worker: verify, commit, write the transition, print the progress line |
| 7 | **Drill, then stop** | Nothing dispatchable means blocked on a person: drill the whole open frontier as one round. Report counts and park `wait` only when every question is already out |

Three rules hold the loop:

- **Collect on the transition, never at the end of the round** — a finished PRD
  still marked `claimed` blocks everything that needs it.
- **Never take a worker's word for a transition** — `specced` needs spec files
  on disk, `done` needs verify output actually run.
- **One orchestrator per board** — it is the only writer of PRD state, so there
  is nothing to race and no locking.
- **Read the board with one call, and write down what the call cannot know** —
  the scan is step 1, `prds/.round.md` is the round's own memory across a
  compaction, and a fact established once is cited rather than re-run.
  `@@round`.

## Who does the work

Workers do the work. The orchestrator moves the states — `@@workers` is the
split and the exact brief to hand each one, verbatim, placeholders filled. The
role is what the session does. The persona is who does it — `@@personas`.

A persona is switchable and stored nowhere: the session starts as `engineer`
and `persona <id>` re-aims it — `@@personas`. A worker's is read off one table
in `@@workers` and never asked. The roster is also a set of colleagues the
board calls mid-round on its own judgment — `@@consult`: it puts one problem to
a persona it is not wearing, talks it through, and tells you who it asked and
what they said. `ask <id> <question>` is you starting that conversation.

## Where the rest of the rules live

**One question, one file.** A scope is what a feature is made of, not a
reading list — open the file that answers what is in front of you, and let it
send you on. These are the mid-round lookups, and each is one file:

| the question in front of you | the one file |
|---|---|
| what the round does next | @references/parts/loop.md |
| what a compaction lost | `prds/.round.md`, then `scan`. @references/parts/round.md |
| what to hand a worker, and who it works as | @references/parts/workers.md |
| what a state means, and what moves it | @references/parts/states.md |
| what the progress line prints | @references/parts/progress.md |
| what goes in the commit | @references/parts/commits.md |
| how a PRD's state mirrors onto Jira, and back | @resources/jira/README.md |
| which frontmatter key, and its default | @references/parts/contract.md |
| what a worker's out-of-scope finding becomes | @references/parts/derived.md |
| who works the session | @references/parts/personas.md |
| putting one problem to a colleague | @references/parts/consult.md |

Everything else is a scope, read when its handle fires and not before — the
whole of this table is a book, and a round that opens it reads it again after
every compaction:

| stage | scopes |
|---|---|
| reading the board | `@@board` · `@@states` · `@@order` · `@@derived` · `@@master` · `@@settings` |
| doing the work | `@@workers` · `@@specs` · `@@personas` · `@@consult` · `@@drill` · `@@language` |
| leaving a record | `@@commits` · `@@memos` · `@@progress` · `@@report` |
| working it by hand | `@@handles` · `@@view` · `@@statusline` · `@@install` · `@@doctor` · `@@guard` |

## Addressing

`@<path>` is one file. `@@<keyword>` is one scope. @index.md defines both
syntaxes and names the files behind every keyword. @references/files.md is the
manifest — every tracked file, one row — read when a file is added, never to
work the board.
