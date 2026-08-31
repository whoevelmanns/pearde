---
complexity: 8
workflow: correct-a-documented-claim
footprint:
  - resources/workflows.py
  - resources/board/plan.py
  - references/workflow.md
---

# spec02 — a `workflow:` that is not a slug is a break, in both readers and in the contract

@references/parts/workflows.md says a slug naming no workflow is "a broken
PRD, not a silent one". A **list** was neither: `workflow_marks` skipped on
`isinstance(v, list)` and `board_workflow_refs` skipped on the same, so a
two-item list of slugs naming nothing was silent in `scan`, silent in `plan`'s
`ready now`, and silent in `check` at exit 0. The two readers agreed, which is
why this was a gap in the contract rather than a drift between them — and why
fixing one alone would have manufactured a drift that did not exist. This unit
writes the missing sentence into the contract and makes both readers implement
it in the same round.

**What already stands.** All of it, in the working tree. `resources/workflows.py`
carries the value out of `_refs_one` as written instead of dropping a
non-scalar, and `check` names a list and any other non-slug shape.
`resources/board/plan.py` marks a list-valued key as a break so the scan line
shows it and `blocked_reason` refuses to dispatch it. `references/workflow.md`
gained the contract sentence and two `## The check` bullets.

**What is left.** Nothing in code. One judgement call to review: the scan mark
for a list reuses the existing `?` grammar — `wf one-route,two-route?` — rather
than inventing a second marker. That is deliberate. `blocked_reason` gates on
`mark.endswith("?")`, so a distinct marker would have left a list-valued PRD
dispatchable, which is the silence this unit exists to end. The words are
separated where they are read in prose: `blocked_reason` tests the shape
directly and says "the key holds one slug — a list is a break, not an absence"
rather than the dangling-slug sentence.

**Footprint note for whoever picks this up.** `resources/board/plan.py` is a
shared file and was being edited by another session throughout this PRD's
analysis. The two hunks belonging here are in `dispatchable`/`blocked_reason`
(~1439) and `workflow_marks` (~1913). Everything else uncommitted in that file
belongs to someone else — keep the hunks disjoint and do not tidy a hunk you
do not recognise.

## Acceptance

- [x] `workflows.py check` reports a `prd.md` whose `workflow:` is a list, names the file, and exits 1
- [x] the message says the key holds one slug and that another shape is a break, not an absence
- [x] `plan.py scan` marks the same PRD's line as a break rather than printing it clean
- [x] the PRD is not dispatchable, and the reason names the shape rather than a dangling slug
- [x] a `workflow:` that is absent stays silent — absence is not a break, and a PRD needs no route
- [x] `references/workflow.md` says the key holds one slug and that any other shape is a break, and `## The check` lists it

## Verify and Proof

```sh
bash prds/check-crosses-member-boundaries/probe/verify.sh
bash prds/check-crosses-member-boundaries/probe/verify.sh --vs-head
python3 resources/index.py check; echo "index=$?"
python3 resources/workflows.py check; echo "workflows=$?"
```

Four of this unit's checks are among the ten that fail against HEAD — run
`--vs-head` to see them named. On HEAD both readers skip a list and the check
exits 0, so these are real failures before the change rather than vacuous
passes. The absence box (a missing `workflow:` stays silent) passes against
HEAD by design: it guards against a fix that over-corrects by treating
absence as a break.

## Boxes closed by the orchestrator — 2026-08-29

The implementer was killed eleven times without recording a tick — the machine
slept or the connection dropped at or before its first command, every time. I
verified the twenty-one myself against the analyst's harness rather than resume
a twelfth.

What the evidence is:

```
probe/verify.sh              verify: 18/18 checks pass
probe/verify.sh --vs-head    vs HEAD: 10 of 18 checks FAIL against the unpatched readers
workflow-reader/verify.sh    verify: 39/39 checks pass
index.py check · workflows.py check · doctor.sh    all exit 0
```

The eighteen harness checks carry the behavioural boxes; I read their labels and
mapped each to the box it closes. Four boxes are not behavioural — two assert
prose in `references/workflow.md`, two assert the gates — and I checked those
directly.

**One correction worth recording, because it is the failure this PRD is about.**
My first grep for the prose boxes returned zero for *"the library does not
merge"* and *"the key holds one slug"*, and I nearly recorded them as unmet. The
document says both — as `The library does **not** merge` and `The key holds
**one slug**`, with markdown bold inside the phrase my pattern required to be
contiguous. The check was wrong, not the work. That is the same defect this
board has found in three acceptance lines this week, and I walked into it while
verifying somebody else's.

Ticked by the orchestrator, not by a worker. The evidence above is mine and the
build is the analyst's.
