# pearde — the PRD board

One session orchestrates a board of PRDs — product requirement definitions. It
specs them ahead, dispatches implementers on the specced ones, puts blocking
questions to the user, and prints progress on every state change.

All state is on disk. Anything that can read files, write files, and run
commands can work the board. The board is `prds/` at the repo root.

| file                            | what                                                             |
|---------------------------------|------------------------------------------------------------------|
| `SKILL.md`                      | entry point where skills are discovered from a directory         |
| `references/system.md`          | the same pointer as a drop-in block, where instructions are read from a file |
| `references/install.md`         | what installed means. Not wired up? Start here                   |
| `references/drill.md`           | how to ask. Missing, unclear, or the user's call: drill, never guess |
| `references/language.md`        | how to write. Everything on the board follows it                 |
| `references/settings.md`        | every board-wide knob. The live copy is `prds/settings.md`       |
| `references/memo.md`            | how a decision is recorded, and why it is not a PRD              |
| `references/templates/prd.md`   | one PRD                                                          |
| `references/templates/spec.md`  | one implementable unit                                           |
| `references/templates/memo.md`  | one decision                                                     |
| `memos.py`                      | reads and checks the memos — the only reader of that format      |
| `doctor.sh`                     | installed, wired, mirroring? `--fix` repairs                     |
| `statusline.sh`                 | renders the progress numbers continuously                        |
| `view/`                         | the board as a live view — the wave planner, the service that watches, the render, and the writers. **The view** below |

## Roles

| role             | does                                                        |
|------------------|-------------------------------------------------------------|
| **orchestrator** | works the board. The ONLY writer of PRD state — nothing to race, so no locking. One per board, and on a master board that one owns every member it merges |
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

- A directory holding `prd.md` is a PRD.
- A subdirectory holding its own `prd.md` is a child PRD.
- `specs/` and `memos/` hold no `prd.md`, so scan walks past both.
- A parent with children is **not dispatchable** until every child is `done`.
  Work flows to the leaves.

## Master boards

A **master board** merges other boards into one. It exists to plan across
projects: one scan, one wave plan, one timeline, one progress line over several
repos.

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
  - ../realm/prds
---
```

- A board whose `settings.md` carries `members:` **is** a master board. Nothing
  else marks one, and it is otherwise an ordinary board: it can hold its own
  PRDs, its own memos, its own view.
- An entry is `- <path>` or `- <name>: <path>`. A relative path resolves
  against the master's `prds/`; a path at a repo root gains `/prds`.
- The name defaults to the directory the board sits in — `realm/prds`
  is `realm`. Write `<name>: <path>` to hold a name against a move.
- **Nothing moves.** Every member keeps its own `prds/`, `settings.md`,
  `memos/` and its own view. PRDs, specs and memos are written
  where they live.
- What lives at the master: the plan, the merged mirror, the progress line.

**Addressing.** A member PRD is `@<member>/<rel>` board-wide — `@model/nucleus`,
`@mitosys/gate/child`. The sigil is what makes one flat namespace safe: a PRD
directory is never named `@…`, so a qualified address can never collide with
one of the master's own PRDs. Every handle takes it: `run @model/nucleus`,
`retry @model/nucleus`, `needs: @model/nucleus`.

**The parent is where you work.** One orchestrator, on the master. It scans
every member, dispatches their workers, and writes each transition into that
PRD's own `prd.md` at its real path. Nothing is copied, staged, or mirrored on
disk — there is exactly one file per PRD, and it is the member's.

A member session working its own board while a master session works the group
is the two-orchestrators case the loop already forbids. Same rule, wider board:
one orchestrator per PRD, and the master owns every PRD it merges.

**Reconcile.** A master's plan is a function of every member's state, so a
transition written in one project re-orders the whole board:

```sh
python3 <skill>/view/plan.py reconcile [board]   # waves recomputed, anchor kept
```

The live service does it by itself — it watches every member's files and
reconciles within about a second of a change landing in any of them, so the
timeline is never drawing yesterday's order. `plan` is still what re-anchors
the schedule on today; `reconcile` only re-orders.

**What crosses a board boundary, and what does not:**

| thing                            | scope                                                                                  |
|----------------------------------|-----------------------------------------------------------------------------------------|
| `prd.md`, specs, memos, `state`  | the member. Written where the PRD lives, never at the master                             |
| `needs:`                         | the whole master board. Resolved in the PRD's own board first, so a member's `needs: sibling` keeps meaning its sibling; across boards it is `@<member>/<prd>`. A bare name matching PRDs on two boards is ambiguous, reported, and ignored |
| `footprint:`                     | qualified with the member name before any overlap check — two repos both touching `src/lib.ts` are not touching one file. An **absolute** path is left as written, which is how a deliberate cross-repo overlap still clashes |
| `language`                       | the PRD's own board. A member's PRD, spec and report are written in that member's `language`; the master's is for its own PRDs and for the round |
| `workers`, `pipeline`            | the master. It is the one dispatching                                                   |
| `est` / `actual` calibration     | the member. Read the pairs from the board the PRD lives on — one repo's hours do not estimate another's |
| `repo` for a worker brief        | the PRD's own `repo:`, else the member's repo root — the directory holding its `prds/`   |

**Naming.** A master board is named for what it owns, not for the directory it
sits in. The first round that meets a master board with no `name:` asks the
user for one and writes it to `settings.md`, exactly as the first run asks for
the board language. Until then the name is inferred from the members
(`mitosys+model+realm`), which keeps the board working and is not an answer.

**What belongs on the master's own board:** a PRD that spans more than one
member. True of one member alone → it belongs on that member's board, however
large it is. The master sees and schedules every member's work; it implements
none of it that a member could own.

## Frontmatter contract

Tools read the keys below. Every other key in a `prd.md` or a spec is yours and
no tool touches it.

`prd.md`:

| key         | written by                     | read for                                          |
|-------------|--------------------------------|---------------------------------------------------|
| `state`     | orchestrator                   | the loop, the status line                         |
| `priority`  | user                           | dispatch order, higher first                      |
| `est`       | orchestrator, from the analyst | progress line, `~<h>h left`                       |
| `actual`    | orchestrator                   | calibration                                       |
| `commit`    | orchestrator                   | the sha the PRD landed as, per **Commits**        |
| `claim`     | orchestrator                   | the sweep, elapsed on `done`                      |
| `repo`      | user                           | the worker brief. Optional                        |
| `needs`     | user                           | `plan` wave order. A list of PRD dir names. Optional |
| `footprint` | user / orchestrator            | the overlap check in step 5, and `plan`'s waves when specs carry none. A list of paths. Optional |
| `origin`    | whoever creates the PRD        | the split in the progress line, and the tripwire in **Derived work**. `requested` \| `derived` |
| `from`      | orchestrator                   | which PRD's work surfaced a `derived` one. A PRD dir name |

`specNN.md`:

| key         | written by | read for                        |
|-------------|------------|---------------------------------|
| `est`       | analyst    | summed into the PRD's `est`     |
| `footprint` | analyst    | the overlap check in step 5     |

- `state` is the only key the loop cannot run without.
- Missing `priority` sorts at 0. Missing `est` weighs at the board average.
- Missing `origin` reads as `requested`. That default is deliberate: a board
  that predates this key keeps its numbers, and the only way to get counted as
  derived is to say so.
- Match a key by name, at any indentation, anywhere in the frontmatter. A
  `time:` map holding `est` and `actual` reads the same as both at top level.
  Names are unique within one file.
- Writing frontmatter preserves what you did not write — unknown keys, order,
  comments, nesting. Add `complexity`, `blast-radius`, `owner`: it survives
  every transition.

Body sections are contract too: `## Questions`, `## Answers`, `## Failure` in a
PRD; `## Acceptance` and `## Verify and Proof` in a spec. Sections you add
beside them are yours.

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
- `blocked` — the work is done and a box it cannot close waits on something
  named: another PRD landing, a commit, a machine. Carries `needs:` naming
  what it waits for; the body says which boxes are open and what closes each.
  It is live work — it counts in the progress line and the plan, and it never
  invites a blind retry.

Never reach for `blocked` to avoid a hard `failed`.

A `state` outside this table is the user's own and **parked**: never
dispatched, never scheduled by `plan`, left out of the progress line and the
status line, and kept out of the plan rather than folded into `open`.
Report parked PRDs by name in the round — neither progress nor backlog.

## Derived work

A board holds two kinds of PRD, and conflating them is how a board stops
delivering what it was opened for.

- **`origin: requested`** — the user asked for it. The deliverable.
- **`origin: derived`** — the board found it while working. A wrong claim in a
  PRD, a gate that cannot fail, a check whose selector is the wrong set.

Derived work is real and often the best work on the board. It is also
**self-generating**: a gate written to prove a requested PRD can itself be
defective, and the PRD that fixes it grows a gate of its own. Nothing in the
loop bounds that, so it has to be bounded here.

**Filing a derived PRD is not free.** Two rules, both at creation time:

1. **State the consequence for a requested PRD.** Name which one, and what it
   gets wrong if this is not fixed. A derived PRD whose body cannot name that
   consequence is filed **`state: deferred`** — parked, per **States**: never
   dispatched, never scheduled, out of the progress line, reported by name.
   Not `open`. `open` means the board intends to do it.
2. **A defect in an instrument is a memo, not a PRD.** If the finding changes
   no verdict about the deliverable — a check that would pass too quietly, a
   count that is a reading rather than a measurement, a census whose predicate
   was narrow — write it per **Memos** and move on. That knowledge is exactly
   what a memo is for: it outlives the work, and it costs no worker.

The test between them is one question: **would fixing this change what ships,
or only how loudly the board would have noticed?** The first is a PRD. The
second is a memo.

**The tripwire.** When open+`analyzing`+`specced`+`claimed` derived PRDs reach
the same count as requested ones, the board is working on itself. The loop
stops filing derived PRDs, reports the split with both counts, and puts it to
the user in the round: continue, defer the derived tree, or drop it. Do not
decide this alone — the trade between a finished deliverable and a perfect
record is the user's, and it is invisible to them until someone says the two
numbers out loud.

Two derived PRDs may not depend on each other more than one level deep. A
derived PRD filed against a derived PRD is the loop feeding on itself; fold the
second into the first, or write the memo.

**Measured, on a real board.** A dotfiles port ran to 34 of 54 requested PRDs
`done` with roughly 37h of requested work left — and 52 derived PRDs `done`
against 25 still open, 11 of those about the checking machinery rather than the
configuration. Derived `done` outnumbered requested `done`. The progress line
read `done 92/145 · 63%` throughout, which was true of the board and wrong
about the deliverable, and the user found out by asking why a port was taking
so long. Both rules above and the split in the **Progress line** exist because
that board could not report the difference.

## The loop

Run until the board is drained, or everything left is blocked on the user.
`once` = one round. `status` = step 1 plus the progress report, changing
nothing.

**1. Scan**

- Read `prds/settings.md`. Missing means first run: run
  `bash <skill>/doctor.sh --fix`, print every line it printed, create
  `settings.md` per `references/settings.md`, asking the user for the board
  language.
- `find prds -type f -name prd.md`, parse every frontmatter.
- `members:` in `settings.md` means a **master board**: scan every member the
  same way and address its PRDs `@<member>/<rel>`, per **Master boards**. With
  no `name:` on it, ask the user what the group is called and write it before
  the round goes on — a name inferred from directory names is a placeholder.
- No board: create `prds/`, report it empty, stop.
- Record what the working tree already owes — `git status --porcelain` in the
  board's repo and in every `repo:` on it. Those paths are the user's, and no
  commit this round adds them, per **Commits**.
- Once per session, sweep a dead session's leftovers — `analyzing` with no live
  worker → `open`; `claimed` with no live worker → `failed`. Partial code may
  exist, and a human look is cheaper than a blind retry.
- Read the worker's **output** before writing that sweep. `analyzing` with spec
  files on disk is an analyst that finished and an orchestrator that died: the
  transition is `specced` with the specs' `est` summed, not `open`. Sweeping it
  to `open` throws away work that is sitting right there.

A worker its infrastructure killed — API error, lost network, full disk — is
not a failed attempt:

- Resume THAT worker if it can be resumed. It holds the context, and its
  acceptance boxes are almost always empty because the evidence died with the
  process.
- Before it continues, establish whether the tree is left **deliberately**
  broken. A spec that asks for a break watched to fail leaves the break applied
  for as long as it takes to read the failure, and a worker killed in that
  window leaves broken code `claimed` does not hint at.
- Ask the worker which edit was in flight. It knows; the board does not.

**2. Answer**

- Read what came back through the view: a PRD whose `## Answers` grew, or one
  a person moved, is the user talking to the board. The view writes those
  directly, so they are simply on the board when the round scans it.
- Collect `## Questions` from every `question` PRD.
- Put them to the user as one round per `references/drill.md` — the whole
  frontier, numbered, each with your recommended answer.
- Questions from different PRDs share a round. A question depending on another
  still open belongs to the next round.
- Write answers under `## Answers`, set those PRDs `open`.
- No reply: leave them `question`, work the rest.

**3. Refine**

- The analyst left the proposed split in its report. Create each child dir +
  `prd.md` (`state: open`, the child's contract as body), set the parent
  `open`.
- No usable split proposal means nobody understands the PRD yet: drill it per
  `references/drill.md`, then write that tree as the children.
- Never invent a split to keep the board moving.

**4. Spec ahead**

While count(*dispatchable* `specced`) < **pipeline** and dispatchable `open`
PRDs exist (leaf, unclaimed, priority desc): mark each `analyzing` +
`claim: <worker> <started>` and dispatch analysts in one parallel batch.

Dispatchable is the same test as step 5 — `needs:` all `done`, no footprint
clash with a `claimed` PRD. A `specced` PRD nobody can be handed is not
pipeline: counting it starves the analyst stage exactly when the board is most
stuck, and the highest-priority `open` PRD is usually the one that would
unstick it.

**5. Implement**

While count(`claimed`) < **workers** and `specced` PRDs exist: pick by
priority, skip any whose `needs:` are not all `done`, skip any whose footprint
overlaps a `claimed` PRD, mark `claimed` + `claim: <worker> <started>`,
dispatch an implementer.

- Both skips are real work — a footprint clash makes two workers edit one file,
  and an unmet `needs:` sends a worker at code its dependency has not written.
- A PRD skipped for either reason stays `specced`. Say which of the two holds
  it, so a stalled-looking board reads as a queue rather than a bug.
- The footprint is the union of the specs' `footprint:` and the PRD's own.

**6. Collect**

On each finished worker: validate the result (specs on disk / verify output
present), write the transition, write `actual:` on a clean `done` per
**Calibration**, commit what landed per **Commits** and write its `commit:`,
clear `claim:`, print the progress line, post the worker's report with
`POST /report` per **The view**, return to step 2.

A worker reports defects outside its own scope — that is what a worker is for,
and it must not reach into a sibling's files to fix them. Deciding what becomes
of each report is the orchestrator's, per **Derived work**: a consequence for a
requested PRD makes it a derived PRD, `origin: derived` and `from:` naming the
PRD that surfaced it; a defect in an instrument makes it a memo; neither makes
it `open` by default. Check the tripwire before filing, not after.

A finished analyst refills the pipeline; a finished implementer frees a worker
slot. Do not poll if results are pushed to you.

**7. Stop**

Nothing in flight and nothing dispatchable: report per-state counts, every
`question` / `refine` / `failed` PRD by name with what it needs, and the final
progress line.

- Say what the tree owes: commits made this run, what is ahead of the
  upstream, and every path left dirty. The board commits and never pushes,
  so the last word on the run is the user's to act on.
- Everything left is waiting on the user, and the live service is up? Park on
  `serve.py wait` in the background before you stop, per **The view**. An
  answer the user writes in the view then wakes the round that acts on it,
  instead of waiting until someone next runs `/pearde`.

Report the two origins separately, and name what remains of the **deliverable**
first — the requested PRDs still not `done`, with their `est`. A closing report
that leads with a board-wide percentage tells the user how busy the board was,
not whether the thing they asked for exists. Every `deferred` derived PRD is
listed by name in the same breath, so parking is visible rather than quiet.

## Install check

An install that is present and broken looks exactly like one that is absent:
both do nothing. `doctor.sh` tells them apart.

```sh
bash <skill>/doctor.sh [board]         # report; exit 1 when a part is broken
bash <skill>/doctor.sh --fix [board]   # report, then repair
```

One part per line for one board, each `ok`, `off`, or `broken`. A broken part
carries the command that repairs it. `members` reports only on a master board;
the rest always report.

| part         | `off`                                  | `broken`                                                        |
|--------------|----------------------------------------|------------------------------------------------------------------|
| `skill`      | discovered nowhere                     | the skills symlink resolves to no skill folder                   |
| `statusline` | no `statusLine` in the config in force | configured, and its command does not resolve or renders nothing  |
| `board`      | no board                               | off the contract path, or no `language`                          |
| `members`    | not a master board — no `members:`     | a `members:` entry that is not a board on disk, or an empty list  |
| `memos`      | no `memos/`                            | a memo fails the check in `references/memo.md`                   |
| `view`       | the service is not running             | it runs and this board is not registered                                  |
| `plan`       | no plan on record yet                  | —                                                                          |

- It reads the config `$CLAUDE_CONFIG_DIR` names, falling back to `~/.claude` —
  several profiles can live on one machine, and a status line wired into the
  wrong one is correct and inert.
- `--fix` repairs three things: a missing skill symlink, a dead status-line
  symlink, and a view service that is down or not watching this board.
- `--fix` never writes `settings.json`. The status line a user configured is
  theirs, so a missing one is printed as JSON to paste.
- After repairing, doctor re-checks itself once — the report and exit code
  describe the state the repairs left behind, so a clean first run is one
  command: `doctor.sh --fix` ends green and watched.

Run it on the first run, on `doctor`, and whenever a part is silent when it
should not be.

## Progress line

Print on EVERY state change:

```
▸ <prd>: <from> → <to> · asked <ad>/<an> · <ap>% · derived <dd>/<dn> · open <o>/<n> · <q>% · ~<h>h left @<w> workers
```

| term       | is                                                                        |
|------------|---------------------------------------------------------------------------|
| weight     | the PRD's `est`. No `est` counts at the average est of estimated PRDs, `est-default` from `prds/settings.md` if none are estimated |
| `<ad>/<an>`| `done` / all PRDs with `origin: requested` — **the deliverable**            |
| `<ap>`     | Σ est(done, requested) / Σ est(all requested). `failed` counts as remaining |
| `<dd>/<dn>`| `done` / all PRDs with `origin: derived`. Counts, never est-weighted        |
| `<o>`      | PRDs still `open` — untouched, no analyst on them, both origins            |
| `<q>`      | `<o>/<n>`. A count, never est-weighted — an `open` PRD has no `est` to weight by |
| `<n>`      | the states in the **States** table only                                    |
| a master   | every member's PRDs and its own, in one set — the numbers are the group's, and a member named in a line is named `@<member>/<prd>` |
| `~<h>h`    | Σ est(not done) ÷ active workers, both origins — it is the whole queue      |

- **The `asked` figure is the answer to "how far along are we".** A single
  combined percentage cannot answer it, because derived PRDs enlarge the
  denominator with work the user never requested: a board 90% through its
  deliverable reads 63% once its own findings are counted alongside. Report
  both or neither.
- Omit the `derived` term on a board that has none. An empty term reads as a
  broken line, and a board with nothing derived should not carry the vocabulary.
- When the **Derived work** tripwire is live — derived in flight matching
  requested — say so on the line and in the round. A ratio nobody states is a
  ratio nobody acts on.
- `<q>` and `<p>` do not sum to 100. `<q>` is how much of the board is
  untouched, `<ap>` how much of the requested work is done.
- A parked PRD is in neither numerator nor denominator. Name it in the report
  instead of diluting the percentage with work nobody will do.
- `~<h>h left` is an estimate. Label jumps honestly — a refine split that adds
  children moves it up.

`statusline.sh` renders the same numbers continuously where a status line can
run a command, plus what the working tree owes and a link to the board:

```
<dir> <branch> *<dirty> ↑<ahead> ↓<behind> · <model>
▸pearde <ad>/<an> <ap>% · +<dn>d · open <o> <q>% · ▸board
```

- Two rows. The board is what is being read, and sharing a row with the path
  pushed it off the edge of a narrow terminal.
- No board in scope, no second row — a blank row reads as a broken status line,
  not an empty board.
- `<ad>/<an> <ap>%` is the requested work only, matching the progress line.
  `+<dn>d` is the derived PRD count, suppressed at zero — one glyph, because
  the status line has no room to argue and its job is to stop a derived tree
  growing unseen between rounds.
- `*<dirty>` is uncommitted entries. `↑`/`↓` are commits against the upstream.
  A branch with no upstream reads `no-upstream`, not `↑0` — nothing to push to
  is not nothing to push.
- `▸board` links to the board's live view, from the running service. It is an
  OSC-8 hyperlink; `PRD_STATUS_LINK=off` prints the
  label bare for a terminal that shows the escape raw. Optional.

## Calibration

`est` is a guess. `actual` is what a run measured. Every clean run makes the
next `est` better.

Write `actual:` on the `claimed → done` transition. Elapsed = now minus the
timestamp in `claim:`. Round to the nearest 5 minutes, in `est`'s units — `45m`,
`2h`.

Write it only when the run was clean:

- one dispatch, `specced` straight to `done`
- DONE returned, every box `[x]`, verify output shown
- no BLOCKED round-trip
- no `## Failure` anywhere in the PRD's history

Anything else leaves `actual:` empty. A retry measures the retry; a BLOCKED
round-trip measures how long the user took to answer. Neither is the cost of
the work, and a wrong number is worse than none.

Read the record before writing a new `est:`:

```sh
grep -rl 'state: done' prds --include=prd.md \
  | xargs -r grep -H -E '^[[:space:]]*(est|actual):'
```

Scale by the ratio the pairs show. Three pairs at 4h/40m mean the board
estimates 6× high — say so in the report, and estimate the next PRD at the
corrected scale.

## Commits

A PRD that lands is committed on the transition that lands it. A board that
runs for hours otherwise ends with one working tree holding every PRD's work —
nothing can be reviewed, reverted, or bisected on its own, and the only review
left is the whole session.

The orchestrator commits. Never a worker — two implementers committing in
parallel write each other's half-finished files into each other's commits, and
one writer is the rule that already keeps them apart.

| transition          | do                                                                    |
|---------------------|------------------------------------------------------------------------|
| `claimed → done`    | commit                                                                 |
| `claimed → blocked` | commit — the work is done, the open boxes wait on something named       |
| `blocked → done`    | commit what closing the boxes wrote                                    |
| `claimed → failed`  | nothing. Name the dirty paths in the report, leave them on disk         |

Board state written between transitions — answers, a refine split, a memo —
carries no commit of its own and rides the next one. It describes work in
flight; a commit records work that landed.

**Scope: the footprint, never the tree.** Add the union of the specs'
`footprint:` and the PRD's own, plus the PRD's own folder. Never `git add -A`,
never `git commit -a` — step 5 already proved no other `claimed` PRD writes
that footprint, so a footprint-scoped commit cannot swallow a parallel worker's
half-written file or a `failed` PRD's leftovers.

Two guards on what gets added:

- **The inherited tree is not the board's.** Step 1 records what is dirty
  before the round starts. Those paths are never added, whatever footprint they
  fall in. Name them once in the round.
- **A path the worker wrote outside its footprint is a wrong footprint.**
  Commit it with the rest and say so — step 5 cleared some other PRD against a
  file it did not know this one touches.

**Gate first.** Commit only what the `done` gate passed: verify output in the
report, every box `[x]`, spot-checks run. A red tree is a `failed` PRD, and a
`failed` PRD does not commit.

**Message.** Subject `<prd> — <what landed>`, one line per spec, `prd:` naming
the folder so the history points back at the board.

```
<prd> — <the PRD's contract in one line>

<specNN>: <goal>
<specNN>: <goal>

prd: prds/<path>
```

Write the sha to `commit:` on the PRD, beside `actual:`. It is the only link
from a `done` PRD to the code it produced, and `retry` on a later regression
starts by reading it.

**One commit per repo the PRD wrote.** A PRD with `repo:` elsewhere writes code
there and its own record on the board: commit each where it lives, same subject
line. One repo is one commit. On a master board that is the member's repo, not
the master's.

**Never push.** The commit is the board's, the push is the user's. Report what
is ahead in the closing report and stop there.

`commits: off` in `prds/settings.md` holds all of it — each transition then
names its dirty footprint instead. While it is on, `*<dirty>` in the status
line is the reading that matters: a count climbing across rounds is a board
whose commits are not landing.

## Worker briefs

Give each worker exactly its brief with the placeholders filled in. `<skill>`
is this folder's path.

Rules for every worker:

- Never edit frontmatter, never touch other PRDs, never write outside the PRD
  folder. Implementers also write the target repo.
- Never commit, never stage, never branch. Leave the work in the tree — the
  orchestrator commits the PRD on the transition that lands it, per **Commits**.
- Write per `references/language.md`, in the board `language` from
  `prds/settings.md`. Name the language in the brief. On a master board that is
  the language of the PRD's **own** board — a member's PRD is written in the
  member's language, per **Master boards**.
- Give a member's worker real paths, never `@<member>/…`: the address is the
  board's, the worker's brief names the file and the repo it lives in. `repo`
  is the PRD's own, else the member's repo root.
- A report that is incomplete, or a worker stopped mid-task: continue THAT
  worker — it holds the context. Never respawn it.
- Report a defect found outside your scope; do not file it and do not fix it.
  Say what is wrong, what you measured, and which requested PRD it would get
  wrong if anything. The orchestrator decides whether that becomes a PRD, a
  memo, or nothing, per **Derived work** — a worker that files its own findings
  turns one PRD into three and cannot see the board's ratio.

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

| report                                                                     | set                                    |
|----------------------------------------------------------------------------|----------------------------------------|
| DONE, every box ticked, verify output shown                                 | `done`                                 |
| DONE, open boxes waiting on something named, everything the worker owns proven | `blocked` + `needs:`                |
| anything less                                                               | `failed`, or answer a BLOCKED worker and let it finish |

Two unclosable boxes to catch when the specs land, not after a worker has spent
hours on them:

- A box asking for a **commit** or a commit message — committing is the
  orchestrator's act on the transition, per **Commits**.
- A `verify:` running the **whole workspace** — it inherits every other node's
  flake, so the box measures the tree's worst neighbour rather than this node's
  work.

A spec asking to change **another** PRD's body — usually a child correcting a
parent's acceptance box — is the orchestrator's edit on that transition, not
the worker's. The worker reports the wording. One writer per file holds, and a
worker reaching into a sibling folder is how two of them collide.

## Without parallel workers

Run the same loop single-file: scan → answer → refine → pick the
highest-priority actionable PRD → run its brief yourself as a checklist
(analyst for `open`, implementer for `specced`) with the transitions before and
after → print the progress line → repeat. Effectively `workers=1`,
`pipeline=1`.

Every rule holds: one writer, verify before `done`, commit on the transition,
work flows to the leaves.

## Memos

A PRD says what to build. A **memo** says what was decided and what it beat. A
PRD goes `done` and stops mattering; a memo outlives the work it governed.

```
prds/memos/<slug>.md
```

- No `state`. Never claimed, specced, or dispatched.
- Invisible to scan and to the progress line — `memos/` holds no `prd.md`.
- On the board anyway — a decision recorded where the next session does not
  look is a decision nobody has.

Frontmatter is a **closed set**: `memo`, `kind`, `status`, `subject`, `date`
required; `updated`, `prds`, `supersedes`, `superseded_by` optional; anything
else is a typo that fails `doctor`. This is the one place the board inverts its
own rule — a `prd.md` keeps every key you add, a memo does not, because the
memo table is a fold of the frontmatter and a fold cannot be computed from keys
nobody declared.

Body shape, per `references/templates/memo.md`: Decision, Why, **Alternatives
considered**, Consequences. Alternatives is never empty — a memo with no
alternatives is a claim, not a decision, and nobody can later tell whether the
other road was walked and rejected or never seen.

```sh
python3 <skill>/memos.py list [board]    # slug · kind · status · date · subject
python3 <skill>/memos.py check [board]   # what doctor reports for `memos`
```

Write one when a call is made that the code will not explain: a rule the board
follows, a road not taken, a constraint that looks arbitrary. Not for what a
commit message covers. `references/memo.md` is the format and the argument.

Decisions already recorded in another system stay there: `memos: <dir>` in
`prds/settings.md` reads that dir read-only, and the strict gate
keeps applying only to the board's own `memos/`.

## Handles

The spelling follows the setup — `/pearde status` where commands take
arguments, "pearde status" in plain chat. The meanings are fixed.

| Want                         | Say                                                                                                      |
|------------------------------|-----------------------------------------------------------------------------------------------------------|
| report only, change nothing  | `status`                                                                                                 |
| one round, then stop         | `once`                                                                                                   |
| more implementers            | `workers=5` — written to `prds/settings.md`, persists                                                    |
| deeper spec pipeline         | `pipeline=5` — written to `prds/settings.md`, persists                                                   |
| hold the commits             | `commits=off` — written to `prds/settings.md`, persists. Each transition names its dirty footprint instead, per **Commits** |
| new PRD                      | `add <title>` — creates the dir + `prd.md` from `references/templates/prd.md`, `state: open`, `origin: requested` |
| park a derived PRD           | `defer <prd>` — `state: deferred`, per **Derived work**. Reported by name, never dispatched              |
| work out what is wanted      | `drill <prd>` — interview per `references/drill.md`; with no `<prd>`, into a new tree                    |
| retry a failed PRD           | `retry <prd>` — moves `## Failure` into the body as history, sets `open`                                 |
| a blocked PRD's event landed | `unblock <prd>` — re-runs only the open boxes, per **States**; `done` when they close                    |
| run one PRD to done          | `run <prd>` — the loop scoped to that PRD's subtree                                                      |
| record a decision            | `memo <subject>` — creates `prds/memos/<slug>.md` from `references/templates/memo.md`, per **Memos**     |
| pre-plan parallel waves      | `plan` — `view/plan.py plan` per **The view**; print the waves it returns                                |
| the local timeline           | `gantt` — `sync.py gantt --open`: the plan as `prds/.gantt.html`, x = distance to the vision |
| open the board               | `view` — `view/serve.py ensure`, then the URL it prints, per **The view**                                |
| plan across projects         | `master <path> …` — writes `members:` in `prds/settings.md`, asks the group's `name:` the first time, per **Master boards**. This board is then the parent every round works in |
| what a master merges         | `master` with no path — `sync.py members`: every member, its path, and `MISSING` when it is not on disk  |
| stop merging one             | `master drop <name>` — removes that `members:` entry. Nothing in the member changes; it is a board again |
| re-order after a member moved| `reconcile` — `sync.py reconcile`: waves recomputed, anchor kept. The live service already does it       |
| is this thing wired?         | `doctor` — `doctor.sh --fix`, per **Install check**; print every line                                    |

`add` is the user asking, so it writes `origin: requested`. Only the
orchestrator writes `origin: derived`, and only with `from:` naming the PRD
whose work surfaced it — see **Derived work** for what must be true before a
derived PRD is filed `open` rather than `deferred`.

`master <path>` takes one or more paths, each a board or a repo holding one,
and appends them to `members:`. It creates nothing in the member and moves no
file — a board joins a master by being named in one list, and leaves the same
way. Print what the merged board now holds: member count, PRD count, and the
plan `reconcile` produced.

`memo <subject>` slugs the subject — lowercase, spaces to hyphens. The slug is
both the filename and the `memo:` key, and `doctor` fails if they disagree.
Write the memo when the call is made, not when the work lands.

`add` takes the title as written. A one-line title is too thin to spec, so the
analyst returns REFINE or QUESTION and the drill happens then. Use `drill` to
settle it first: it runs `references/drill.md` to completion and leaves a tree
the loop picks up — settled contract as the body, each branch a child dir with
its own `prd.md`, `state: open`. Dispatch nothing while a drill is running.

`run <prd>` filters the board to that PRD and its children:

- Scan still parses everything, for the sweep and the progress line, but only
  PRDs inside `prds/<prd>/` are answered, refined, specced, or implemented.
- Nothing outside the subtree changes state.
- The user named it, so a `failed` target or child is reopened first, exactly
  as `retry` would.
- A `done` target is reported and left alone. No match: list the near-misses,
  change nothing.
- The run ends when the subtree is drained — report the target's final state —
  or everything left in it is blocked on the user.

One orchestrator per board. On start, if the scan shows fresh `analyzing` /
`claimed` claims you did not make, their workers may be alive in another
session: say so and run `status` only. Never sweep another live session's
claims.

## The view

The board is files; the view is how a person reads and works them. One command
starts it, once per machine:

```sh
python3 <skill>/view/serve.py ensure     # start if needed, register this board
```

From then on `http://127.0.0.1:8443/board/<name>` is the board, live: it
re-renders within a second of any file changing, and every board registered on
this machine is listed at `/`.

**Five readings of the same board.**

| view          | answers                                                        |
|---------------|------------------------------------------------------------------|
| **timeline**  | what is in front of us — see below                                |
| **board**     | what is where — kanban by state; drag a card to write `state:`    |
| **list**      | all of it — sortable, filterable, one row per PRD                 |
| **analytics** | how this is going — where the work sits, where the hours are, estimates against reality, hours left over time |
| **memos**     | what the board decided — `prds/memos/`, rendered                  |

**The timeline's x axis is not time.** The workers are agents: they start when
the work is dispatchable, and there are as many of them as the board can
usefully run, so a date on a bar is a guess about staffing. The dependency
structure is not a guess. The axis is est-hours along the **critical path** —
zero at now, the right edge the vision reached.

- **★ critical** marks the chain that sets the finish. An hour cut there moves
  the vision closer; an hour cut anywhere else moves nothing.
- **float** is the tail behind a bar: how late it may start before it becomes
  critical.
- **ready now** is the frontier at zero, ordered by how much work each PRD
  unblocks. That ordering *is* the dispatch order.
- **wave bands** across the top are the plan's rounds — a wave runs after the
  one before it, because that is what a footprint clash means.
- the header names the **peak agent count** the fastest path asks for, beside
  what `workers` costs instead. The gap between them is the decision.
- **dates** (or `v`) draws the same bars on the worker-limited calendar, at
  `gantt-day` hours per day, for anyone who wants a date.

**Clicking anything opens the PRD**, and the pane writes back: title, `state`,
`priority`, the body, a note appended to `## Notes`, and — on a PRD in
`question` — its questions with an answer box that writes `## Answers` and sets
the PRD `open` again. `+ PRD` (or `n`) writes a new one from the view. Every
write goes through `view/edit.py`: one line at a time, atomically, frontmatter
and body never in the same write.

Deep links are real: `#prd=<rel>` opens one PRD, `#view=board` opens a view.

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
background at session start, and again whenever a round ends with work still
open: the board wakes the orchestrator rather than the orchestrator polling the
board.

**What the board keeps.** `prds/.plan.json` is the last plan (waves, schedule,
the day it was anchored). `prds/.history.jsonl` is one row a day — the only
memory the board has, and what the burn-down draws. Both are machine-local and
regenerable; gitignore them:

```
prds/.plan.json
prds/.history.jsonl
prds/.view.html
```

