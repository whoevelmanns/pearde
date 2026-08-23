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
| `plane/`                        | the board as live tickets in a self-hosted Plane, the live service, and the wave planner. Optional — `plane/plane.md` |

## Roles

| role             | does                                                        |
|------------------|-------------------------------------------------------------|
| **orchestrator** | works the board. The ONLY writer of PRD state — nothing to race, so no locking. One per board |
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
| `claim`     | orchestrator                   | the sweep, elapsed on `done`                      |
| `repo`      | user                           | the worker brief. Optional                        |
| `needs`     | user                           | `plan` wave order. A list of PRD dir names. Optional |
| `footprint` | user / orchestrator            | the overlap check in step 5, and `plan`'s waves when specs carry none. A list of paths. Optional |

`specNN.md`:

| key         | written by | read for                        |
|-------------|------------|---------------------------------|
| `est`       | analyst    | summed into the PRD's `est`     |
| `footprint` | analyst    | the overlap check in step 5     |

- `state` is the only key the loop cannot run without.
- Missing `priority` sorts at 0. Missing `est` weighs at the board average.
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
status line, and given its own Plane state rather than borrowing `open`'s.
Report parked PRDs by name in the round — neither progress nor backlog.

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
- No board: create `prds/`, report it empty, stop.
- Once per session, sweep a dead session's leftovers — `analyzing` with no live
  worker → `open`; `claimed` with no live worker → `failed`. Partial code may
  exist, and a human look is cheaper than a blind retry.

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
**Calibration**, clear `claim:`, print the progress line, mirror per **Plane**,
return to step 2.

A finished analyst refills the pipeline; a finished implementer frees a worker
slot. Do not poll if results are pushed to you.

**7. Stop**

Nothing in flight and nothing dispatchable: report per-state counts, every
`question` / `refine` / `failed` PRD by name with what it needs, and the final
progress line.

## Install check

An install that is present and broken looks exactly like one that is absent:
both do nothing. `doctor.sh` tells them apart.

```sh
bash <skill>/doctor.sh [board]         # report; exit 1 when a part is broken
bash <skill>/doctor.sh --fix [board]   # report, then repair
```

Five parts for one board, each `ok`, `off`, or `broken`. A broken part carries
the command that repairs it.

| part         | `off`                                  | `broken`                                                        |
|--------------|----------------------------------------|------------------------------------------------------------------|
| `skill`      | discovered nowhere                     | the skills symlink resolves to no skill folder                   |
| `statusline` | no `statusLine` in the config in force | configured, and its command does not resolve or renders nothing  |
| `board`      | no board                               | off the contract path, or no `language`                          |
| `memos`      | no `memos/`                            | a memo fails the check in `references/memo.md`                   |
| `plane`      | not installed                          | installed and unreachable, or reachable and this board never bootstrapped |

- It reads the config `$CLAUDE_CONFIG_DIR` names, falling back to `~/.claude` —
  several profiles can live on one machine, and a status line wired into the
  wrong one is correct and inert.
- `--fix` repairs four things: a missing skill symlink, a dead status-line
  symlink, a board Plane is running for that was never bootstrapped, and a
  live service not watching this board.
- `--fix` never writes `settings.json`. The status line a user configured is
  theirs, so a missing one is printed as JSON to paste.
- After repairing, doctor re-checks itself once — the report and exit code
  describe the state the repairs left behind, so a clean first run is one
  command: `doctor.sh --fix` ends green, mirrored, and watched.

Run it on the first run, on `doctor`, and whenever a part is silent when it
should not be.

## Progress line

Print on EVERY state change:

```
▸ <prd>: <from> → <to> · done <d>/<n> · <p>% · open <o>/<n> · <q>% · ~<h>h left @<w> workers
```

| term      | is                                                                         |
|-----------|----------------------------------------------------------------------------|
| weight    | the PRD's `est`. No `est` counts at the average est of estimated PRDs, `est-default` from `prds/settings.md` if none are estimated |
| `<p>`     | Σ est(done) / Σ est(all). `failed` counts as remaining                      |
| `<o>`     | PRDs still `open` — untouched, no analyst on them                           |
| `<q>`     | `<o>/<n>`. A count, never est-weighted — an `open` PRD has no `est` to weight by |
| `<n>`     | the states in the **States** table only                                     |
| `~<h>h`   | Σ est(not done) ÷ active workers                                            |

- `<q>` and `<p>` do not sum to 100. `<q>` is how much of the board is
  untouched, `<p>` how much of the work is done.
- A parked PRD is in neither numerator nor denominator. Name it in the report
  instead of diluting the percentage with work nobody will do.
- `~<h>h left` is an estimate. Label jumps honestly — a refine split that adds
  children moves it up.

`statusline.sh` renders the same numbers continuously where a status line can
run a command, plus what the working tree owes and a link to the board:

```
<dir> <branch> *<dirty> ↑<ahead> ↓<behind> · <model>
▸pearde <d>/<n> <p>% · open <o> <q>% · ▸board
```

- Two rows. The board is what is being read, and sharing a row with the path
  pushed it off the edge of a narrow terminal.
- No board in scope, no second row — a blank row reads as a broken status line,
  not an empty board.
- `*<dirty>` is uncommitted entries. `↑`/`↓` are commits against the upstream.
  A branch with no upstream reads `no-upstream`, not `↑0` — nothing to push to
  is not nothing to push.
- `▸board` links to the Plane timeline, from the `gantt` key `plan` writes into
  `.plane-map.json`. It is an OSC-8 hyperlink; `PRD_STATUS_LINK=off` prints the
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

## Worker briefs

Give each worker exactly its brief with the placeholders filled in. `<skill>`
is this folder's path.

Rules for every worker:

- Never edit frontmatter, never touch other PRDs, never write outside the PRD
  folder. Implementers also write the target repo.
- Write per `references/language.md`, in the board `language` from
  `prds/settings.md`. Name the language in the brief.
- A report that is incomplete, or a worker stopped mid-task: continue THAT
  worker — it holds the context. Never respawn it.

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

- A box asking for a **commit message** — committing is not an implementer's
  act.
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

Every rule holds: one writer, verify before `done`, work flows to the leaves.

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
`prds/settings.md` mirrors that dir to Plane read-only, and the strict gate
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
| new PRD                      | `add <title>` — creates the dir + `prd.md` from `references/templates/prd.md`, `state: open`             |
| work out what is wanted      | `drill <prd>` — interview per `references/drill.md`; with no `<prd>`, into a new tree                    |
| retry a failed PRD           | `retry <prd>` — moves `## Failure` into the body as history, sets `open`                                 |
| a blocked PRD's event landed | `unblock <prd>` — re-runs only the open boxes, per **States**; `done` when they close                    |
| run one PRD to done          | `run <prd>` — the loop scoped to that PRD's subtree                                                      |
| record a decision            | `memo <subject>` — creates `prds/memos/<slug>.md` from `references/templates/memo.md`, per **Memos**     |
| pre-plan parallel waves      | `plan` — `sync.py plan` per **Plane**; print the waves it returns                                        |
| the adaptive local timeline  | `gantt` — `sync.py gantt --open`: the plan as `prds/.gantt.html`, a now-line and only the rows in the scrolled window |
| the ticket mirror            | `plane` — `plane/plane.sh boot`: app up + every board synced, per **Plane**                              |
| is this thing wired?         | `doctor` — `doctor.sh --fix`, per **Install check**; print every line                                    |

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

## Plane

Optional. The board mirrors to a self-hosted Plane running inside the skill:

- one ticket per `prd.md` — title, body, `state`, `priority` mapped, every
  other frontmatter scalar a `key: value` label, child PRDs as sub-tickets
- one **page** per memo — a memo is a document, so it belongs in the wiki, not
  the work list

Setup, mapping, and the wave planner: `plane/plane.md`. Install:
`references/install.md` step 3.

```sh
python3 <skill>/plane/serve.py ensure        # the live service: watch + mirror
python3 <skill>/plane/sync.py sync --quiet   # one manual mirror pass
python3 <skill>/plane/sync.py plan           # waves → stdout + `wave: N` labels
python3 <skill>/plane/sync.py gantt --open   # the plan as prds/.gantt.html
```

All three are safe to run any time. `gantt` needs no Plane at all: it renders
the last plan as one self-contained HTML file, an adaptive condensed timeline —
a vertical line marks now, and only the tasks whose bars cross the visible
window get a row, sorted by priority, so scrolling left and right re-forms the
list around the time under your eyes. `plan` rewrites it and `sync` keeps it
fresh once it exists; details in `plane/plane.md`.

**The live service first.** Run `serve.py ensure` once at session start: it
starts the daemon if none runs, registers this board, and from then on every
disk change mirrors itself within a second — tickets, memo pages, and the
waves as Plane cycles. It also serves the timeline live at
`http://127.0.0.1:8443/board/<name>` and takes worker reports as ticket
comments (`POST /report`) — post each worker's report there on collect, so the
ticket carries its own evidence. Details: `plane/plane.md` § The live service.

Mirror rule, on `prds/.plane.env` and `plane` from `prds/settings.md`:

| `.plane.env` | Plane            | do                                                        |
|--------------|------------------|-----------------------------------------------------------|
| present      | daemon watching (`serve.py status`) | nothing — it mirrors for you; `POST /report` on collect |
| present      | daemon not running | `serve.py ensure`; until it runs, `sync --quiet` after every state change |
| absent       | installed and up | `plane/plane.sh bootstrap` this board, then mirror — a running app mirrors nothing on its own |
| absent       | not installed    | no mirror; report it once in the round, never again        |

`plane: off` in `prds/settings.md` stops all three: no bootstrap, no sync, no
report. The board on disk is the source of truth — ticket edits made in Plane
are overwritten on the next sync.

**Memos → Pages.** `sync` mirrors `prds/memos/` into the project's Pages: a
`Memos` index whose table is a fold of the frontmatter, plus one
`Memo · <slug>` page each. They are pages, not work items, so they stay out of
the issue list, the Gantt, and the progress count.

- A memo deleted on disk has its page **archived**, not deleted — archiving
  undoes in one click, and the record of having decided is the thing least safe
  to destroy.
- Pages live on Plane's session API, not `/api/v1`, so the memo mirror is
  best-effort exactly like the `Gantt — waves` view: with auto-login off it is
  skipped, `sync` says so on its last line, and the tickets still mirror.
- The pages are flat, not nested under the index — this Plane build drops a
  page out of the project's page collection the moment a `parent` is set and
  404s its detail route with it. The `Memo · ` prefix does the grouping the
  tree would have done.

**`plan`** orders the undone PRDs into waves — as parallel as `needs:`
frontmatter, parent-after-children, and footprints allow — labels each ticket
`wave: N`, and dates it so Plane's Timeline view is the Gantt of the plan
(kanban is the Board layout, grouped by State). It reads `workers` and
`est-default` from `prds/settings.md`; `--workers=N` overrides. Run it on
`plan`, and re-run it when a refine adds children or specs land with
conflicting footprints.

What it guarantees:

- **Two constraints, one fixed point.** A footprint clash bumps the lower
  priority to the next wave, and every bump re-applies the `needs` floor — so a
  bumped PRD never ends up level with, or ahead of, a parent that waits on it.
- **A footprint comes from the specs, or from the PRD.** `footprint:` on
  `prd.md` counts too, so a PRD plans correctly before it is specced and while
  an implementer holds its spec files.
- **A parent weighs nothing.** Its hours are its children's; counting both
  bills the same work twice. It still waits for them.
- **Only real work is scheduled.** `done` and parked PRDs are named, not
  planned, and a PRD that leaves the plan loses its Gantt bar on the next sync.
- **The timeline is a saved view.** `plan` prints the URL of a `Gantt — waves`
  view whose layout is the timeline, so the plan opens as a Gantt instead of a
  list. It needs auto-login on; without it, the layout is two clicks.

**`plane`** runs `plane/plane.sh boot`: install and start if needed, then every
board on the machine — this one, the registry, every Claude session folder
holding a `prds/`, and any board one level below one of those — bootstrapped
into its own Plane project and synced. A board off the contract path is
mirrored, not skipped; `doctor.sh` is what says move it. No browser step
anywhere.

`plane/plane.sh status [board]` answers both halves: the app, and whether that
board mirrors. To look at a board in the app: `plane/plane.sh open` — the
browser, straight into the workspace, no login.
