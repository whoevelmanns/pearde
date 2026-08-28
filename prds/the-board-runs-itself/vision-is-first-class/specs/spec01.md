---
complexity: 30
workflow: implement-a-spec
footprint:
  - resources/board/plan.py
  - prds/the-board-runs-itself/vision-is-first-class/probe
---

# spec01 — `plan.py` reads the axis from `prds/vision.md` and prints it

`axis_depth` reads `vision.md` — `vision:`, `terminals:`, `edges:` — and
places every PRD by the longest serial chain to a terminal; `scan` carries
the axis on its first line and marks off-axis rows; `pearde vision` prints
the axis for a person, `--json` what `.vision.json` held, `--next` the
frontier, `--check` the doctor row; `COMMANDS` registers it. `.vision.json`
is neither read nor written, and `plane_name()` is gone.

## What stands from the probe

All of it is in the tree, uncommitted, in `resources/board/plan.py`:

- `VISION_FILE`, `read_vision`, `resolve_addr`, `vision_axis`, `axis_depth`
  — after `board_name`, where `plane_name` and the `.vision.json` reader
  were. `resolve_addr` is `resolve_need` plus the own-name rule:
  `@<name>/<rel>` with the board's `name:` is the board's own PRD.
- Depth rules copied from `vision.py`: a `done` dependent on the chain costs
  no hop (`step = d if done else d + 1`), a child edges into its parent, a
  terminal is depth 0 whatever stands behind it, a PRD reaching no terminal
  is `None`.
- `compute_plan` calls `axis_depth(board, prds)` and ranks by `axis.get(r)`
  — by rel, no address prefix, so `plane_name`/`project_name` are out of
  the ranking.
- `cmd_scan`: the first line ends ` · axis: <on> on · <off> off` over live
  PRDs when terminals are declared; the second line is `vision: <sentence>`
  whenever the file carries one; a live row off the axis carries
  `off-axis` after the `wf` bit. A board with no `vision.md` prints
  byte-identical output — measured on a temp copy of this board with the
  file removed, same md5 before and after.
- `plan_frontier(r)` names `plan`'s ready set once; `cmd_plan` and
  `vision --next` both call it.
- `vision_json`, `critical_chain`, `cmd_vision`, `_vision_cli`,
  `COMMANDS = {"vision": _vision_cli}` — the callable takes argv after the
  command name and returns the exit code; the sibling `example` command
  already registers into the same dict with the same shape.
- `main` routes `vision`; the docstring lists it.
- `prds/the-board-runs-itself/vision-is-first-class/probe/verify.sh` —
  52 assertions over a temp fixture shaped like the example board.

## What is left

- Read the hunk once against the rules below and keep it; nothing in this
  spec needs new code. The manifest rows for the new template are spec02.
- Measured on the master board (read-only): `vision --json` agrees with
  the old `vision.py` on every PRD both name (13 of 13, depth for depth).
  The one on-axis PRD the old script lacks is `@mitosys/record-shape-port`,
  whose edge into `@master/corpus-flow` only resolves under the own-name
  rule. Keep that behaviour — it is the rule the contract adds.

## Acceptance

- [x] `python3 resources/board/plan.py scan <copy of resources/board/example>` with `terminals: [big]` in its `vision.md` prints a first line ending `axis: 2 on · 4 off`, a second line `vision: …`, `off-axis` on the `next`, `asking`, `building` and `finished` rows and on neither `big` row
- [x] `python3 resources/board/plan.py vision <that copy>` prints `chain: big/second → big`, `big/second` under `depth 1`, `big` under `depth 0`, and `off-axis — 4 with no path to a terminal`
- [x] `python3 resources/board/plan.py vision --next <that copy>` lists the same PRDs in the same order as the `ready now` section of `plan` on the same copy
- [x] `python3 resources/board/plan.py vision --json <that copy>` prints `"depth": 1` for `@example/big/second`, `"depth": 0` for `@example/big`, and `@example/next` under `off_axis`
- [x] `python3 resources/board/plan.py vision --check <that copy>` prints `1 terminal · 2 on · 4 off · longest chain 1` and exits 0; with `- nowhere` added to `terminals:` it prints `terminal nowhere names no PRD` and exits 1
- [x] On the same copy with `vision.md` removed, `scan` output is byte-identical to the output before `vision.md` was added (`cmp` on the two captures)
- [x] `grep -c '"\.vision\.json"' resources/board/plan.py` prints `0` and `grep -c 'plane_name' resources/board/plan.py` prints `0`
- [x] `python3 -c 'import sys; sys.path.insert(0, "resources/board"); import plan; print("vision" in plan.COMMANDS)'` prints `True`
- [x] `bash prds/the-board-runs-itself/vision-is-first-class/probe/verify.sh` ends `verify: 52/52 checks pass`

## Verify and Proof

```sh
bash prds/the-board-runs-itself/vision-is-first-class/probe/verify.sh
grep -c '"\.vision\.json"' resources/board/plan.py
grep -c 'plane_name' resources/board/plan.py
D=$(mktemp -d); cp -R resources/board/example/. "$D"
python3 resources/board/plan.py scan "$D/prds" > "$D/before.txt"
printf -- '---\nvision: One row in every band.\nterminals:\n  - big\n---\n' > "$D/prds/vision.md"
python3 resources/board/plan.py scan "$D/prds" | head -2
python3 resources/board/plan.py vision "$D/prds"
python3 resources/board/plan.py vision --next "$D/prds"
python3 resources/board/plan.py vision --check "$D/prds"; echo "exit $?"
rm "$D/prds/vision.md"; python3 resources/board/plan.py scan "$D/prds" | cmp - "$D/before.txt" && echo byte-identical
rm -rf "$D"
```
