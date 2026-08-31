---
complexity: 12
workflow: implement-a-spec
footprint:
  - resources/board/transitions.py
  - references/parts/handles.md
  - references/parts/states.md
  - references/parts/progress.md
---

# spec01 — `pearde sweep`, the claim baseline, and the owed line

`transitions.py` gains what the loop's contract makes one command: `sweep
[--apply]` reads `plan.py`'s `silent_of` and lists every held claim silent
past `claim-ttl`; `claim` records its baseline under `prds/.claims/<prd>/`
through `collect.snapshot()`; `answer` lists the `prd.md` it wrote in
`prds/.claims/riders` through `collect.owe()`; and every transition line
printed from a shell ends `round file owed · as <id>`, because the guard's
reminder fires on a tool edit and never on a command.

**Already in the tree from the probe** — every line named here stands,
uncommitted: `sweep_rows`, `round_names`, `cmd_sweep`, `owed_line`,
`snapshot_claim`, `owe_path` and the `("sweep", cmd_sweep)` row in
`COMMANDS` (transitions.py 12, 25-35, 276-318, 503, 570-652, 695); the
`sweep` row and the cleared `pending` marks in `handles.md`; the `sweep
--apply` cells on `analyzing` and `claimed`, the `specced` and `done` gate
cells, and the deleted "Never take a worker's word" paragraph in `states.md`;
the command list in `progress.md`. Nothing is left to write; what is left is
to run the block below and reconcile the two harness lines it moves
(transitions-are-commands 74 → 72: `.claims/` now moves on a claim, and
`COMMANDS` exposes nine names).

## Acceptance

- [x] `pearde sweep --help` exits 0 and `pearde help` prints no `not yet` line
- [x] on a copy of the example board with `claim-ttl: 1m` and every mtime two minutes back, `pearde sweep` lists `building` with `silent 2m` and does not list `finished`
- [x] touching `src/app.py` in the copy's repo removes `building` from the list — the output is `sweep: no claim silent past claim-ttl 1m`
- [x] `pearde sweep --apply` moves the silent `claimed` PRD to `failed`, writes a `## Failure` whose first word is `swept`, clears `claim:`, and prints a line ending `· round file owed · as engineer`
- [x] `--apply` leaves an `analyzing` PRD whose `specs/` holds a file, printing `pearde specced <prd>` on its row; and leaves a claim `prds/.round.md` names, printing `named in prds/.round.md`
- [x] `pearde claim` writes `prds/.claims/<prd>/diff` and `gate`; on a board outside a git repo it still moves the state and says `claim: no baseline`
- [x] `pearde answer` lists `prds/<prd>/prd.md` in `prds/.claims/riders`
- [x] `grep -c 'pending ·' references/parts/handles.md` is 0 and `grep -ci 'never take a worker' references/parts/states.md` is 0

## Verify and Proof

```sh
bash prds/the-board-runs-itself/the-loop-is-commands/probe/verify.sh
python3 resources/pearde.py sweep --help
grep -c 'pending ·' references/parts/handles.md
grep -n 'sweep --apply' references/parts/states.md
grep -n '`sweep` · `specced`' references/parts/progress.md
python3 -c "import ast; ast.parse(open('resources/board/transitions.py').read())"
```
