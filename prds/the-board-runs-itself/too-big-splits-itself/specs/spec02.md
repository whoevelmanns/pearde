---
complexity: 6
workflow: implement-a-spec
footprint:
  - references/parts/workers.md
  - resources/board/brief.py
  - prds/the-board-runs-itself/brief-is-printed/probe/verify.sh
---

# spec02 — the analyst brief carries both numbers, filled from `settings.md`

Inside the `<!-- brief:analyst -->` block of `references/parts/workers.md`, one
added paragraph before "Spec what this PRD asks for": a build whose specs would
sum above `<split_above>` or count above `<specs_above>` returns REFINE, never
SPECCED. The placeholder table names both, and `brief.py` fills them from
`specs.limits(prd["board_path"])`. The placeholders are `_`-spelled because the
table's rule (and `TOKEN_RE`) is "lowercase, `_` or `/` inside" — `<dir-name>`
in the same block must stay unfilled.

The committed `brief-is-printed` harness diffs the rendered analyst block
against `workers.md` with its placeholders filled by `sed`; its list grew by
the two new ones. The rule it asserts — the role section is the block with
the placeholders filled — is unchanged.

**Stands from the probe:** all of it, harness repair included. **Left:** run
the harnesses, tick the boxes.

## Acceptance

- [x] `python3 resources/board/brief.py --check` prints nothing and exits 0
- [x] on a copy of the example board, `pearde brief big/second` prints ``above `40` or count`` and ``above `6` returns REFINE``, and neither `<split_above>` nor `<specs_above>` unfilled
- [x] after `pearde settings split-above=50` and `specs-above=3` on the copy, the same brief prints ``above `50` `` and ``above `3` ``
- [x] the block is additive: every line of `workers.md` outside the added paragraph and the two table rows is byte-identical to `HEAD`
- [x] `bash prds/the-board-runs-itself/brief-is-printed/probe/verify.sh` prints `verify: 104/104 checks pass`; the workflow-attach (47/47), workflow-improve (73/73) and workflow-reader (39/39) harnesses are unchanged
      — closed by the orchestrator at collect on the worktree audit of HEAD 53b3d46: attach `47/47 checks pass`, improve `73/73 checks pass`; the working tree reads 39/47 and 64/73 only because `the-loop-is-commands`' uncommitted rewrite of loop.md is in it, outside this PRD

## Verify and Proof

```sh
python3 resources/board/brief.py --check; echo "rc=$?"                                # silent, 0
bash prds/the-board-runs-itself/too-big-splits-itself/probe/verify.sh
bash prds/the-board-runs-itself/brief-is-printed/probe/verify.sh | tail -1            # 104/104
git diff HEAD -- references/parts/workers.md | grep '^[-+][^-+]' | grep -vc '^+'      # 0 removed lines
```
