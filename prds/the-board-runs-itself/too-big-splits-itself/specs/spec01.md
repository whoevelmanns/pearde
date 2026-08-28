---
complexity: 8
workflow: implement-a-spec
footprint:
  - references/settings.md
  - resources/board/specs.py
---

# spec01 — the two limits are settings, and `specced` refuses a set over either

`split-above` (default 40) and `specs-above` (default 6) are two rows of
`references/settings.md`, read by `specs.limits(board_path)` from the PRD's
own board's `settings.md` — a master reads each member's. `pearde specced`
sums the specs and counts the files after every per-file refusal, and refuses
the set over either limit with `over split-above: 58 > 40 — REFINE it` /
`over specs-above: 7 > 6 — REFINE it`, one line per limit, before it writes
anything; `--check` refuses the same way. `refine` already lands the split
under the parent's `## Children` (specs.py `refine`, unchanged by this PRD).

**Stands from the probe:** all of it — the two rows beside `claim-ttl`,
`LIMITS`, `limits()`, `read_specs` returning the count, the refusal in
`specced`, the module docstring. **Left:** run the harness, tick the boxes.

## Acceptance

- [x] `references/settings.md` has a table row for `split-above` at 40 and one for `specs-above` at 6, each naming the refusal line `specced` prints
- [x] on a copy of the example board with `big/second` set `analyzing` and seven specs of `complexity: 10`, `pearde specced big/second --blast low` exits 1 and stderr carries `over specs-above: 7 > 6 — REFINE it` and `over split-above: 70 > 40 — REFINE it`; `state:` is still `analyzing`
- [x] three specs of 20, 20, 18 exit 1 with `over split-above: 58 > 40 — REFINE it` and no `specs-above` line; `pearde settings split-above=60` on the copy makes `--check` exit 0 printing `complexity 58`
- [x] `--check` refuses a set over a limit with the same line and exit 1
- [x] a value that is not an integer (`split-above: many`) reads at the default: `specs.limits(<board>)` returns `{'split-above': 40, 'specs-above': 6}`
- [x] a `## Split` piped to `pearde refine` on the refused PRD creates the children, sets the parent `open`, writes the rows under `## Children`, and `pearde scan` lists the parent with `needs right,left`
- [x] `bash prds/the-board-runs-itself/specced-is-a-command/probe/verify.sh` still prints `verify: 90/90 checks pass`

## Verify and Proof

```sh
bash prds/the-board-runs-itself/too-big-splits-itself/probe/verify.sh
grep -c '^| `split-above` | 40 \|^| `specs-above` | 6 ' references/settings.md      # 2
grep -n 'REFINE it' resources/board/specs.py
bash prds/the-board-runs-itself/specced-is-a-command/probe/verify.sh | tail -1        # 90/90
```
