---
state: done
origin: requested
actual: 11.0h
commit: 00a1371
priority: 60
complexity: 0
blast-radius:
repo: pearde
---

# the-board-runs-itself — one command moves the states, the board organises itself toward a vision, and a person reads one page

`prds/vision.md` is the destination. This PRD is its contract, and the
children are the work. Work flows to the leaves: this PRD is done when every
child is.

## What is true today

- A round is a model reading rules. `references/parts/` is 2,037 lines, and
  the loop opens `loop.md` (302), `workers.md` (198), `commits.md`,
  `progress.md`, `states.md` and a persona file to move one PRD from
  `claimed` to `done`.
- Every transition is a hand edit. `state:`, `claim:`, `commit:`, `actual:`,
  `complexity:` are written by the model with an editor, one line at a time,
  and the gate each one has is a sentence the model is trusted to have read.
- A collect is ~12 tool calls. A REFINE split is the model creating
  directories. A brief is composed from three files at every dispatch. A first
  run asks a question and copies a block.
- The vision axis lives in `prds/vision.py` and `prds/allboards.py` on the
  master board, outside the skill — 33 KB that re-implements `plan.py`'s
  scan. `order.md` already cites `.vision.json` as the frontier's order.
- Worker liveness is a guess. "`claimed` with no live worker" is a judgment
  the model makes from nothing on disk.
- Every check in this repo builds its own fixture — four `probe/` dirs, eleven
  scripts, each with a temp board of its own, and no board a reader can open.
- `report.md` at the root measured one round on 2026-08-27: 318,584 output
  tokens — a capped proxy model re-deriving, and a model with the rules in
  context ignoring them. `MAX_THINKING_TOKENS`, `scan`, `prds/.round.md` and
  the guard closed the **reading** half. This tree closes the **writing**
  half: the hand edits no cap and no scan can bound.

## The shape — three rings

| ring | holds | a newcomer meets it |
|---|---|---|
| **core** | the board, the nine states, the loop as six commands, the view | in the first five minutes |
| **advisors** | drill, memos, workflows, personas, consult, report | when a PRD needs one |
| **tools** | master, doctor, guard, statusline, scout, install | when something is wired or broken |

Nothing is removed. The README presents the rings; `index.md` stays the agent's
map.

## Decisions — settled here, not asked

| decision | beats | why |
|---|---|---|
| the tool moves the states, and the prose becomes the spec of the tool | a better model reading better prose | measured: the rules were on disk and ignored for 160,000 tokens. A command cannot be ignored — `prds/memos/the-tool-moves-the-states.md` |
| `pearde init` defaults `language` to English and says so on its first line | asking on the first run | one question is the whole first-run friction, and the key is one line to change — `prds/memos/init-defaults-the-language.md` |
| `prds/vision.md` is a board file the skill reads | a script per board | `order.md` already depends on it; a second board would fork the script |
| the deferred derived tree stays deferred; this tree absorbs the two pieces its own gate needs | reopening the three derived PRDs | the user answered the tripwire on 2026-08-28 by deferring them. `collect`'s gate here is `index.py check` green, so the directory row of `snapshots-fold-to-one-row` lands inside `an-example-board` (it needs the same mechanism), and the probe rules of `probe-code-lives-in-the-prd-folder` land inside `brief-is-printed` (the brief is where they are read). `check-crosses-member-boundaries` stays parked |
| every check runs on one example board | a temp fixture per probe | one board a reader can open is one board every harness can snapshot |

## Children

| child | delivers | needs | priority |
|---|---|---|---|
| `an-example-board` | one small board in every band of the pressure order; every harness points at it | — | 72 |
| `one-command` | `pearde <cmd>` — one entry point over every script; the skills say that line | — | 70 |
| `transitions-are-commands` | `add` `claim` `release` `answer` `defer` `retry` `unblock` `set` — each checks its gate and prints the progress line | one-command · an-example-board | 68 |
| `specced-is-a-command` | `specced` validates the specs and sums the weight; `refine` materialises children from the analyst's `## Split` table | transitions-are-commands | 66 |
| `collect-is-a-command` | `collect` — verify, commit the footprint, `done`, `POST /report`, one call | transitions-are-commands | 66 |
| `brief-is-printed` | `brief <prd>` prints the worker's brief with persona, workflow and paths filled | one-command | 64 |
| `too-big-splits-itself` | `split-above` and `specs-above` in settings; over the limit is REFINE, and REFINE is a command | specced-is-a-command · brief-is-printed | 62 |
| `init-asks-nothing` | `init` — a board, registered, planned, three next lines printed, no question | one-command · vision-is-first-class | 62 |
| `vision-is-first-class` | `prds/vision.md` read by `plan.py` on every board; `vision.py` retires; `pearde vision` | one-command | 60 |
| `the-loop-is-commands` | `loop.md` rewritten as the calls it makes, under 120 lines; a `PreToolUse` guard matcher refuses a hand-written `state:` where it is wired | transitions · specced · collect · brief · init | 58 |
| `the-page-shows-the-round` | the now-strip, the round panel, `silent <age>` on held rows, the report as a view, `/board/<name>` from `name:` | transitions-are-commands | 56 |
| `readme-in-three-rings` | a README for a person: quickstart, the five files, the states as one picture, three rings | the-loop-is-commands · init-asks-nothing · vision-is-first-class | 55 |
| `tokens-per-transition` | the round's cost as a number on the page, from the guard's own count | one-command · the-loop-is-commands | 40 |

Every child carries `workflow: probe-then-spec` — the library's route for
an open PRD, seeded the same day. The analyst names `implement-a-spec` on the
specs it writes.

Deferred on the board and absorbed here: `snapshots-fold-to-one-row` into
`an-example-board`, `probe-code-lives-in-the-prd-folder` into
`brief-is-printed`. `check-crosses-member-boundaries` stays deferred.

## Order

The serial chain is `an-example-board → one-command → transitions-are-commands
→ specced-is-a-command → collect-is-a-command → the-loop-is-commands →
readme-in-three-rings`. Everything else runs beside it as its gate clears:
`brief-is-printed` and `vision-is-first-class` the moment `one-command` lands
(they share `doctor.sh` with `init-asks-nothing`, which the plan serialises
after them); `the-page-shows-the-round` after transitions;
`too-big-splits-itself` after specced and brief; `tokens-per-transition` last.

## Constraints

- Python 3 stdlib, no build step, no dependency. Files stay the truth.
- The nine states, the gates, the frontmatter contract and one orchestrator
  per board do not move. A command is the orchestrator's hand, not a second
  writer — and a command cannot tell who called it, so "a worker never runs a
  transition" stays a sentence in the brief, per
  `prds/memos/the-tool-moves-the-states.md`.
- No agent, tool, hook or vendor is named in a command's output or a brief.
- Every reference an agent reads keeps `references/language.md`. The README
  is the one document that gets a human reader.
- A child adds a command as a module under `resources/board/` exposing
  `COMMANDS`; `pearde.py` discovers it. No child edits the dispatcher, and
  the handle rows are written once by `one-command`.
- A child that touches `references/parts/*.md` deletes the sentence the
  command now enforces. A rule the tool checks and the prose restates is two
  rules that can disagree.
- Each child's harness runs against `an-example-board`, copied to a temp dir,
  never in place.

## Non-goals

- A workflow engine. Nothing runs a step for a worker.
- A hosted or multi-user daemon. The view stays on `127.0.0.1`; a LAN bind is
  a later PRD with its own contract.
- Rewriting the timeline canvas, or merging skills.
- A database, a queue, or a process the board needs in order to plan.

## Inherited tree

~670 uncommitted lines across 19 files sit in this repo from another session
— the names column in `view.js`, the answered panel in `serve.py`, scout
data, `drill.md`, `workflow.md`, two templates, six `prds/` edits. They are
not this tree's. Commit or drop them before `an-example-board` starts, so the
first snapshot is of a known page.

## Pointers

- @references/parts/loop.md · @references/parts/states.md ·
  @references/parts/commits.md · @references/parts/progress.md — the rules
  the commands implement, and the sentences they then delete.
- @resources/board/plan.py `standing`, `compute_plan`, `cmd_scan` — what the
  commands read. @resources/board/edit.py — how they write.
- `/Users/feb/dev/infra/prds/vision.py` and `allboards.py` — the axis to fold
  in.
- `report.md` at the repo root — the measurement this tree answers.
