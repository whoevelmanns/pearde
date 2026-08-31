---
complexity: 8
footprint:
  - resources/board/plan.py
  - resources/board/transitions.py
  - prds/the-tool-keeps-its-word/one-predicate-for-dispatchable/probe/verify.sh
---

# spec01 — `plan.dispatchable()` is the one gate, and scan, plan and claim all read it

`dispatchable(prd, prds, board=None) -> None | "<gate>: <why>"` in
`resources/board/plan.py` is the only place the claim gates are written:
`unclaimed:`, `leaf:` (a live child, or `held by <child> (parked)` — a parked
child is neither done nor coming), `container:` (children all `done`, no specs
and no open box of its own — `collect`'s, never `claim`'s), `needs:`,
`footprint:`, `workflow:`. `transitions.gate_claim` raises the string as it
stands, so every prefix `brief.py`'s `SKIP` maps survives. `compute_plan` holds
a refused `open`/`specced` PRD to the tail of the schedule (a container folds at
zero instead); `cmd_scan` calls it on the free set — a container moves to the
`collect` band, a refused PRD to `gated` with the reason on its line when no
`needs`/`after` bit already says it; `plan_frontier` and `cmd_plan` read the
same hold, and the plan's gated line carries the `wf <slug>?` mark the ready
line does.

**Already standing from the probe** (built in place — an edit to two
footprint files has no meaning outside them): the whole of the above, in
`plan.py` (`dispatchable` after `overlap`; the hold in `compute_plan`; the
split in `cmd_scan`; `plan_frontier`; `cmd_plan`) and `transitions.py`
(`gate_claim` is three lines). The probe harness passes 50/50. **Left:** run
it, confirm the untouched example's `scan` is byte-identical, confirm the
daemon re-exec'd. Nothing else — do not widen the predicate.

The contract's signature named a third argument `settings`; nothing in the
six gates reads a setting, so the third argument is `board` — the master's
library, which `workflow_marks` needs. Keep it.

## Acceptance

- [x] `grep -c '^def dispatchable(' resources/board/plan.py` prints `1`, and `resources/board/transitions.py` contains `planlib.dispatchable(prd, prds, board)` and neither `has children not done` nor `is claimed and holds`
- [x] on a copy of the example with `big/second` at `state: later`: `plan.py scan` lists `big` under `gated` with `leaf: big held by big/second (parked)` and not under `ready`; `transitions.py claim big w --board <copy>` exits 1 with the same reason and writes nothing
- [x] on a copy with `big/second` `done`: `scan` lists `big` under `collect` with `container: every child done — pearde collect closes it`; `claim big w` exits 1 with that reason and `big` stays `open`
- [x] on the same copy plus `big/specs/spec01.md`, and on one plus an open box in `big/prd.md`: `big` is under `ready` and `claim big w` exits 0
- [x] `bash prds/the-tool-keeps-its-word/one-predicate-for-dispatchable/probe/verify.sh` ends `50 checks · 50 pass · 0 fail`
- [x] `plan.py scan` on an untouched copy of the example (files `touch`ed first) is byte-identical to the same command run by `HEAD`'s `plan.py` (copied beside its siblings under `mktemp -d`, never `git stash`) — `cmp` prints nothing; a diff naming only `progress:` is the sibling's `progress_terms` hunk, not this spec's
- [x] `python3 resources/board/serve.py status` opens with `serve: up`

## Verify and Proof

```sh
bash prds/the-tool-keeps-its-word/one-predicate-for-dispatchable/probe/verify.sh
grep -c '^def dispatchable(' resources/board/plan.py
grep -c 'planlib.dispatchable(prd, prds, board)' resources/board/transitions.py
! grep -q 'has children not done' resources/board/transitions.py
T=$(mktemp -d); cp -R resources "$T/res"; git show HEAD:resources/board/plan.py > "$T/res/board/plan.py"; python3 resources/board/plan.py example "$T/a" >/dev/null; find "$T/a" -type f -exec touch {} +; python3 resources/board/plan.py scan "$T/a/prds" > "$T/new.txt"; python3 "$T/res/board/plan.py" scan "$T/a/prds" > "$T/old.txt"; cmp "$T/old.txt" "$T/new.txt" && echo identical; rm -rf "$T"
python3 resources/board/serve.py status | head -1
```
