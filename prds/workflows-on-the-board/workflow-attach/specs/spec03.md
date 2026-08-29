---
complexity: 9
footprint:
  - resources/board/plan.py
---

# spec03 — the scan line says which workflow a PRD is on, and when it dangles

`plan.py scan` is the one call an orchestrator makes at the top of a round, so
an attached workflow has to be visible there. A PRD's line gains `· wf <slug>`,
and `· wf <slug>?` when the slug leaves the worker without a route.

Standing after the probe: `workflow_marks` and the one `bits.append` are
written, and the probe harness covers a resolving slug, a slug naming no file,
a slug naming an atomic, an absent key, an empty key, a spec's own key, and
both halves of the master resolution order.

## Acceptance

- [x] A PRD with `workflow: <slug>` naming a workflow in its board's library
      prints `wf <slug>` on its `scan` line, with no `?`.
- [x] A PRD whose slug names no file in the library prints `wf <slug>?`.
- [x] A PRD whose slug names an **atomic** prints `wf <slug>?` too — an atomic
      is a file, so the slug resolves, but a route was asked for and a single
      step was found.
- [x] A PRD with no `workflow:`, and one with an empty `workflow:`, print no
      `wf` at all.
- [x] On a master board, a member PRD resolves against its own board's library
      first and the master's second, and a slug only the master holds prints
      unmarked.
- [x] Each library is read once per `scan` call, not once per PRD:
      `workflow_marks` memoises by board path.
- [x] This spec's change is four hunks in `plan.py` — the import,
      `workflow_marks`, and one each for the two lines inside `cmd_scan`. The
      file's diff shows those four and spec04's `cmd_plan` hunk, five in all,
      named by their hunk headers rather than by a bare total, which is a
      number any other session can move.
- [x] No line the diff **adds or removes** mentions `question_counts`,
      `answers_of` or `ANSWER_LINE_RE`, so it stages apart from anything
      landing in the asks-view region. One such name appears in the diff as
      *context* — `q, a = question_counts(p)`, the call site two lines above
      the `bits.append`; the definitions themselves are ~150 lines away and
      already committed at HEAD.
- [x] `python3 resources/board/plan.py scan`, `plan`, `status` and `gantt` all
      exit 0 on this repo's own board, which carries no library at all.

## Verify and Proof

```sh
bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh
git diff resources/board/plan.py | grep '^@@'   # 4 scan-side + spec04's cmd_plan
git diff resources/board/plan.py | grep '^[+-]' | grep -v '^[+-][+-][+-]' \
  | grep -c 'question_counts\|answers_of\|ANSWER_LINE_RE'   # 0 changed lines
python3 resources/board/plan.py scan  >/dev/null && echo "scan ok"
python3 resources/board/plan.py plan  >/dev/null && echo "plan ok"
python3 resources/board/plan.py status >/dev/null && echo "status ok"
python3 resources/board/plan.py gantt >/dev/null && echo "gantt ok"
bash prds/workflows-on-the-board/workflow-reader/verify.sh | tail -1
```
