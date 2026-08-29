---
complexity: 6
footprint:
  - references/parts/loop.md
---

# spec04 — a PRD whose `workflow:` resolves to nothing is not dispatched

The PRD's `## Rules` already say it: a `workflow:` naming no workflow is a
broken PRD, and "the worker is not dispatched until it is fixed or removed".
Specs 01-03 gave that rule its instruments — `workflows.py check` names the
file, `plan.py scan` marks the line `wf <slug>?` — and no step acts on either.
A rule with no mechanism is a note.

Steps 4 and 5 of `references/parts/loop.md` already carry a skip register:
`needs:` not all `done`, and a footprint clash with a `claimed` PRD. This adds
the third skip to that same register, in the same words, and says what the
orchestrator does instead of dispatching.

The skip also has to be legible where the orchestrator reads its dispatch
list. Two of the three are already materialised by the planner — an unmet
`needs:` drops a PRD out of `ready now`, a footprint clash prints `after …
(footprint)` — so a third written into the same register, and contradicted by
the same output, is a rule the machine argues with. `cmd_plan` therefore
prints the mark on the `ready now` line as well.

That is **display only**. `compute_plan` keeps its ordering untouched: a PRD
with a dangling slug is still ordered exactly where its priority and its
weight put it, and it still comes out of the planner in `ready now`. The
refusal is the orchestrator's act, the mark is what makes the refusal
readable.

## Acceptance

- [x] Step 5's dispatch sentence in `references/parts/loop.md` names a third
      skip beside the two: skip any whose `workflow:` names no workflow.
- [x] The register below it says all three skips are real work, and says what
      the third one costs — a brief whose opening block expands to nothing —
      naming the **atomic** case as the same break.
- [x] The same register says what the orchestrator does instead of waiting:
      fix the slug or remove the key, in the same round, and names both
      instruments — the scan's `wf <slug>?` mark and `workflows.py check`,
      with `check` as the one that also reads a spec's own `workflow:`.
- [x] The "a skipped PRD stays `specced`" line asks which of the **three**
      holds it; `references/parts/loop.md` no longer says "Both skips" or
      "which of the two".
- [x] Step 4's `Dispatchable is the same test as step 5` sentence carries the
      third clause too, so the analyst stage and the implementer stage read
      one definition and not two.
- [x] `cmd_plan`'s `ready now` line prints `wf <slug>?` in the parenthetical
      beside `(unspecced)` for a PRD whose slug names no workflow, and the
      same for one naming an atomic. A slug that resolves, and a PRD with no
      key, print no `wf` there — the parenthetical is the register of what
      holds a PRD back, and a route that resolves holds back nothing.
- [x] `compute_plan` is untouched: `git diff resources/board/plan.py` shows no
      hunk inside it and mentions it nowhere, and both `plan.py scan` and
      `plan.py plan` on a board with a dangling slug still list that PRD, in
      the position its priority earns — the refusal is the orchestrator's, not
      the planner's.
- [x] The `loop.md` edit is one hunk, inside steps 4 and 5 and nothing else:
      `git diff references/parts/loop.md | grep -c '^@@'` is 1.
- [x] The paragraph is true on a master board as well as a plain one. It says
      the scan mark holds on both, and that `workflows.py check` reads one
      board's own tree only — so on a master it never reaches a member's PRDs,
      and a member PRD held by a **spec's** slug appears in neither output.
      Run `check` on the board the PRD lives on.
- [x] `python3 resources/index.py check` prints nothing this spec added.

## Verify and Proof

```sh
bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh | tail -1
git diff references/parts/loop.md | grep -c '^@@'          # 1
git diff resources/board/plan.py | grep -c 'compute_plan'  # 0
python3 resources/index.py check
```
