---
complexity: 4
footprint:
  - references/parts/commits.md
  - references/parts/round.md
  - references/parts/solo.md
---

# spec03 — the edited file lands in the commit, the refusal lands in the round

An applied edit that never reaches a commit is a file the next session finds
dirty and cannot attribute. `references/parts/commits.md` scopes a commit to
"the union of the specs' `footprint:` and the PRD's own, plus the PRD's folder"
and forbids `git add -A`, so a workflow file is currently outside every path a
collect is allowed to add — and it must stay outside every `footprint:`,
because the library is the board's and not the PRD's. The scope sentence
therefore names it as a fourth source, and the message shape gains a
`workflow:` line so the commit says which run paid for the change.

A **refused** edit changes no file, so nothing on disk records that the run
proposed it or why it was turned down — and the next round either re-refuses it
from scratch or takes it. `references/parts/round.md` gains an `## Edits`
section for exactly that: one line per edit, applied or refused, with whose
fault the failure was.

`references/parts/solo.md` step 5 closes the loop for a session with no
workers. The orchestrator followed the route itself, so there is no report to
read and no second reader to hand it to: it writes the edit at the step that
failed, and rules 2 to 5 still hold.

Standing after the probe: all three are written and asserted. What is left is
review of the wording, and of the `workflow:` message line's shape.

## Acceptance

- [x] `references/parts/commits.md`'s `Scope:` sentence adds any workflow file
      the collect edited to the paths a commit may add.
- [x] A bullet says the edited file is added with the rest and named in the
      message, that it is the one path in the commit no `footprint:` declares,
      and why the PRD's footprint does not grow to hold it.
- [x] The message template carries a `workflow: <slug> — <what the run taught>`
      line under the spec lines.
- [x] The one-commit-per-repo paragraph says a library `workflows:` points into
      another repo commits there, same subject, and never rides the commit in
      the repo the PRD wrote.
- [x] `references/parts/round.md`'s template carries an `## Edits` section
      between `## Asked` and `## Owed`, whose row is
      `<slug> ## <section> — applied | refused · <whose fault>`.
- [x] The prose under it says why a refusal is the half that must be written
      down, and that the section is omitted rather than left empty when no
      worker returned a `## Workflow` section.
- [x] `references/parts/solo.md` step 5 says the orchestrator following a route
      itself writes the edit at the step that failed rather than collecting it,
      and names rules 2 to 5 of loop step 6 as still holding.
- [x] `prds/.round.md` is git-ignored and machine-local, so this spec adds no
      file to the tree: `git check-ignore prds/.round.md` exits 0.
- [x] `python3 resources/index.py check` prints nothing this spec added.

## Verify and Proof

```sh
bash prds/workflows-on-the-board/workflow-improve/probe/verify.sh
git check-ignore prds/.round.md && echo "round file is ignored"
python3 resources/index.py check
```
