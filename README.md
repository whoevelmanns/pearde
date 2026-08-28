# pearde — the PRD board

One session orchestrates a board of PRDs — product requirement definitions.
All state is on disk under `prds/` at the repo root. Anything that can read
files, write files, and run commands can work it.

## The workflow

A round is seven steps, run until the board is drained or everything left is
blocked on the user. `once` runs one round. `status` runs step 1 and reports,
changing nothing. Full text: `@@loop`.

| step | command | the orchestrator decides |
|---|---|---|
| 1 scan | `pearde scan` · `pearde sweep` once per session · read `prds/.round.md` · `pearde init` when there is no board | nothing — read |
| 2 answer | `pearde answer <prd> Q<n> "<text>"` per answer | what to put to the user, per @references/drill.md, and what they said |
| 3 refine | `pearde refine <prd> < report` | whether the analyst's table is usable; a drill when it is not |
| 4 spec ahead | `pearde claim <prd> <worker>` · `pearde brief <prd>` → dispatch | which persona the job wears |
| 5 implement | the same two commands | which persona the job wears |
| 6 collect | read the report · apply or refuse `## Workflow` edits · `pearde collect <prd>` | whether to believe the report; whether an edit was the atomic's |
| 7 drill, then stop | one drill round over the frontier · rewrite `prds/report.md` and `prds/.round.md` · `pearde view wait` | the forks and their three answers |

Three rules hold the loop:

- **Collect on the transition, never at the end of the round** — a finished PRD
  still marked `claimed` blocks everything that needs it.
- **The command is the gate** — `specced` reads the spec files, `collect` runs
  the verify blocks, and a `state:` written by hand is what `@@guard` refuses.
- **One writer per file, sequenced between sessions** — a claim another
  session's `prds/.round.md` names is its live work, and `sweep` leaves it.
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
