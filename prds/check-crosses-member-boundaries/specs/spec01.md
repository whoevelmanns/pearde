---
complexity: 14
workflow: implement-a-spec
footprint:
  - resources/workflows.py
  - references/workflow.md
---

# spec01 — a master board's check reads its members, and resolves each slug where that PRD can see it

`board_workflow_refs` walked `os.walk(board)` and nothing else, so from a
master board the check saw none of its members' PRDs and a dangling route
inside a member was invisible from above. The same single-library lookup was
wrong in the other direction: a member PRD naming a slug the master's library
holds was called broken. This unit makes the walk cross into every board named
in `members:`, addressed `@<member>/<rel>` the way `plan.py scan` addresses it,
and makes resolution per-PRD — its own board's library first, then the
master's, the order @references/parts/workers.md sets. The libraries are asked
in turn and never merged: the library does not merge, only the refs do.

**What already stands.** All of it, in the working tree. `board_workflow_refs`
was split into `_refs_one(board, prefix)` and a crossing wrapper; `members()`
in `resources/workflows.py` borrows `plan.py`'s reader rather than parsing
`members:` a second time; `check` resolves per-PRD against a per-board library
cache and reports a member named in `members:` that is not on disk.

**What is left.** Nothing in code. The remaining work is review of the two
judgement calls below.

**The deferred import is load-bearing.** `plan.py` imports `workflows` at its
top, so `import plan` at module level in `workflows.py` closes the circle
while both are still loading. It is deferred inside `members()` on purpose and
the comment says so; moving it to the top of the file breaks both readers.

**The half that was measured impossible, and is documented rather than fixed.**
The PRD asked that a member PRD resolving in the master's library be silent
"whichever board `check` is pointed at". It cannot be. A member board carries
no `settings.md` naming its master and no back-reference; `members:` is only
ever read downward, so from below there is no master to ask. This is not
`check` lagging `scan` — `plan.py scan` pointed at the member alone marks the
same slug `wf mw?` and prints the same "names no workflow" reason. The
resolution order is implemented once, in the master's context, and from below
by nothing. Both statements of the rule are scoped to that context in the
documents — @references/parts/workflows.md says "A member PRD **on a master
board**", @references/parts/workers.md says "A **member's worker**" — and
@references/install.md:199 says members are "boards in their own right". The
user's answer is the master direction only. The PRD's Verify line is narrowed
accordingly and no box below asks for the impossible half.

## Acceptance

- [x] `check` on a master board reports a dangling `workflow:` inside a member and exits 1
- [x] the member's PRD is addressed `@<member>/<rel>`, the address `plan.py scan` prints
- [x] a member PRD whose slug resolves in the **master's** library is NOT reported when `check` is pointed at the master
- [x] a member PRD whose slug resolves in its **own** library is NOT reported, even though the master's library lacks it
- [x] a master whose members are all clean prints nothing and exits 0
- [x] a board named in `members:` and absent from disk is reported by name and path, and exits 1
- [x] a board with no `members:` behaves exactly as before — same wording, same exit codes
- [x] `references/workflow.md` states that the library does not merge, that the check crosses into members, and that resolution is own-board-first then master
- [x] `python3 resources/index.py check` exits 0 and `bash resources/doctor.sh` exits 0
- [x] `bash prds/workflows-on-the-board/workflow-reader/verify.sh` still passes at its full total

## Verify and Proof

```sh
bash prds/check-crosses-member-boundaries/probe/verify.sh
bash prds/check-crosses-member-boundaries/probe/verify.sh --vs-head
bash prds/workflows-on-the-board/workflow-reader/verify.sh
python3 resources/index.py check; echo "index=$?"
python3 resources/workflows.py check; echo "workflows=$?"
bash resources/doctor.sh >/dev/null 2>&1; echo "doctor=$?"
```

`--vs-head` re-runs the whole harness against `git show HEAD:` copies of both
readers and prints how many checks fail there. **10 of 18 fail against HEAD
and 18/18 pass against this build** — that is the proof these boxes can fail,
and the harness refuses to report success if none of them does.

Boxes 1, 2 and 6 are among the ten. Boxes 3, 4 and 5 pass against HEAD too,
**vacuously**: HEAD's master check reports nothing at all, so "is NOT
reported" holds for the wrong reason. They are only meaningful together with
box 1, which forces the check to report something before the others can say
what it must not report. Read them as a set, never one at a time. Box 7 (a
plain board is unchanged) passes against HEAD by design — it is a regression
guard on behaviour that was already correct.

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
