---
complexity: 5
workflow: implement-a-spec
footprint:
  - references/parts/states.md
  - references/parts/contract.md
  - references/parts/progress.md
---

# spec03 — the parts say the command is the gate, and nothing they said before is reflowed

`states.md` gains a fifth column, `command`, naming for each state the
command that writes it and its gate, plus one paragraph under the table
saying the command checks the gate, prints the line, exits 1 naming the gate,
that `defer` writes `deferred`, that `set --force` is the escape hatch, and
that the view's drag is the same function forced. `contract.md`'s `state` row
says it is written by the transition command and never by hand; its `claim`
row says `claim` writes it and `release`/`retry` clear it. `progress.md`
opens with "Printed by the tool", naming the commands and the one term they
cannot know. Every edit is additive; no existing row is re-aligned, because
`prds/workflows-on-the-board/workflow-attach/probe/verify.sh` matches
`contract.md`'s `workflow` rows by their padding.

## What stands from the probe

All three edits are in the tree (`git diff --stat` on the three files: 30
insertions, 14 deletions, the deletions being the table rows the column was
added to). After them the three committed harnesses printed their baselines:
`workflow-attach` `47/47 checks pass`, `workflow-improve` `73/73 checks
pass`, `workflow-reader` `verify: 39/39 checks pass`.

## What is left

Nothing in these three files. `loop.md`'s sentences that the commands now
enforce are `the-loop-is-commands`'s to delete, and `handles.md`'s command
column is `one-command`'s — both listed in the analyst's report, neither
touched here.

## Acceptance

- [x] `grep -c '| command |' references/parts/states.md` prints `1`, and every one of the nine state rows in that table has a non-empty fifth cell
- [x] `grep -n 'Printed by the tool' references/parts/progress.md` matches, and the sentence names `PEARDE_AS`
- [x] `grep -n 'never by hand' references/parts/contract.md` matches on the `state` row
- [x] `bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh` still prints `47/47 checks pass` — the `workflow` rows of `contract.md` are byte-unchanged

## Verify and Proof

```sh
grep -c '| command |' references/parts/states.md
awk -F'|' '/^\| `(open|analyzing|refine|question|specced|claimed|blocked|done|failed)` /{ if ($6 ~ /^ *$/) print "EMPTY: " $2 }' references/parts/states.md
grep -n 'Printed by the tool' references/parts/progress.md
grep -n 'never by hand' references/parts/contract.md
grep -n '| `workflow`  | user ·' references/parts/contract.md
```
