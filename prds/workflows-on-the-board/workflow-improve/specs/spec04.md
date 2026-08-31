---
complexity: 3
footprint:
  - prds/workflows-on-the-board/workflow-improve/probe
---

# spec04 — the dry run, run rather than described

The PRD's `## Verify` is a dry run: one worker report with two edits, one the
atomic's fault and one the code's; the collect applies one, refuses one and
says which, `runs` goes 0 → 1 on the files that ran, `check` is silent, and the
commit lists the edited file. Every other spec here ships prose, and prose is
what this harness makes falsifiable.

It cannot run on this board. `prds/workflows/` does not exist —
`workflow-seed` writes it and is still `open` — so the library is built in a
temp dir at run time. It is never built under `prds/`: a file named `prd.md`
anywhere below it is read as a real PRD of this board, and a fixture that did
that would move the counts of the board it is testing.

`collect.py` beside the harness is the collect's workflow half as code. Nothing
in the shipped tree calls it and nothing should: whose fault a failure was is
the orchestrator's judgment, and a script that guessed it would be the workflow
engine the PRD rejects — so the verdict is an argument to it, and only the
mechanical half runs. It exists so the dry run has an exit code.

The harness ends in a **census**, not a summary: all five rules of the collect
enumerated, each marked with the command that catches it being skipped. Four of
the five are marked `— nothing`. That output is the spec's most useful line,
and removing it to make the harness look greener is the failure this spec
exists to prevent.

## Acceptance

- [x] `prds/workflows-on-the-board/workflow-improve/probe/verify.sh` builds its
      whole fixture library under `mktemp -d` and removes it on exit; `git
      status --short` after a run shows no new path under `prds/` beyond the
      probe folder itself.
- [x] The fixture is a workflow over three atomics, all at `runs: 0`, and
      `python3 resources/workflows.py check` on it is silent before the collect.
- [~] The fixture workflow's step 2 carries `on failure` `→ 1`, and the fixture
      report's row for it reads `failed → 1 · passed`, so the back-edge case is
      exercised and not assumed. Struck: the second clause is unreachable.
      @references/parts/workflows.md, written by this PRD, fixes the report at
      **one row per step** — a re-traversal collapses into one row with a
      compound outcome, so no well-formed report presents the same atomic
      twice, `collect.py`'s dedup branch is dead by construction, and the
      `runs == 1` assertion cannot fail. The fixture DEPICTS the back-edge and
      the prose closes the real trap — an orchestrator counting by hand off
      `failed → 1 · passed` could write `runs: 2` — but depicting is not
      exercising, and a check that cannot fail is one of the four shapes this
      PRD calls the atomic's fault.
- [x] The report carries exactly two edits under `### Edits`, one the atomic's
      fault (a stale path) and one the code's (a red tree, whose edit would
      also leave `## Done when` unable to fail).
- [x] After the collect: the applied edit's replacement text is in the atomic,
      the text it replaced is gone rather than appended to, and no dated line
      was written.
- [x] After the collect: the refused edit's atomic is byte-for-byte what it
      was apart from the `runs:` line rule 3 moves — its step `stopped`, so it
      ran — and its `updated` did not move. The harness masks that one line
      and diffs the rest, because `cmp` on the whole file would fail on rule 3
      itself and two greps would both pass on a file reflowed around them.
- [x] After the collect: `runs` is 1 on the workflow and on all three atomics,
      including the one whose step `stopped`; the atomic the back-edge returned
      to reads 1 and not 2.
- [x] After the collect: `updated` is today on the edited atomic only — not on
      the workflow, not on an atomic that ran clean, not on the refused one.
- [x] After the collect: `python3 resources/workflows.py check` is silent, and
      `list` totals four runs over four files.
- [x] A format-breaking edit is caught by `check` before the commit: a fixture
      whose step names an atomic nobody wrote makes `check` name that slug.
- [x] A file edited on the day it was written passes `check` — `updated` equal
      to `date` is not `updated` preceding it.
- [x] The harness asserts each rule of specs 01-03 by grepping the shipped
      file, and asserts that the claims stated in two files agree rather than
      only that each is present.
- [x] The harness prints the five-rule census with the enforcing command per
      rule, and four of the five read `— nothing`.
- [x] `bash prds/workflows-on-the-board/workflow-improve/probe/verify.sh` exits
      0 and prints `68/68 checks pass` or more.

## Verify and Proof

```sh
bash prds/workflows-on-the-board/workflow-improve/probe/verify.sh; echo "rc=$?"
git status --short prds/
python3 resources/board/plan.py scan | head -2    # still 14 PRDs
```
