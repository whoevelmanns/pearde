---
complexity: 7
footprint:
  - references/parts/workflows.md
  - references/parts/workers.md
---

# spec02 — what decides an edit, and what a run counts as

`references/parts/loop.md` says the collect applies an edit "when the failure
was the atomic's". That sentence needs a table behind it or it is a judgment
call made fresh every round. `references/parts/workflows.md` gains an
`## Improved` section holding it: six rows saying which failures are applied and
which refused and why, the four rules an edit is held to, how `runs` and
`updated` move, and where the commit goes.

Two of those rules exist nowhere else. **An atomic stays one unit** — an edit
adding a second job splits the atomic and the workflow gains a row — and **the
order may change from a run** — a step that always fails until a later one has
run is in the wrong place, so the row moves and the back-edges renumber with
it. Neither is in the collect's five actions, because both change the library's
shape rather than one file's text.

`runs` is the one number here, and the format's phrase for it — "times
followed" — splits in two under a back-edge: a step taken twice was followed
twice, and was also in exactly one run. This section closes it on **one
collect, one count**, because `runs` is read to see which files are exercised,
and the alternative reads `runs: 3` off a single bad afternoon.

`references/parts/workers.md` gets the other end: the on-return rule for either
brief, and a row on the implementer's table, so an orchestrator holding a
report finds the five actions from the file that told it what to dispatch.

Standing after the probe: both files are written and asserted. What is left is
review of the wording, and of whether the six-row table is the right cut.

## Acceptance

- [x] `references/parts/workflows.md` has an `## Improved` section citing
      `references/parts/loop.md` step 6 and `references/parts/solo.md` step 5.
- [x] It carries a table whose rows map a failure to `applied` or `refused`
      with a reason: a wrong command, a stale path, a check that cannot fail
      and an unlisted failure shape are applied; the code's and the PRD's are
      refused.
- [x] It says a refusal is said out loud, names which of the two it was, and is
      recorded in `prds/.round.md` because the unchanged file records nothing.
- [x] It carries the four rules an edit is held to — from a run never from
      reading, fold don't log, an atomic stays one unit, the order may change
      from a run — each with the consequence, not just the slogan.
- [x] It says `runs` +1 on the workflow and every atomic that ran, that a step
      that `stopped` did run, that a step never reached does not count, and
      that a step taken twice by a back-edge counts once.
- [x] It says `updated` moves only on a file whose text changed, with the
      worked case: a route followed clean ten times reads `runs: 10` at its
      original `updated`.
- [x] It says `runs` is evidence and not a score, and what a `0` beside an old
      `date` means.
- [x] Its `When a file is written` table gains a third row for the collect.
- [x] `references/parts/workers.md` carries an on-return paragraph covering
      either brief, naming `## Workflow <slug>` as the trigger and citing
      `references/parts/loop.md` step 6 for the five actions.
- [x] The implementer's on-return table carries a row for a report that also
      carries `## Workflow <slug>`, whose action is the row's own state plus
      the five actions — the workflow half never overrides the verdict.
- [x] The `> Follow the workflow` block in `references/parts/workers.md` is
      byte-identical to the copy in
      `prds/workflows-on-the-board/workflow-attach/prd.md`, unchanged by this
      spec: `bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh`
      prints `47/47 checks pass`.
- [x] `bash prds/workflows-on-the-board/workflow-reader/verify.sh` prints
      `39/39 checks pass`.
- [x] `python3 resources/index.py check` prints nothing this spec added.

## Verify and Proof

```sh
bash prds/workflows-on-the-board/workflow-improve/probe/verify.sh
bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh
bash prds/workflows-on-the-board/workflow-reader/verify.sh
python3 resources/index.py check
```
