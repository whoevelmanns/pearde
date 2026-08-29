---
state: done
origin: derived
from: workflows-on-the-board/workflow-reader
priority: 45
complexity: 26
blast-radius: mid
repo: pearde
needs:
  - workflows-on-the-board/workflow-attach
footprint:
  - resources/workflows.py
  - resources/board/plan.py
  - references/workflow.md
actual: 2.4h
---

# check-crosses-member-boundaries — a master board's check reads its members' PRDs

## Deferred 2026-08-28

Parked by the user when @references/parts/derived.md's tripwire fired: three
derived PRDs live against three requested, which is the board working on
itself. The deliverable — the `workflows-on-the-board` tree — finishes first,
and the derived tree comes back as its own round with nothing half-built.

Nothing here is withdrawn. The finding stands as measured; only its place in
the queue moved.

When this is done, `python3 resources/workflows.py check` run on a master board
reports a member PRD whose `workflow:` names no workflow, and a master board
with one broken member exits 1.

## The consequence, named

`board_workflow_refs` in `resources/workflows.py` walks `os.walk(board)` and
nothing else. A member board lives on its own path — `plan.py`'s `scan` merges
them by calling `_scan_one` once per member — so from a master board the
walk sees none of them.

Measured by the `workflow-attach` implementer, `reproduced`, fixture: a master
at `$TMP/master/prds` with member `solo` at `$TMP/solo/prds` holding one PRD
carrying `workflow: no-such-route`.

| run                    | says                                                                              |
|------------------------|-------------------------------------------------------------------------------------|
| `check` on the member  | ``broken/prd.md: `workflow: no-such-route` names no workflow in the library`` · exit 1 |
| `check` on the master  | nothing · **exit 0**                                                                |
| `scan` on the master   | `specced   · @solo/broken · p10 · w5 · wf no-such-route?`                            |

This gets `workflows-on-the-board/workflow-reader` wrong — the PRD that shipped
`check` as one of the two instruments naming a dangling slug. On a master board
only one of the two fires, and the one that stays silent is the one wired into
`doctor.sh`. A green `workflows` row on a master board is not evidence that the
members are clean; today it is evidence of nothing at all.

It does **not** get `workflow-attach` wrong. The skip that PRD wrote into
@references/parts/loop.md is driven by the scan mark, which does cross, and its
text names both instruments without claiming `check` crosses.

## The other half — a false positive on a valid member board

The same walk is wrong in the other direction, and this half turns `doctor`
red on a board that is correct.

@references/parts/workers.md sets the resolution order: *a member's worker
resolves the slug against its own board's library first, then the master's*.
`plan.py scan` implements both halves. `check` implements neither — it asks
one library, the board's own.

Measured on the same fixture, `reproduced`: a member PRD carrying
`workflow: mw`, a slug the MASTER's library holds and the member's does not.

| run                   | says                                                                    |
|-----------------------|---------------------------------------------------------------------------|
| `scan` on the master  | the line, unmarked — correct, the slug resolves                            |
| `check` on the member | ``b-master/prd.md: `workflow: mw` names no workflow in the library`` — **false** |

`resources/doctor.sh:325` runs `workflows.py check "$BOARD"` against the board
it is pointed at, so this is a red `workflows` row on a valid member board. The
third dispatch skip that `workflows-on-the-board/workflow-attach` wrote into
@references/parts/loop.md then tells the orchestrator to "fix the slug or
remove the key" — which on this PRD would destroy a working one.

The blind master is inherited from `workflow-reader`. The disagreement between
the rule and the reader is `workflow-attach`'s: it wrote the resolution order
into the documents, implemented it in `scan`, and pointed `loop.md` at the
reader that does not implement it.

## The third disagreement — a list-valued `workflow:` is silent everywhere

The same shape, in a third place. `workflow:` is specified as a slug and the
Rules say a broken one is *"a broken PRD, not a silent one"*. A **list** is
neither a slug nor a break either reader recognises: `workflow_marks` skips on
`isinstance(v, list)` and `board_workflow_refs` skips on the same.

Measured by the `workflow-attach` implementer, `reproduced`, fixture: a PRD
whose `workflow:` is a two-item list of slugs that name nothing.

| run                | says            |
|--------------------|--------------------|
| `scan`             | the line, unmarked |
| `plan`'s `ready now` | `(unspecced)`, nothing more |
| `workflows.py check` | nothing, exit 0  |

Silent in all three. The two readers agree, which is why it is not a drift and
why the implementer correctly did not fix its half — fixing one would
manufacture the drift that does not exist today. It is a shape error rather
than a dangling slug, and the Contract section names what the key holds
without saying what a non-slug shape does. That sentence is what this PRD
writes, and then both readers implement it.

## Two more the readers get wrong, folded here rather than filed

The tripwire was at parity when these were found, so they join the PRD that
already owns `resources/workflows.py` and `resources/board/plan.py` instead of
becoming new nodes.

**`brief` glues a paragraph to the last bullet.** `resources/workflows.py:280`
reduces `## Use when` with `[l for l in use if l.strip()]`, dropping every
blank line, so a `## Use when` whose bullets are followed by a paragraph
renders run-on — on the one page a worker actually reads. `reproduced` by the
`workflow-seed` analyst: a draft of `probe-then-spec` with a trailing paragraph
rendered glued, and it worked around it by making the citation a bullet, so no
library file triggers it today. Gets `workflow-reader` wrong, and every future
workflow whose `## Use when` needs more than a list.

**A spec-level `workflow:` has no scan-line signal.** `plan.py scan` prints
`wf <slug>` from the PRD's key alone, so `workflow-seed`'s line shows no route
while all three of its specs carry one. @references/parts/workflows.md
describes the mark in terms of the PRD's key only, so this may be intended —
settle it here: either the mark means "the PRD's own key" and says so, or it
means "a route is attached somewhere here" and reads the specs too. Gets
`workflow-attach` wrong if the second reading was meant.

## Files

| file                     | change                                                                                                      |
|--------------------------|-----------------------------------------------------------------------------------------------------------------|
| `resources/workflows.py` | `board_workflow_refs` walks the board's members as well as the board, addressing a member's PRD the way the scan does — `@<member>/<rel>`. The member list is `plan.py`'s `members()` reading `members:` from `settings.md`; import it rather than re-parsing, one reader per format |
| `resources/workflows.py` | resolution becomes per-PRD rather than per-board: a slug resolves against the PRD's own board's library first, then its master's — the order @references/parts/workers.md already sets. That is what removes the false positive as well as the blindness; one walk fixes one half only |
| `resources/workflows.py` · `resources/board/plan.py` | a `workflow:` that is not a scalar slug is reported by both readers, in the same words — the shape error joins the dangling slug rather than passing as absence. One rule, written once in @references/workflow.md, read by the check and the mark |
| `references/workflow.md`  | the Contract line says what the key holds AND what a non-slug shape is: one slug, and anything else is a break |

## Rules

- **The library does not merge.** Only the refs do. A member resolves a slug
  against its own library first and then the master's — the order `needs:`
  resolves in, already written in @references/parts/workers.md — so a master's
  `check` has to ask that question per member, not against one flattened set.
- A member board that is missing from disk is reported, not skipped silently.
  `plan.py`'s `cmd_status` already prints `MISSING` for one; this matches it.

## Verify

- The fixture above, rebuilt: `check` on the master reports the member's
  dangling slug and exits 1.
- A master whose members are all clean: `check` silent, exit 0.
- A member PRD whose slug resolves in its **own** library but not the master's
  is not reported — the per-member resolution order holds.
- A member PRD whose slug resolves in the **master's** library but not its own
  is not reported **when `check` is pointed at the master**. That is the false
  positive above, and it is the half that makes `doctor` lie.
- ~~whichever board `check` is pointed at~~ — **narrowed, measured
  impossible.** Run against a member on its own, nothing on this board can
  find that member's master: a member carries no `settings.md` naming one and
  no back-reference, and `members:` is only ever read downward. `plan.py scan`
  fails there identically — pointed at the member it marks the same slug
  `wf mw?` — so the asymmetry is not `check` lagging `scan`, it is the
  resolution order being implemented once, in the master's context, and from
  below by nothing. The user's answer is the master direction only; a member
  run alone is documented as unable to resolve its master's library rather
  than made able to. `specs/spec01.md` carries the measurement, and
  `probe/verify.sh` carries the checks.
- `bash prds/workflows-on-the-board/workflow-reader/verify.sh` still passes, at
  whatever total it then carries.
