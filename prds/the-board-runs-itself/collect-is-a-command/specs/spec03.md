---
complexity: 6
workflow: implement-a-spec
footprint:
  - resources/board/collect.py
  - references/settings.md
  - prds/the-board-runs-itself/collect-is-a-command/probe
---

# spec03 — the board's gate runs before the commit, measured against the claim's baseline

`gate:` in `prds/settings.md` is one command, default none. `collect` runs it
in the board's repo root after the specs' verify blocks and before step 3.
Red is exit 1 and no commit, like a red verify; `--fail` writes it under
`## Failure` the same way. Red is measured against what `snapshot()` recorded
at `claim:` under `prds/.claims/<prd>/gate`: a non-zero exit whose every
output line is already in the record is known and green — the line says
`gate red, known`; a line the record lacks is red. With no record, any
non-zero exit is red.

## What stands

`collect.py` reads `gate` through `board_settings()`, appends it to the check
list as `("gate", <command>, <board repo root>)`, and compares against
`baseline()["gate_lines"]`. `snapshot()` records the gate's exit and output.
`references/settings.md` carries the `gate` row. The harness proves G (red
gate stops, green gate passes) and P (known red is green; a new line is red).

## What is left

- `prds/settings.md` on this board gets `gate: bash resources/doctor.sh` —
  the one command that runs `index.py check` and `memos.py check` as its own
  rows, the three § Deliverable names. Outside this PRD's footprint; the
  orchestrator writes it. The known `index` lines then live in the snapshot,
  and a collect on this board is green while it adds none.
- The gate runs under `bash -e -o pipefail`, one script. A board that writes
  three commands on one `gate:` line joins them with `;` and reads the last
  exit, or with `&&` and stops at the first red — say which in the row when a
  board needs it.

## Acceptance

- [x] harness section G: `gate: echo gate-red; false` stops with exit 1, `gate-red` on stdout, no commit; `gate: true` collects
- [x] harness section P: with `prds/.claims/finished/gate` holding `exit 1` and `known-red`, a gate printing `known-red` and exiting 1 collects and the line says `gate red, known`; a gate that also prints `NEW-red` stops with exit 1 and no commit
- [x] `grep -c '^| `gate`' references/settings.md` prints `1`, and the row names the default `none`, the baseline under `prds/.claims/<prd>/gate`, and @references/parts/commits.md
- [x] `collect --snapshot finished` on a fixture with `gate: echo known-red; false` writes `exit 1` as the first line of `prds/.claims/finished/gate`

## Verify and Proof

```sh
bash prds/the-board-runs-itself/collect-is-a-command/probe/verify.sh
grep -c '^| `gate`' references/settings.md
grep -n '"gate"' resources/board/collect.py
```
