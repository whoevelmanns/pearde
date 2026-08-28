---
complexity: 12
workflow: implement-a-spec
footprint:
  - references/parts/loop.md
  - references/parts/solo.md
  - references/parts/round.md
  - references/parts/workers.md
  - references/parts/commits.md
  - references/drill.md
  - README.md
  - references/system.md
  - resources/pearde.py
---

# spec03 — the round is written as the calls it makes

`loop.md` is the seven-row table with the command in the middle column and
the orchestrator's decision on the right, under 120 lines; `solo.md` the
same rows with the brief followed by hand, under 25; `round.md`'s
`## Established` says the progress line is printed and never computed;
`commits.md` loses "Gate first"; `workers.md`'s implementer block names the
`## Verify and Proof` block instead of a `verify:` key; `drill.md` § Output
writes the tree through `pearde add --body -` and `pearde refine`; the README
carries the same seven rows and "one writer per file, sequenced between
sessions"; `system.md` sends the first run to `pearde init`; `RESERVED` in
`pearde.py` is empty.

**Already in the tree from the probe:** every file above, as described. What
is left is the report's reconciliation of the harness lines the rewrite
moved — workflow-attach 47 → 42 (the three dispatch skips are `claim`'s gate;
the checker is named `pearde workflow check`), workflow-improve 73 → 70 (the
seven collect actions are `collect`'s; solo.md no longer numbers step 6's
rules), one-command 70 → 54 (`RESERVED` is empty, so the fixture copy has no
name that answers `not yet`). Those harnesses belong to other PRDs; the
implementer quotes the reds and does not edit them.

## Acceptance

- [x] `wc -l references/parts/loop.md` ≤ 120 and `wc -l references/parts/solo.md` ≤ 25
- [x] `loop.md` and `README.md` each carry exactly seven rows starting `| 1 ` … `| 7 `, and every `pearde <cmd>` named in `loop.md` answers `--help` with exit 0
- [x] `grep -ci 'never take a worker' references/parts/*.md README.md` sums to 0
- [x] `grep -c 'verify:` command' references/parts/workers.md` is 0 and `bash prds/the-board-runs-itself/brief-is-printed/probe/verify.sh` still prints `104/104`
- [x] `references/drill.md` § Output names `pearde refine <prd> < split` and `references/system.md` names `pearde init`
- [x] `python3 resources/pearde.py help` prints no `not yet` line and `python3 resources/index.py check` prints nothing

- [x] `prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh` allows `prds/.claims/` in its stray check and expects the nine `COMMANDS` names with `sweep` — prints `74 checks · 74 pass · 0 fail`
- [x] `prds/the-board-runs-itself/one-command/probe/verify.sh`'s `--help` loop is the `FORWARD` names plus `hello`, and the two reserved-name checks assert `RESERVED == {}` — prints `54 passed, 0 failed`
- [x] `prds/workflows-on-the-board/workflow-attach/probe/verify.sh` asserts the three dispatch skips as `transitions.gate_claim` refusals on fixture PRDs (`workflow:` naming nothing, `needs:` not done, a footprint a `claimed` PRD holds), and needles `and names the gate` and `` `pearde workflow check` names the file `` in `loop.md` — prints `47/47 checks pass`
- [x] `prds/workflows-on-the-board/workflow-improve/probe/verify.sh` pins the four collect-edit rules in `solo.md` beside `Apply or refuse per whose fault`, and the two step-6 count checks are deleted — the seven actions are `collect`'s — prints `71/71 checks pass`

## Verify and Proof

```sh
wc -l references/parts/loop.md references/parts/solo.md
grep -c '^| [1-7] ' references/parts/loop.md README.md
grep -ci 'never take a worker' references/parts/*.md README.md
grep -c 'verify:` command' references/parts/workers.md
sed -n '/^## Output/,$p' references/drill.md | grep -c 'pearde refine'
grep -c 'pearde init' references/system.md
python3 resources/pearde.py help | grep -c 'not yet'
bash prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh | tail -1
bash prds/the-board-runs-itself/one-command/probe/verify.sh | tail -1
bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh | tail -1
bash prds/workflows-on-the-board/workflow-improve/probe/verify.sh | tail -1
```
