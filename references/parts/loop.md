# The loop

The seven steps, in order. Run until the board is drained, or everything left
is blocked on the user. `once` = one round. `status` = step 1 plus the progress
report, changing nothing.

**1. Scan**

- Read `prds/settings.md`. Missing means first run: `bash
  @resources/doctor.sh --fix`, print every line it printed, create
  `settings.md` per @references/settings.md, asking the user for the board
  language.
- `find prds -type f -name prd.md`, parse every frontmatter.
- `members:` means a **master board**: scan every member the same way, address
  its PRDs `@<member>/<rel>`. No `name:` on it: ask the user and write it
  before the round goes on.
- No board: create `prds/`, report it empty, stop.
- **Nothing to read for the persona.** It is session state, not a setting:
  the session is `engineer` until it is switched, and the first round with a
  job matching another signal row asks — @references/parts/personas.md. Every
  round's line carries the active id, per @references/parts/progress.md.
- Once per session, sweep a dead session's leftovers — `analyzing` with no
  live worker → `open`, `claimed` with no live worker → `failed`. Partial code
  may exist, and a human look is cheaper than a blind retry.
- Read the worker's **output** before sweeping. `analyzing` with spec files on
  disk is an analyst that finished: the transition is `specced` with the
  specs' `complexity` summed, not `open`. `claimed` with every acceptance box
  `[x]` is an implementer that finished: collect it per step 6, and only then
  is anything left over a leftover.

A worker its infrastructure killed — API error, lost network, full disk — is
not a failed attempt:

- Resume THAT worker if it can be resumed — it holds the context, and its
  acceptance boxes are usually empty because the evidence died with it.
- First establish whether the tree is **deliberately** broken: a spec that
  watches a break fail leaves the break applied, and a worker killed in that
  window leaves broken code `claimed` does not hint at.
- Ask the worker which edit was in flight. It knows. The board does not.

**2. Answer**

- A PRD whose `## Answers` grew, or one a person moved in the view, is the
  user talking to the board — the view writes those directly.
- Collect `## Questions` from every `question` PRD. Put them to the user as one
  round per @references/drill.md — the whole frontier, numbered, each with its
  three prepared answers so answering is a pick, not an essay. Use the
  ask-user-question mechanism where one exists, the three answers as the
  options. A question depending on one still open waits for the next round. A
  `## Questions` section that is a fork with no three answers is not askable
  yet: write the three yourself, or send the analyst back for them.
- Write answers under `## Answers` (`**Q1** — <text>`), set those PRDs
  `open`. No reply: leave them `question`, work the rest — the **asks** view
  shows the same round with the same three answers as buttons.

**3. Refine**

- The analyst left the proposed split in its report. Create each child dir +
  `prd.md` (`state: open`, the child's contract as body), set the parent
  `open`.
- No usable split proposal: drill per @references/drill.md, then write that
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

- Both skips are real work. A footprint clash makes two workers edit one file.
  An unmet `needs:` sends a worker at code its dependency has not written.
- A skipped PRD stays `specced`. Say which of the two holds it, so a stalled
  board reads as a queue rather than a bug.
- The footprint is the union of the specs' `footprint:` and the PRD's own.

**6. Collect**

On each finished worker: validate the result (specs on disk / verify output
present), write the transition, commit per @references/parts/commits.md, clear
`claim:`, print the progress line, post the report with `POST /report` per
@references/parts/view.md, return to step 2.

**Collect on the transition, never at the end of the round.** A PRD whose work
is done and whose state still says `claimed` blocks every PRD that `needs:` it
and every PRD its footprint clashes with — the board holds a finished thing and
schedules around it. One worker's result is one collect.

A PRD is **finished** when every acceptance box in its specs is `[x]`. That is
not a state — it is a condition read off the specs on disk, and what step 1
sweeps for on a session that starts with work already done.

**Before `done` on work this session implemented, call the skeptic** — one
question, on your own judgment, no permission needed:
@references/parts/personas.md. You are checking your own work, which is the
one check you cannot run from inside your own frame. What it finds is advice;
the transition is still yours, and the gates below do not move.

| what is true                                                      | do                          |
|-------------------------------------------------------------------|------------------------------|
| every box `[x]`, verify output in the report, spot-checks run      | commit, `done`               |
| every box `[x]`, no verify output on record                        | run the verify commands yourself, then commit and `done` |
| boxes open, the worker is live                                     | leave it — this is progress, not a stall |
| boxes open, no live worker                                         | the sweep in step 1: `failed` |

`plan` prints the finished set before the queue, and the view leads its
frontier with it — see @references/parts/view.md.

A worker reports defects outside its own scope and never fixes them. What each
report becomes is the orchestrator's call, per @references/parts/derived.md — a
consequence for a requested PRD becomes a derived PRD with `origin: derived`
and `from:`, an instrument defect becomes a memo. Neither is `open` by default.
Check the tripwire before filing.

A finished analyst refills the pipeline. A finished implementer frees a slot.
Do not poll where results are pushed to you.

**7. Stop**

Nothing in flight and nothing dispatchable: report per-state counts, every
`question` / `refine` / `failed` PRD by name with what it needs, and the final
progress line.

- Everything left waiting on the user, and the live service up? Park
  `@resources/view/serve.py wait` in the background before stopping, per
  @references/parts/view.md — an answer written in the view then wakes the
  round that acts on it.

Report the two origins separately. Name what remains of the **deliverable**
first — requested PRDs not `done`, with `complexity`. List every `deferred`
derived PRD by name in the same breath, so parking is visible.
