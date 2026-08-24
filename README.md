# pearde — the PRD board

One session orchestrates a board of PRDs — product requirement definitions. It
specs them ahead, dispatches implementers on the specced ones, puts blocking
questions to the user, and prints progress on every state change.

All state is on disk: the board is `prds/` at the repo root. Anything that can
read files, write files, and run commands can work it.

| file                            | what                                                        |
|---------------------------------|--------------------------------------------------------------|
| `SKILL.md`                      | entry point where skills are discovered from a directory     |
| `references/system.md`          | the same pointer as a drop-in block for an instructions file |
| `references/install.md`         | what installed means. Not wired up? Start here               |
| `references/drill.md`           | how to ask. Missing, unclear, or the user's call: drill, never guess |
| `references/language.md`        | how to write. Everything on the board follows it             |
| `references/settings.md`        | every board-wide knob. The live copy is `prds/settings.md`   |
| `references/memo.md`            | how a decision is recorded, and why it is not a PRD          |
| `references/templates/prd.md`   | one PRD                                                      |
| `references/templates/spec.md`  | one implementable unit                                       |
| `references/templates/memo.md`  | one decision                                                 |
| `memos.py`                      | reads and checks the memos — the only reader of that format  |
| `doctor.sh`                     | installed, wired, mirroring? `--fix` repairs                 |
| `statusline.sh`                 | renders the progress numbers continuously                    |
| `view/`                         | the live view: planner, service, render, writers. **The view** below |

## Roles

| role             | does                                                        |
|------------------|--------------------------------------------------------------|
| **orchestrator** | works the board. The ONLY writer of PRD state — nothing to race, so no locking. One per board; on a master board it owns every member it merges |
| **analyst**      | turns one `open` PRD into specs, a split, or questions       |
| **implementer**  | turns one `specced` PRD's specs into verified code           |

Workers do the work. The orchestrator moves the states.

## The board

```
prds/
  settings.md       # board settings — references/settings.md
  memos/            # decision records — references/memo.md
    <slug>.md
  <prd-name>/
    prd.md          # frontmatter state + the request
    specs/          # analyst-written, one implementable unit per file
      spec-<name>.md
    <child-prd>/    # a sub-PRD from refine
      prd.md
```

- A directory holding `prd.md` is a PRD; a subdirectory holding its own is a
  child PRD.
- `specs/` and `memos/` hold no `prd.md`, so scan walks past both.
- A parent with children is **not dispatchable** until every child is `done`.
  Work flows to the leaves.

## Master boards

A **master board** merges other boards to plan across projects: one scan, one
wave plan, one timeline, one progress line over several repos.

```yaml
# prds/settings.md, at the master
---
name: master
language: English
workers: 6
pipeline: 4
members:
  - ../mitosys/prds
  - model: ../model/prds
---
```

- `members:` in `settings.md` **is** what makes a master board. Otherwise it is
  an ordinary board: its own PRDs, memos, view.
- An entry is `- <path>` or `- <name>: <path>`. A relative path resolves
  against the master's `prds/`; a path at a repo root gains `/prds`. The name
  defaults to the directory the board sits in; `<name>: <path>` pins it.
- **Nothing moves.** Every member keeps its own `prds/`, `settings.md`,
  `memos/`, view. PRDs, specs and memos are written where they live. The master
  holds only the plan and the progress line.

**Addressing.** A member PRD is `@<member>/<rel>` board-wide —
`@model/nucleus`. A PRD directory is never named `@…`, so a qualified address
cannot collide with the master's own PRDs. Every handle takes it: `run
@model/nucleus`, `needs: @model/nucleus`.

**The master is where you work.** One orchestrator, on the master. It scans
every member, dispatches their workers, and writes each transition into that
PRD's own `prd.md` at its real path — exactly one file per PRD, the member's.
A member session working its own board while a master session works the group
is the forbidden two-orchestrators case.

**Reconcile.** A transition in one member re-orders the whole board:

```sh
python3 <skill>/view/plan.py reconcile [board]   # waves recomputed, anchor kept
```

The live service watches every member and reconciles within about a second.
`plan` re-anchors the schedule on today; `reconcile` only re-orders.

**Across a board boundary:**

| thing                            | scope                                                                                  |
|----------------------------------|-----------------------------------------------------------------------------------------|
| `prd.md`, specs, memos, `state`  | the member. Written where the PRD lives, never at the master                             |
| `needs:`                         | the whole master board. Resolved in the PRD's own board first; across boards it is `@<member>/<prd>`. A bare name matching two boards is ambiguous, reported, and ignored |
| `footprint:`                     | qualified with the member name before any overlap check — two repos touching `src/lib.ts` are not one file. An **absolute** path is left as written, so a deliberate cross-repo overlap still clashes |
| `language`                       | the PRD's own board. The master's is for its own PRDs and the round                      |
| `workers`, `pipeline`            | the master — it is the one dispatching                                                   |
| `est` / `actual` calibration     | the member — one repo's hours do not estimate another's                                  |
| `repo` for a worker brief        | the PRD's own `repo:`, else the member's repo root — the directory holding its `prds/`   |

**Naming.** The first round that meets a master board with no `name:` asks the
user for one and writes it to `settings.md`. Until then the name is inferred
from the members (`mitosys+model`) — a placeholder, not an answer.

**On the master's own board:** only PRDs spanning more than one member. True of
one member alone → it belongs on that member's board.

## Frontmatter contract

Tools read the keys below. Every other key is yours and no tool touches it.

`prd.md`:

| key         | written by                     | read for                                          |
|-------------|--------------------------------|---------------------------------------------------|
| `state`     | orchestrator                   | the loop, the status line                         |
| `priority`  | user                           | dispatch order, higher first                      |
| `est`       | orchestrator, from the analyst | progress line, `~<h>h left`                       |
| `actual`    | orchestrator                   | calibration                                       |
| `claim`     | orchestrator                   | the sweep, elapsed on `done`                      |
| `repo`      | user                           | the worker brief. Optional                        |
| `needs`     | user                           | `plan` wave order. PRD dir names. Optional        |
| `footprint` | user / orchestrator            | the overlap check in step 5, `plan`'s waves when specs carry none. Paths. Optional |
| `origin`    | whoever creates the PRD        | the split in the progress line, the tripwire in **Derived work**. `requested` \| `derived` |
| `from`      | orchestrator                   | which PRD's work surfaced a `derived` one         |

`specNN.md`:

| key         | written by | read for                    |
|-------------|------------|------------------------------|
| `est`       | analyst    | summed into the PRD's `est` |
| `footprint` | analyst    | the overlap check in step 5 |

- `state` is the only key the loop cannot run without. Missing `priority`
  sorts at 0; missing `est` weighs at the board average; missing `origin`
  reads as `requested` — the only way to count as derived is to say so.
- Match a key by name, at any indentation, anywhere in the frontmatter — a
  `time:` map holding `est` reads the same as top level. Names are unique
  within one file.
- Writing frontmatter preserves what you did not write — unknown keys, order,
  comments, nesting.

Body sections are contract too: `## Questions`, `## Answers`, `## Failure` in a
PRD; `## Acceptance` and `## Verify and Proof` in a spec. Sections beside them
are yours.

## States

| state       | meaning                                   | set by                         | leaves via                                    |
|-------------|-------------------------------------------|--------------------------------|------------------------------------------------|
| `open`      | claimable for analysis                    | user / orchestrator            | analyst dispatched → `analyzing`               |
| `analyzing` | analyst working out what to do            | orchestrator                   | analyst returns → `specced` \| `refine` \| `question` |
| `refine`    | needs a sub-PRD split or more detail      | orchestrator (analyst verdict) | children created → `open`                      |
| `question`  | blocked on the user                       | orchestrator (analyst verdict) | answers written → `open`                       |
| `specced`   | specs exist, ready to implement           | orchestrator                   | implementer dispatched → `claimed`             |
| `claimed`   | implementer working it                    | orchestrator                   | returns → `done` \| `failed`                   |
| `blocked`   | work done, boxes waiting on a named event | orchestrator                   | the event lands → `claimed` \| `done`          |
| `done`      | specs implemented and verified            | orchestrator                   | terminal                                       |
| `failed`    | attempt failed, needs revisit             | orchestrator                   | `retry <prd>` → `open`                         |

Never take a worker's word for a transition. `specced` requires spec files on
disk. `done` requires the verify commands actually run with output in the
report — spot-check the cheap ones.

`blocked` vs `failed` — whose problem the open box is:

- `failed` — the attempt did not produce the work. A worker that guessed, or
  whose own checks are red, is `failed`.
- `blocked` — the work is done; a box it cannot close waits on something named.
  Carries `needs:`; the body says which boxes are open and what closes each.
  It is live work — counted in the progress line and the plan, never blindly
  retried.

Never reach for `blocked` to avoid a hard `failed`.

A `state` outside this table is the user's own and **parked**: never
dispatched, never scheduled by `plan`, out of the progress line and the status
line, not folded into `open`. Report parked PRDs by name — neither progress
nor backlog.

## Derived work

- **`origin: requested`** — the user asked for it. The deliverable.
- **`origin: derived`** — the board found it while working.

Derived work is real and often good — and **self-generating**: a gate written
to prove a requested PRD can itself be defective, and its fix grows a gate of
its own. Two rules bound it, both at creation time:

1. **State the consequence for a requested PRD** — which one, and what it gets
   wrong if this is not fixed. A derived PRD that cannot name that is filed
   **`state: deferred`** — parked, per **States**. Not `open`; `open` means
   the board intends to do it.
2. **A defect in an instrument is a memo, not a PRD.** A finding that changes
   no verdict about the deliverable — a check passing too quietly, a narrow
   census — is written per **Memos** and costs no worker.

The test: **would fixing this change what ships, or only how loudly the board
would have noticed?** The first is a PRD. The second is a memo.

**The tripwire.** When open+`analyzing`+`specced`+`claimed` derived PRDs reach
the same count as requested ones, the board is working on itself: stop filing
derived PRDs, report both counts, and put it to the user — continue, defer the
derived tree, or drop it. The trade between a finished deliverable and a
perfect record is the user's.

A derived PRD filed against a derived PRD is the loop feeding on itself: fold
it into the first, or write the memo.

## The loop

Run until the board is drained, or everything left is blocked on the user.
`once` = one round. `status` = step 1 plus the progress report, changing
nothing.

**1. Scan**

- Read `prds/settings.md`. Missing means first run: `bash <skill>/doctor.sh
  --fix`, print every line it printed, create `settings.md` per
  `references/settings.md`, asking the user for the board language.
- `find prds -type f -name prd.md`, parse every frontmatter.
- `members:` means a **master board**: scan every member the same way, address
  its PRDs `@<member>/<rel>`. No `name:` on it: ask the user and write it
  before the round goes on.
- No board: create `prds/`, report it empty, stop.
- Once per session, sweep a dead session's leftovers — `analyzing` with no
  live worker → `open`; `claimed` with no live worker → `failed`. Partial code
  may exist; a human look is cheaper than a blind retry.
- Read the worker's **output** before sweeping. `analyzing` with spec files on
  disk is an analyst that finished: the transition is `specced` with the
  specs' `est` summed, not `open`.

A worker its infrastructure killed — API error, lost network, full disk — is
not a failed attempt:

- Resume THAT worker if it can be resumed — it holds the context, and its
  acceptance boxes are usually empty because the evidence died with it.
- First establish whether the tree is **deliberately** broken: a spec that
  watches a break fail leaves the break applied, and a worker killed in that
  window leaves broken code `claimed` does not hint at.
- Ask the worker which edit was in flight. It knows; the board does not.

**2. Answer**

- A PRD whose `## Answers` grew, or one a person moved in the view, is the
  user talking to the board — the view writes those directly.
- Collect `## Questions` from every `question` PRD; put them to the user as
  one round per `references/drill.md` — the whole frontier, numbered, each
  with your recommended answer. A question depending on one still open waits
  for the next round.
- Write answers under `## Answers`, set those PRDs `open`. No reply: leave
  them `question`, work the rest.

**3. Refine**

- The analyst left the proposed split in its report. Create each child dir +
  `prd.md` (`state: open`, the child's contract as body), set the parent
  `open`.
- No usable split proposal: drill per `references/drill.md`, then write that
  tree as the children. Never invent a split to keep the board moving.

**4. Spec ahead**

While count(*dispatchable* `specced`) < **pipeline** and dispatchable `open`
PRDs exist (leaf, unclaimed, priority desc): mark each `analyzing` +
`claim: <worker> <started>` and dispatch analysts in one parallel batch.

Dispatchable is the same test as step 5 — `needs:` all `done`, no footprint
clash with a `claimed` PRD. A `specced` PRD nobody can be handed is not
pipeline — counting it starves the analyst stage exactly when the board is
most stuck.

**5. Implement**

While count(`claimed`) < **workers** and `specced` PRDs exist: pick by
priority, skip any whose `needs:` are not all `done`, skip any whose footprint
overlaps a `claimed` PRD, mark `claimed` + `claim: <worker> <started>`,
dispatch an implementer.

- Both skips are real work — a footprint clash makes two workers edit one
  file; an unmet `needs:` sends a worker at code its dependency has not
  written.
- A skipped PRD stays `specced`. Say which of the two holds it, so a stalled
  board reads as a queue rather than a bug.
- The footprint is the union of the specs' `footprint:` and the PRD's own.

**6. Collect**

On each finished worker: validate the result (specs on disk / verify output
present), write the transition, write `actual:` on a clean `done` per
**Calibration**, clear `claim:`, print the progress line, post the report with
`POST /report` per **The view**, return to step 2.

A worker reports defects outside its own scope and never fixes them. What each
report becomes is the orchestrator's call, per **Derived work**: a consequence
for a requested PRD → derived PRD with `origin: derived` and `from:`; an
instrument defect → memo; neither is `open` by default. Check the tripwire
before filing.

A finished analyst refills the pipeline; a finished implementer frees a slot.
Do not poll if results are pushed to you.

**7. Stop**

Nothing in flight and nothing dispatchable: report per-state counts, every
`question` / `refine` / `failed` PRD by name with what it needs, and the final
progress line.

- Everything left waiting on the user, and the live service up? Park
  `serve.py wait` in the background before stopping, per **The view** — an
  answer written in the view then wakes the round that acts on it.

Report the two origins separately; name what remains of the **deliverable**
first — requested PRDs not `done`, with `est`. List every `deferred` derived
PRD by name in the same breath, so parking is visible.

## Install check

An install that is present and broken looks exactly like one that is absent.
`doctor.sh` tells them apart:

```sh
bash <skill>/doctor.sh [board]         # report; exit 1 when a part is broken
bash <skill>/doctor.sh --fix [board]   # report, then repair
```

One part per line, each `ok`, `off`, or `broken`; a broken part carries the
command that repairs it. `members` reports only on a master board.

| part         | `off`                                  | `broken`                                                        |
|--------------|----------------------------------------|------------------------------------------------------------------|
| `skill`      | discovered nowhere                     | the skills symlink resolves to no skill folder                   |
| `statusline` | no `statusLine` in the config in force | configured, and its command does not resolve or renders nothing  |
| `board`      | no board                               | off the contract path, or no `language`                          |
| `members`    | not a master board — no `members:`     | an entry that is not a board on disk, or an empty list           |
| `origin`     | no PRDs to read                        | a `derived` PRD with no `from:`, or the **Derived work** tripwire live |
| `memos`      | no `memos/`                            | a memo fails the check in `references/memo.md`                   |
| `view`       | the service is not running             | it runs and this board is not registered                         |
| `plan`       | no plan on record yet                  | —                                                                |

- It reads the config `$CLAUDE_CONFIG_DIR` names, falling back to `~/.claude`
  — a status line wired into the wrong profile is correct and inert.
- `--fix` repairs three things: a missing skill symlink, a dead status-line
  symlink, a view service down or not watching this board. It never writes
  `settings.json` — a missing status line is printed as JSON to paste.
- After repairing, doctor re-checks once — the report and exit code describe
  the state the repairs left behind.

Run it on the first run, on `doctor`, and whenever a part is silent when it
should not be.

## Progress line

Print on EVERY state change:

```
▸ <prd>: <from> → <to> · asked <ad>/<an> · <ap>% · derived <dd>/<dn> · open <o>/<n> · <q>% · ~<h>h left @<w> workers
```

| term       | is                                                                        |
|------------|---------------------------------------------------------------------------|
| weight     | the PRD's `est`; missing counts at the average est of estimated PRDs, `est-default` if none |
| `<ad>/<an>`| `done` / all `origin: requested` — **the deliverable**                     |
| `<ap>`     | Σ est(done, requested) / Σ est(all requested). `failed` counts as remaining |
| `<dd>/<dn>`| `done` / all `origin: derived`. Counts, never est-weighted                  |
| `<o>`      | PRDs still `open`, both origins                                             |
| `<q>`      | `<o>/<n>`. A count — an `open` PRD has no `est` to weight by                |
| `<n>`      | the states in the **States** table only                                     |
| a master   | every member's PRDs and its own, one set; a member's PRD is named `@<member>/<prd>` |
| `~<h>h`    | Σ est(not done) ÷ active workers, both origins — the whole queue            |

- **`asked` is the answer to "how far along are we".** Derived PRDs enlarge
  the denominator with work the user never requested: a board 90% through its
  deliverable reads 63% combined. Report both or neither.
- Omit the `derived` term on a board that has none.
- When the tripwire is live, say so on the line and in the round.
- `<q>` and `<ap>` do not sum to 100 — untouched board vs requested work done.
- A parked PRD is in neither numerator nor denominator; name it in the report.
- `~<h>h left` is an estimate. Label jumps honestly — a refine split moves it
  up.

`statusline.sh` renders the same numbers continuously, plus what the working
tree owes and a link to the board:

```
<dir> <branch> *<dirty> ↑<ahead> ↓<behind> · <model>
▸pearde <ad>/<an> <ap>% · +<dn>d · open <o> <q>% · ▸board
```

- Two rows — sharing one pushes the board off a narrow terminal. No board in
  scope, no second row.
- `<ad>/<an> <ap>%` is requested work only. `+<dn>d` is the derived count,
  suppressed at zero — its job is to stop a derived tree growing unseen.
- `*<dirty>` is uncommitted entries; `↑`/`↓` commits against upstream. No
  upstream reads `no-upstream`, not `↑0`.
- `▸board` is an OSC-8 hyperlink to the live view. `PRD_STATUS_LINK=off`
  prints the label bare. Optional.

## Calibration

`est` is a guess; `actual` is what a run measured.

Write `actual:` on `claimed → done`. Elapsed = now minus the timestamp in
`claim:`, rounded to 5 minutes, in `est`'s units — `45m`, `2h`.

Only when the run was clean:

- one dispatch, `specced` straight to `done`
- DONE returned, every box `[x]`, verify output shown
- no BLOCKED round-trip
- no `## Failure` anywhere in the PRD's history

Anything else leaves `actual:` empty — a retry measures the retry, a BLOCKED
round-trip measures the user's response time, and a wrong number is worse than
none.

Read the record before writing a new `est:`:

```sh
grep -rl 'state: done' prds --include=prd.md \
  | xargs -r grep -H -E '^[[:space:]]*(est|actual):'
```

Scale by the ratio the pairs show. Three pairs at 4h/40m mean the board
estimates 6× high — say so, and estimate at the corrected scale.

## Commits

A PRD that lands is committed on the transition that lands it — otherwise one
working tree ends up holding every PRD's work, and nothing can be reviewed,
reverted, or bisected on its own.

The orchestrator commits. Never a worker — two implementers committing in
parallel write each other's half-finished files into each other's commits.

| transition          | do                                                              |
|---------------------|------------------------------------------------------------------|
| `claimed → done`    | commit                                                           |
| `claimed → blocked` | commit — the work is done, the open boxes wait on something named |
| `blocked → done`    | commit what closing the boxes wrote                              |
| `claimed → failed`  | nothing. Name the dirty paths in the report, leave them on disk  |

Board state written between transitions — answers, a refine split, a memo —
rides the next commit.

**Scope: the footprint, never the tree.** Add the union of the specs'
`footprint:` and the PRD's own, plus the PRD's folder. Never `git add -A`,
never `git commit -a` — step 5 already proved no other `claimed` PRD writes
that footprint.

- **The inherited tree is not the board's.** Step 1 records what is dirty
  before the round starts; those paths are never added, whatever footprint
  they fall in. Name them once in the round.
- **A path the worker wrote outside its footprint is a wrong footprint.**
  Commit it with the rest and say so.

**Gate first.** Commit only what the `done` gate passed: verify output in the
report, every box `[x]`, spot-checks run. A red tree is a `failed` PRD, and a
`failed` PRD does not commit.

**Message.** Subject `<prd> — <what landed>`, one line per spec, `prd:` naming
the folder:

```
<prd> — <the PRD's contract in one line>

<specNN>: <goal>
<specNN>: <goal>

prd: prds/<path>
```

Write the sha to `commit:` on the PRD, beside `actual:` — the only link from a
`done` PRD to its code, and where `retry` on a regression starts.

**One commit per repo the PRD wrote.** A PRD with `repo:` elsewhere writes
code there and its record on the board: commit each where it lives, same
subject. On a master board that is the member's repo.

**Never push.** The commit is the board's, the push is the user's. Report what
is ahead and stop.

`commits: off` in `prds/settings.md` holds all of it — each transition then
names its dirty footprint. While on, a `*<dirty>` count climbing across rounds
is a board whose commits are not landing.

## Worker briefs

Give each worker exactly its brief with the placeholders filled in. `<skill>`
is this folder's path.

Rules for every worker:

- Never edit frontmatter, never touch other PRDs, never write outside the PRD
  folder. Implementers also write the target repo.
- Write per `references/language.md`, in the board `language` from
  `prds/settings.md` — named in the brief. On a master board, the language of
  the PRD's **own** board.
- Give a member's worker real paths, never `@<member>/…`. `repo` is the PRD's
  own, else the member's repo root.
- A report that is incomplete, or a worker stopped mid-task: continue THAT
  worker — it holds the context. Never respawn it.
- Report a defect found outside your scope; do not file it and do not fix it.
  Say what is wrong, what you measured, and which requested PRD it would get
  wrong. The orchestrator decides what it becomes, per **Derived work**.

**Analyst** — one per `open` PRD being specced:

> Read `prds/<prd>/prd.md`, including `## Answers`, and explore `<repo>` as
> needed. Return exactly one verdict:
>
> - **SPECCED** — write `specs/specNN.md` files, template
>   `<skill>/references/templates/spec.md`, each one implementable unit: goal,
>   `est:` and `footprint:` in frontmatter, `- [ ]` acceptance boxes a check
>   can fail, and a verify command. Calibrate `est` against the `est`/`actual`
>   pairs of done PRDs on the board. Report the spec list, the total `est` in
>   hours, the ratio you calibrated by, and the union of the footprints.
> - **REFINE** — the PRD holds more than one contract, or is too thin to spec.
>   Report the proposed children, `<dir-name> — one-line contract` each, and
>   what detail is missing.
> - **QUESTION** — a real fork only the user can settle: naming, scope, cost.
>   Never a fact you could look up — find facts yourself. Write `## Questions`
>   into `prd.md` in the round format of `<skill>/references/drill.md` and
>   report them.
>
> Spec what this PRD asks for. A wrong claim you find elsewhere, or a check
> that could not fail, goes in your report as a finding — not into a spec, and
> not into a new PRD. Widening the contract is REFINE, not initiative.

On return: SPECCED → confirm the spec files exist, write `est:`, set `specced`.
REFINE / QUESTION → set the state, keep the report.

**Implementer** — one per `specced` PRD dispatched:

> Read `prds/<prd>/prd.md` and every file in `specs/`. Implement the specs in
> `<repo>`. Run each spec's `verify:` command and the repo's own gate. Tick a
> box `[x]` only for a check you actually ran, quoting output. If blocked, STOP
> and report **BLOCKED** with the exact question or wall — do not guess, do not
> redefine the spec. Return **DONE** (per-spec box status + verify output) or
> **FAILED** (what broke, what you tried); on FAILED also write `## Failure`
> into `prd.md`.

On return:

| report                                                                          | set                                    |
|---------------------------------------------------------------------------------|----------------------------------------|
| DONE, every box ticked, verify output shown                                      | `done`                                 |
| DONE, open boxes waiting on something named, everything the worker owns proven   | `blocked` + `needs:`                   |
| anything less                                                                    | `failed`, or answer a BLOCKED worker and let it finish |

Two unclosable boxes to catch when the specs land:

- A box asking for a **commit message** — committing is not an implementer's
  act.
- A `verify:` running the **whole workspace** — it measures the tree's worst
  neighbour, not this node's work.

A spec asking to change **another** PRD's body is the orchestrator's edit on
that transition. The worker reports the wording — one writer per file holds.

## Without parallel workers

Run the same loop single-file: scan → answer → refine → pick the
highest-priority actionable PRD → run its brief yourself as a checklist
(analyst for `open`, implementer for `specced`) with the transitions before
and after → print the progress line → repeat. Effectively `workers=1`,
`pipeline=1`. Every rule holds: one writer, verify before `done`, work flows
to the leaves.

## Memos

A PRD says what to build; a **memo** says what was decided and what it beat,
and outlives the work it governed. `references/memo.md` is the format and the
argument.

```
prds/memos/<slug>.md
```

- No `state`. Never claimed, specced, or dispatched; invisible to scan and the
  progress line — yet on the board, where the next session looks.
- Frontmatter is a **closed set** (`memo`, `kind`, `status`, `subject`, `date`
  required; `updated`, `prds`, `supersedes`, `superseded_by` optional).
  Anything else fails `doctor` — the one inversion of the frontmatter
  contract, because the memo table is a fold over declared keys.
- Body per `references/templates/memo.md`: Decision, Why, **Alternatives
  considered** (never empty — a memo with no alternatives is a claim),
  Consequences.

```sh
python3 <skill>/memos.py list [board]    # slug · kind · status · date · subject
python3 <skill>/memos.py check [board]   # what doctor reports for `memos`
```

Write one when a call is made that the code will not explain: a rule the board
follows, a road not taken, a constraint that looks arbitrary. Not for what a
commit message covers.

Decisions recorded in another system stay there: `memos: <dir>` in
`prds/settings.md` reads that dir read-only; the strict gate applies only to
the board's own `memos/`.

## Handles

The spelling follows the setup — `/pearde status` where commands take
arguments, "pearde status" in plain chat. The meanings are fixed.

| Want                         | Say                                                                                                      |
|------------------------------|-----------------------------------------------------------------------------------------------------------|
| report only, change nothing  | `status`                                                                                                 |
| one round, then stop         | `once`                                                                                                   |
| more implementers            | `workers=5` — written to `prds/settings.md`, persists                                                    |
| deeper spec pipeline         | `pipeline=5` — written to `prds/settings.md`, persists                                                   |
| new PRD                      | `add <title>` — dir + `prd.md` from `references/templates/prd.md`, `state: open`, `origin: requested`    |
| park a derived PRD           | `defer <prd>` — `state: deferred`, per **Derived work**                                                  |
| work out what is wanted      | `drill <prd>` — interview per `references/drill.md`; with no `<prd>`, into a new tree                    |
| retry a failed PRD           | `retry <prd>` — moves `## Failure` into the body as history, sets `open`                                 |
| a blocked PRD's event landed | `unblock <prd>` — re-runs only the open boxes; `done` when they close                                    |
| run one PRD to done          | `run <prd>` — the loop scoped to that PRD's subtree                                                      |
| record a decision            | `memo <subject>` — `prds/memos/<slug>.md` from `references/templates/memo.md`                            |
| pre-plan parallel waves      | `plan` — `view/plan.py plan`; print the waves it returns                                                 |
| the local timeline           | `gantt` — `view/plan.py gantt --open`: the plan as `prds/.view.html`, x = distance to the vision         |
| open the board               | `view` — `view/serve.py ensure`, then the URL it prints                                                  |
| plan across projects         | `master <path> …` — writes `members:` in `prds/settings.md`, asks the group's `name:` the first time. This board is then the parent every round works in |
| what a master merges         | `master` with no path — `view/plan.py members`: every member, its path, `MISSING` when not on disk       |
| stop merging one             | `master drop <name>` — removes that `members:` entry. Nothing in the member changes                      |
| re-order after a member moved| `reconcile` — `view/plan.py reconcile`: waves recomputed, anchor kept. The live service already does it  |
| is this thing wired?         | `doctor` — `doctor.sh --fix`, per **Install check**; print every line                                    |

- `add` is the user asking, so `origin: requested`. Only the orchestrator
  writes `origin: derived`, and only with `from:` — see **Derived work** for
  what must be true before it is filed `open` rather than `deferred`.
- `master <path>` takes one or more paths, each a board or a repo holding one,
  and appends them to `members:`. It creates nothing in the member and moves
  no file. Print what the merged board now holds: member count, PRD count, the
  plan `reconcile` produced.
- `memo <subject>` slugs the subject — lowercase, spaces to hyphens. The slug
  is both the filename and the `memo:` key; `doctor` fails if they disagree.
  Write the memo when the call is made, not when the work lands.
- `add` takes the title as written; a one-line title is too thin to spec, so
  the analyst returns REFINE or QUESTION. `drill` settles it first: it runs
  `references/drill.md` to completion and leaves a tree the loop picks up —
  settled contract as the body, each branch a child dir, `state: open`.
  Dispatch nothing while a drill is running.

`run <prd>` filters the board to that PRD and its children:

- Scan still parses everything, for the sweep and the progress line, but only
  PRDs inside `prds/<prd>/` change state.
- The user named it, so a `failed` target or child is reopened first, as
  `retry` would.
- A `done` target is reported and left alone. No match: list the near-misses,
  change nothing.
- The run ends when the subtree is drained — report the target's final state —
  or everything left in it is blocked on the user.

One orchestrator per board. On start, fresh `analyzing` / `claimed` claims you
did not make may be another session's live workers: say so and run `status`
only. Never sweep another live session's claims.

## The view

The board is files; the view is how a person reads and works them. Once per
machine:

```sh
python3 <skill>/view/serve.py ensure     # start if needed, register this board
```

From then on `http://127.0.0.1:8443/board/<name>` is the board, live — within
a second of any file changing it swaps the new payload in **where it stands**:
the rows move, and scroll, zoom, selection and half-typed text do not. Every
registered board is listed at `/`. `PEARDE_PORT` moves the port.

| view          | answers                                                        |
|---------------|------------------------------------------------------------------|
| **timeline**  | what is in front of us — see below                                |
| **board**     | what is where — kanban by state; drag a card to write `state:`    |
| **asks**      | what is waiting on *you* — every `question` and `blocked` PRD, the question as written, and the box that answers it |
| **list**      | all of it — sortable, filterable, one row per PRD                 |
| **analytics** | how this is going — where the work and hours sit, estimates vs reality, hours left over time |
| **memos**     | what the board decided — `prds/memos/`, rendered                  |

**Every number is a door.** A count, a swatch, a bar, a column head — if it
names a set of PRDs, clicking it goes there: `5 waiting on you` opens **asks**,
`189h to the vision` filters the timeline to the critical chain, `137 done`
opens that list, a legend swatch filters by state. Nothing on the page is a
dead end, and the URL follows, so where you are is a link you can send.

**The timeline's x axis is not time** — agents start when work is
dispatchable, so a date on a bar is a staffing guess; the dependency structure
is not. The axis is est-hours along the **critical path**: zero at now, the
right edge the vision reached.

- **★ critical** marks the chain that sets the finish — an hour cut there
  moves the vision closer; anywhere else, nothing.
- **float** is the tail behind a bar: how late it may start before it becomes
  critical.
- **ready now** is the frontier at zero, ordered by how much work each PRD
  unblocks. That ordering *is* the dispatch order.
- **wave bands** are the plan's rounds — a wave runs after the one before it,
  because that is what a footprint clash means.
- The header names the **peak agent count** the fastest path asks for, beside
  what `workers` costs instead. The gap is the decision.
- **dates** (or `v`) draws the same bars on the worker-limited calendar, at
  `gantt-day` hours per day.

The chart is one canvas, drawn virtualised — only the rows in front of you
cost anything, so a 40-PRD board and a 4000-PRD one draw the same. Drag to
pan, ctrl/⌘+wheel to zoom at the pointer, drag the column edge to widen the
names, `↑↓` to move the selection, `⏎` to open it, ⌘1–6 for the views.
Greyscale carries the plan — state is ink weight, not hue — and the only
colour on the page is the amber and red of the states that want a person.

**Clicking anything opens the PRD**, and the pane writes back: title, `state`,
`priority`, the body, a note appended to `## Notes`, and — on a `question` PRD
— an answer box that writes `## Answers` and sets it `open`. The **asks** view
is that same answer box for every waiting PRD at once (⌘⏎ sends), so the board
can be unblocked without going looking for what blocked it. `+ PRD` (or `n`)
writes a new one. Every write goes through `view/edit.py`: one line at a time,
atomically, frontmatter and body never in the same write. Workers' reports
land via `POST /report` (`{"board","prd","text"}` → `## Report`).

Deep links: `#prd=<rel>` opens one PRD, `#view=asks` a view, `#state=blocked` a filtered list, `#crit=1` the critical chain.

```sh
python3 <skill>/view/plan.py plan         # the waves, to stdout
python3 <skill>/view/plan.py reconcile    # re-order them, keep the anchor
python3 <skill>/view/plan.py gantt --open # the same view as one HTML file
python3 <skill>/view/plan.py status       # the board, its members, its memos
python3 <skill>/view/serve.py wait        # block until the board moves
```

`gantt` writes `prds/.view.html` — the same render, self-contained, no service
needed. It loses only what needs the service: the detail pane's live read and
every edit.

**Being woken, not polling.** `serve.py wait` sleeps in the kernel and exits
the moment anything on the board moves, printing what did. Park it in the
background at session start, and whenever a round ends with work still open.

**What the board keeps.** `prds/.plan.json` is the last plan;
`prds/.history.jsonl` is one row a day — the only memory the board has, what
the burn-down draws. Machine-local and regenerable; gitignore them:

```
prds/.plan.json
prds/.history.jsonl
prds/.view.html
```
