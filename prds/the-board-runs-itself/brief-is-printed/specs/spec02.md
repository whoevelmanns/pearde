---
complexity: 6
workflow: correct-a-documented-claim
footprint:
  - references/parts/workers.md
---

# spec02 — `workers.md` says "hand it `pearde brief`" and stops restating what the command fills

The probe added the markers, the `every` block, the placeholder table and the
three probe clauses to `references/parts/workers.md` without changing a byte
of the existing text — three committed harnesses pin that file. What the
probe did not do, because it is a replacement and not an addition, is the
line the PRD's Files table names: "give each worker exactly its brief"
becomes "hand it `pearde brief`". And the parent's constraint: a sentence the
command now enforces is deleted, not restated — the member-path bullet is
the placeholder table's `<prd>` and `<repo>` rows said twice.

**Already stands from the probe:** five marker pairs, the `every` block, the
placeholder table (ten rows), the three probe clauses at the end of the
analyst block, `--check` silent on the file.

**Left:** two prose edits below. Nothing inside a marker block moves — the
`workflow-attach` harness compares the workflow block byte-for-byte with a
PRD, and `workflow-improve` reads the five collect actions between `**On
return, either brief.**` and `**Analyst**` as an ordered sequence.

## The edits

1. Lines 5–6 —
   `Give each worker exactly its brief with the placeholders filled in. \`@\` and`
   / `` `@@` resolve in @index.md.`` — become:
   `Hand each worker the output of \`pearde brief <prd>\` — one command, nothing`
   / `composed. \`@\` and \`@@\` resolve in @index.md.`
2. The bullet `- Give a member's worker real paths, never \`@<member>/…\`. \`repo\` is the PRD's`
   / `  own, else the member's repo root.` is deleted — the placeholder table's
   `<prd>` and `<repo>` rows are the one statement of it.

## Acceptance

- [x] `grep -c 'Hand each worker the output of `pearde brief <prd>`' references/parts/workers.md` prints `1`
- [x] `grep -c 'Give each worker exactly its brief' references/parts/workers.md` prints `0`
- [x] `grep -c "Give a member's worker real paths" references/parts/workers.md` prints `0`
- [x] `grep -c '^<!-- brief:' references/parts/workers.md` prints `5` and `grep -c '^<!-- /brief -->' references/parts/workers.md` prints `5`
- [x] `python3 resources/board/brief.py --check` prints nothing, exit 0 (or the probe copy, if spec01 has not landed)
- [x] `bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh` prints `47/47`, `workflow-improve` `73/73`, `workflow-reader` `39/39`

## Verify and Proof

```sh
grep -c 'Hand each worker the output of `pearde brief <prd>`' references/parts/workers.md
grep -c 'Give each worker exactly its brief' references/parts/workers.md
grep -c "Give a member's worker real paths" references/parts/workers.md
grep -c '^<!-- brief:' references/parts/workers.md; grep -c '^<!-- /brief -->' references/parts/workers.md
B=resources/board/brief.py; [ -f "$B" ] || B=prds/the-board-runs-itself/brief-is-printed/probe/brief.py; python3 "$B" --check; echo "check exit=$?"
bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh | tail -1
bash prds/workflows-on-the-board/workflow-improve/probe/verify.sh | tail -1
bash prds/workflows-on-the-board/workflow-reader/verify.sh | tail -1
```
