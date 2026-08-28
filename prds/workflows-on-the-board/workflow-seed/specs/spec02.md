---
complexity: 8
workflow: correct-a-documented-claim
footprint:
  - references/workflow.md
  - references/templates/atomic.md
  - references/templates/workflow.md
---

# spec02 — `runs` says one collect, one count at all four sites

`workflow-improve` settled that `runs` counts one per collect: a step a
back-edge returns to counts once, and so does the atomic it landed on.
@references/parts/workflows.md says so. The rejected reading — `runs` as
"times followed" — still shipped at four sites across three files, and an
author reading a template would have written a different number into the same
field than an orchestrator reading `parts/workflows.md`.

**What already stands.** All four sites carry the settled reading:

| site                                  | now reads                                                            |
|---------------------------------------|------------------------------------------------------------------------|
| `references/workflow.md` frontmatter row | `runs the file was in — one collect, one count. Integer ≥ 0, default 0` |
| `references/workflow.md` prose          | `runs` counts the runs the file was in, not the traversals inside one   |
| `references/templates/atomic.md:6`      | `runs this file was in — one collect, one count. Integer >= 0`         |
| `references/templates/workflow.md:6`    | the same comment                                                        |

The sweep for a fifth copy ran and found two, both in PRD bodies —
`prds/workflows-on-the-board/prd.md` and
`prds/workflows-on-the-board/workflow-format/prd.md`. Neither is this PRD's to
edit; both are named in the analyst's report as findings.

**What is left.** Confirm the sweep still finds nothing under `references/` or
`resources/`, and confirm the three committed harnesses that read these files
still pass at their recorded counts.

## Acceptance

- [x] `grep -rn "times followed" references/ resources/` returns no line.
- [x] `grep -rnE "times (the|a) file was followed" references/ resources/`
      returns no line.
- [x] `references/workflow.md` contains `one collect, one count` in the `runs`
      row of the frontmatter table, and `not the traversals inside one` in
      `## How the text changes`.
- [x] `references/templates/atomic.md` and `references/templates/workflow.md`
      each contain `one collect, one count` on the commented `runs` line.
- [x] `references/parts/workflows.md` still carries `One collect, one count` —
      matched on the cell's text across its line wrap, never on its column
      padding.
- [x] `bash prds/workflows-on-the-board/workflow-reader/verify.sh` prints
      `verify: 39/39 checks pass`.
- [x] `bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh` prints
      `47/47 checks pass`.
- [x] `bash prds/workflows-on-the-board/workflow-improve/probe/verify.sh`
      prints `73/73 checks pass`.

## Verify and Proof

```sh
grep -rn "times followed" references/ resources/ && echo "STALE COPY" || echo "no stale copy"
grep -rnE "times (the|a) file was followed" references/ resources/ && echo "STALE COPY" || echo "no stale copy"
grep -c 'one collect, one count' references/workflow.md \
  references/templates/atomic.md references/templates/workflow.md
grep -n 'not the traversals inside one' references/workflow.md
tr '\n' ' ' < references/parts/workflows.md | grep -o 'One collect, *one count'
bash prds/workflows-on-the-board/workflow-reader/verify.sh | tail -1
bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh | tail -1
bash prds/workflows-on-the-board/workflow-improve/probe/verify.sh | grep -E '^[0-9]+/[0-9]+ checks'
```
