# The loop

Eight steps, in order. Run until the board is drained, or everything left is
blocked on the user. `once` = one round. `status` = step 1 plus the progress
report, changing nothing.

**Every step is one command and one decision.** The command checks its gate,
writes the state, prints the progress line and refuses what
@references/parts/states.md forbids. The decision is the right-hand column,
and it is the only thing the round thinks about. Three rules keep it there:

- **Read the board with one call, and read it through the tool.** `pearde
  scan` is step 1 — the whole board on one page, box counts included. Walking
  the tree by hand or opening a `prd.md` for its state is the same information
  at a hundred times the tokens.
- **Write down what the tool cannot know.** `.pearde/.state/round.md`, rewritten at
  every transition — @references/parts/round.md. Context does not survive a
  compaction; that file does. Every command's line ends `round file owed`
  until it is rewritten.
- **An established fact is cited, never re-established.** A count verified at
  12:19 is in the round file with the time on it. Re-running the check buys
  nothing and costs the check.
- **The round has a ceiling.** `context-budget` in @references/settings.md,
  100k by default. Context is billed on every turn, so a window that grew to
  half a million is that much again on the next turn and the one after — the
  board is on disk and the round file is what this session carries, so there
  is nothing in a large window worth paying for twice. The guard notes the
  crossing at 70% and refuses everything but the round file, the steps and
  the board's own commands at the ceiling: write `.pearde/.state/round.md` whole, say
  the round is at its budget, and let the next session resume from it.

Where @references/parts/guard.md is wired, none of this is advice: a
hand-walked board, a board-reading command repeated over an unchanged board,
a third read of an unchanged file and a `state:` written by hand are refused,
and the refusal names the command that answers instead.

| step | command | the orchestrator decides |
|---|---|---|
| 1 scan | `pearde scan` · `pearde sweep` once per session · read `.pearde/.state/round.md` · `pearde init` when there is no board | nothing — read |
| 2 answer | `pearde answer <prd> Q<n> "<text>"` per answer | what to put to the user, per @references/drill.md, and what they said |
| 3 refine | `pearde refine <prd> < report` | whether the analyst's `## Split` table is usable; a drill when it is not |
| 4 spec ahead | `pearde claim <prd> <worker>` · `pearde brief <prd> --worker <worker>` → dispatch as `pearde-analyst` | which persona the job wears |
| 5 implement | the same two commands, dispatched as `pearde-implementer` | which persona the job wears |
| 6 collect | read the returned line · apply or refuse `## Workflow` edits · `pearde collect <prd>` | whether to believe the report; whether an edit was the atomic's |
| 7 knowledge | `python3 resources/knowledge.py query "<the frontier's open question>"` per PRD about to be drilled | whether the record already answers it — cite the note under `## Answers` and skip the question, or let the drill stand |
| 8 drill, then stop | one drill round over the frontier · rewrite `.pearde/report.md` and `.pearde/.state/round.md` · `pearde view wait` | the forks and their three answers |

**1 · Scan.** The sections come out in the pressure order of
@references/parts/order.md — drill, collect, waiting on you, in flight, ready,
gated — and the cut is after `waiting on you`: above it is this round's, below
it is already somebody's. The header names the drill count — `asking N over M
PRDs` — and over one a **drill** section stands first, above *collect*: the
round dispatches nothing past it until it is put (step 2). Open a file only for what the scan does not print, and only when about to act on it. `.pearde/.state/round.md` missing means no round yet. No `.pearde/settings.md` means first run: `pearde init` —
English by default, said on its first line. `master of <n>` with no `name:`:
ask the user and write it. The persona is session state, `engineer` until
switched — @references/parts/personas.md. `jira-sync: on` → see `@@jira`.

`pearde sweep` lists every claim silent past `claim-ttl`
(@references/settings.md) and what `--apply` would do; a claim
`.pearde/.state/round.md` names is a session's live work and stays. Before `--apply`,
read the swept worker's output off the scan: a PRD in **collect** is an
implementer that finished — step 6; `analyzing` with specs on disk is an
analyst that finished — `pearde specced`.
A swept worker's `## Workflow` rows are read with its report: the run happened
whatever the verdict did. A worker its infrastructure killed — API error, lost
network, full disk — is resumed, not swept: it holds the context.

**2 · Answer.** A `## Answers` that grew, or a PRD a person moved in the view,
is the user talking to the board — the view writes those directly. What step 2
puts depends on the count step 1 printed:

| unanswered | step 2 is |
|---|---|
| none | nothing |
| one | that question, put as today |
| two or more | one drill round over all of them per @references/drill.md § The board's own frontier — before step 3, before any claim; the questions already `out` are carried, the rest are put |

While two or more of that round are not yet in `## Asked` nothing is
dispatched: `pearde claim` refuses `asking N — drill first`, and putting them
out is what reopens the board. One standing is not a gate — put it as today
and keep working. Otherwise: put every
`question` PRD and every parked PRD naming a human to the user as one round
per @references/drill.md, each fork with its three prepared answers, through
the ask-user-question mechanism where one exists. A `## Questions` with no
three answers is not askable: write them or send the analyst back. What goes
under `## Answers` is the decision in the user's words — a reply saying the
question was wrong rewrites the round, and `pearde answer` records what was
settled and moves the PRD `open` on the last one. No reply: leave it.

**3 · Refine.** `pearde refine` reads the `## Split` table off the report and
creates the children `open`. No usable table: drill per @references/drill.md
and write that tree through the same command. Never invent a split to keep the
board moving.

**4 · 5 · Spec ahead, implement.** `pearde claim` refuses what is not
dispatchable — held, not a leaf, `needs:` not `done`, a footprint clash with a
`claimed` PRD, a `workflow:` naming nothing — and names the gate; `pearde
brief`, given `--worker <worker>` naming the same worker `claim` just wrote,
runs the same test and prints the brief with the persona off the table in
@references/parts/workers.md — the claim `claim` just wrote is not itself a
refusal when the worker named is the one asking, so the routine dispatch
needs no `--force`. A brief with no `--worker`, or one naming someone else,
still refuses a held PRD exactly as before; `--force` remains the escape
hatch past every gate, for the multi-session case where a PRD is genuinely
someone else's. `pipeline` and `workers` are `settings.md`,
and the scan's **ready** section is the queue in dispatch order. `pearde scan`
marks the PRD's line `wf <slug>?` when its workflow resolves to nothing — the
one refusal you clear yourself: fix the slug or remove the key, then claim in
the same round. `pearde workflow check` names the file, but on a master it
never reaches a member's PRDs. Run `check` on the board the PRD lives on.
`specced` reads a `## Route` on stdin when `## Scores` names a slug the
library does not hold — `--workflow <slug> --route -` — drafts the workflow
and its new atomics at `runs: 0` and runs `workflow check` over the library
before either is kept, refusing the whole call with nothing written on red.
`--workflow none` is refused outright, naming `## Route`.

**6 · Collect.** Results are pushed, never polled: a finished analyst refills
the pipeline, a finished implementer frees a slot. What a worker returns is
one line naming its verdict and its report file — @references/parts/workers.md.
Act on the line. Open `.pearde/prds/<prd>/report.md` only for what the line does not
carry and the transition needs, and never for what a command already parses:
a report read whole is in the window for the rest of the session. The
report's verdict maps to a command in @references/parts/workers.md — SPECCED → `pearde specced`,
REFINE → `pearde refine`, DONE → `pearde collect`, BLOCKED → `pearde release
<prd> blocked`, less → `pearde release <prd> failed` with `## Failure` first,
or answer the worker and let it finish. `collect` runs the verify blocks and
the gate, commits the footprint, writes `done`, posts the report and prints
the line; red is exit 1 and nothing written. Before `done` on work this
session implemented, call the skeptic — @references/parts/consult.md — one
question, on your own judgment; the transition is still yours.

**A report carrying `## Workflow <slug>` followed a route, and the run is what
improves it** — @references/parts/workflows.md. Read the rows: the verdict
decides the transition, and a `stopped` row changes nothing about it.
Apply an edit when the failure was the atomic's.
Refuse it when the failure was the code's or the PRD's, and say which in the
round. The worker wrote the text: paste it or refuse it, never rewrite it.
**`runs` +1** on the workflow and on every atomic that ran, `updated: <today>`
where the text changed — a route `specced` just drafted at `runs: 0` is no
exception: its first collect is `runs: 1` like any other run, and an empty
`## Fails when` is filled by that run for the first time, not left for a
later one. **`pearde workflow check` before the commit.** An edit that
breaks the format is refused, not repaired. The changed files ride the PRD's
commit, `pearde collect --also <path>`. The PRD's own `footprint:` does not change.
**One writer: the orchestrator.** Two workers proposing edits to one atomic
in one round is two collects.

A defect a worker reports outside its scope is the orchestrator's call per
@references/parts/derived.md — a derived PRD or a memo, neither `open` by default.

**7 · Knowledge.** Before a fork is put to the user, query the record for its
question — `python3 resources/knowledge.py query`. A strong hit answers the
question from what is already known: write it straight under `## Answers`, per
step 2, and the fork never reaches the user. A gap or a thin hit changes
nothing — `query` already enqueued the gap into `.pearde/wiki/pending/`, and
the fork still drills at step 8. This step reads the record; it never writes
a `remember` or `conclude` itself — those are a worker's or the user's own.

**8 · Drill, then stop.** Nothing in flight and nothing dispatchable means the
board is blocked on a person: one drill round over the whole open frontier —
@references/drill.md § The board's own frontier — never one per PRD, and never
a question `## Asked` already lists. It is the same drill the scan count starts
when two or more questions stand (step 2), reached here because nothing else
was left rather than because two questions were. Answers land as step 2 lands
them, and the round returns to step 1. Stop when the whole frontier is already
out: report per-state counts, every `question` / `refine` / `failed` PRD with what it
needs, the requested PRDs not `done` with their `complexity`, every `deferred`
derived PRD by name; rewrite `.pearde/report.md` per `@@report` and
`.pearde/.state/round.md`; then park `pearde view wait` so an answer written in the
view wakes the round that acts on it.
