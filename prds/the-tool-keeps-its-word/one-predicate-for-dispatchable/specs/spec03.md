---
complexity: 2
footprint:
  - prds/workflows-on-the-board/workflow-attach/probe/verify.sh
---

# spec03 — the `workflow-attach` harness reads the list the hold moved the dangling PRD to

`prds/workflows-on-the-board/workflow-attach/probe/verify.sh` asserts that
`plan`'s output marks a dangling `workflow:` slug with `wf <slug>?`. Its
`PLANOUT` captures only the `ready now` section, and `dispatchable` now holds
a dangling PRD out of that section — `claim` refuses it, so `plan` no longer
offers it — and lists it under "then, as gates clear" with the same mark. The
rule the harness asserts (the mark survives into the plan) is intact; the
matcher's range is not. Baseline 47/47, at the probe 45/47, and with the one
change below 47/47 (measured on a scratch copy). **Left:** the one line.

Line 125: `sed -n '/ready now/,/^$/p'` → `sed -n '/ready now/,/^≈/p'`. Nothing
else in the file moves.

## Acceptance

- [x] line 125 of the harness reads `PLANOUT="$(python3 "$PLAN" plan "$B" 2>&1 | sed -n '/ready now/,/^≈/p')"`
- [x] `bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh` ends `47/47 checks pass`
- [x] `git diff --stat -- prds/workflows-on-the-board/workflow-attach/probe/verify.sh` shows one file, 1 insertion, 1 deletion

## Verify and Proof

```sh
grep -c "sed -n '/ready now/,/^≈/p'" prds/workflows-on-the-board/workflow-attach/probe/verify.sh
bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh | tail -1
```
