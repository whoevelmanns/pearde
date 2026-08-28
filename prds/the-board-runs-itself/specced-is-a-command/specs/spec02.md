---
complexity: 4
workflow: implement-a-spec
footprint:
  - references/parts/workers.md
  - references/templates/spec.md
---

# spec02 — the analyst brief ends in the block the command reads, and the prose the command enforces leaves

`references/parts/workers.md` carries the two report blocks verbatim —
`## Scores` under SPECCED and `## Split` under REFINE — and its on-return
paragraph names `pearde specced` and `pearde refine` in place of "confirm the
spec files exist, write `complexity:` and `blast-radius:`". The "two
unclosable boxes to catch" paragraph becomes what the gate does. The spec
template's comment names `pearde specced` as the file's reader and what it
refuses on. Each committed harness that reads either file still prints its
recorded count.

**What already stands** (uncommitted, in the tree — six edits, every one a
new sentence or a replaced paragraph, nothing reflowed):

- `workers.md` SPECCED bullet: "End the report with the block the
  orchestrator reads the values off, verbatim:" and the fenced `## Scores`
  block — `complexity: <N>` · `blast-radius: high|mid|low` ·
  `workflow: <slug> | none fit`.
- `workers.md` REFINE bullet: "End the report with the table `pearde refine`
  reads, verbatim:" and the fenced `## Split` table with its three columns.
- `workers.md` "On return:" — SPECCED → `pearde specced <prd> --blast <x>
  [--workflow <slug>]`; REFINE → `pearde refine <prd> < report`; QUESTION
  unchanged.
- `workers.md` "Two unclosable boxes, caught at the gate rather than by eye"
  — the refusal and the warning, one paragraph.
- `templates/spec.md` — the top comment names `pearde specced` and the five
  refusals plus the footprint warning; the `## Verify and Proof` placeholder
  says the command warns when no path is under the footprint.
- The three committed harnesses after the edits: attach `47/47`, improve
  `73/73`, reader `39/39` — the same as before them.

**What is left:** read the six edits back against `references/language.md`
and the checks below; nothing else is owed. If a harness count moved, the
edit that moved it is wrong, not the harness — the attach harness holds the
workflow block byte-identical to `workflow-attach/prd.md`, and the improve
harness reads the five collect actions of the on-return paragraph as an
ordered sequence, so neither region is touched.

## Acceptance

- [x] `grep -c '^>   ## Scores$\|^>   ## Split$' references/parts/workers.md` prints `2`, and the `## Split` header row `| child | contract | needs |` is on the line after it
- [x] `grep -c 'confirm the spec files exist\|Two unclosable boxes to catch' references/parts/workers.md` prints `0`; `grep -c 'pearde specced <prd> --blast\|pearde refine <prd> < report' references/parts/workers.md` prints `2`
- [x] `grep -c 'workflow: none fit' references/parts/workers.md` still prints `1`, and `grep -c 'pearde specced' references/templates/spec.md` prints `2`
- [x] `bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh` ends `47/47 checks pass`, `bash prds/workflows-on-the-board/workflow-improve/probe/verify.sh` ends `73/73 checks pass`, `bash prds/workflows-on-the-board/workflow-reader/verify.sh` ends `verify: 39/39 checks pass`

## Verify and Proof

```sh
grep -c '^>   ## Scores$\|^>   ## Split$' references/parts/workers.md
grep -c 'confirm the spec files exist\|Two unclosable boxes to catch' references/parts/workers.md
grep -c 'pearde specced <prd> --blast\|pearde refine <prd> < report' references/parts/workers.md
grep -c 'workflow: none fit' references/parts/workers.md
grep -c 'pearde specced' references/templates/spec.md
bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh | tail -1
bash prds/workflows-on-the-board/workflow-improve/probe/verify.sh | tail -1
bash prds/workflows-on-the-board/workflow-reader/verify.sh | tail -1
```
