---
complexity: 8
footprint:
  - resources/board/transitions.py
  - prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh
---

# spec02 — the transition row carries the window's count

`resources/board/transitions.py` `record` writes
`{"t","prd","from","to","calls","reads","refused","tokens"}` — the four new
values from `hand_over`: the live session's block for this board (the newest
file under the guard's state directory, read through `plan.py`
`guard_sessions` / `guard_block`), counter minus `mark`; then the mark moves,
`transitions` counts up and `since` is now. `tokens` is what the transcript's
output-token sum grew by — `transcript_tokens` reads the JSONL the hook input
named, counting a streamed message once by its id — and `null` when there is
no transcript or it cannot be read. With no guard file at all, every one of
the four is `null`. `.history.jsonl` is untouched.

All of this stands from the probe, built in place. What is left is the
committed harness of `transitions-are-commands`: two of its matchers assert
the old exact key set and are red by this contract — `every row is
{t,prd,from,to}` (line 139, `sorted(r)==["from","prd","t","to"]`) and `the
add row is from null` (line 142, a grep in which `"prd"` is directly followed
by `"t"`). Widen both to the eight keys; the rule each asserts — every row
carries the four, the add row is `from: null` — does not move.

## Acceptance

- [x] on a copy of the example board with the guard's block at `calls: 10`, `pearde set <prd> <state> --force` appends a row with `calls: 10`, `reads: 10`, `refused: 0`, and `tokens` equal to the transcript's output-token sum with a streamed message counted once
- [x] a second transition after three more calls, one refused, writes `calls: 3`, `refused: 1`, and `tokens` equal to the growth since the first
- [x] with `PEARDE_GUARD_STATE` naming a directory that does not exist, the row reads `"calls": null, "reads": null, "refused": null, "tokens": null`
- [x] with a guard file and no readable transcript, `tokens` is `null` and `calls` is a number
- [x] `.history.jsonl` is not created by a transition
- [x] `bash prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh` prints `74 checks · 74 pass · 0 fail`, and the two matchers now read the eight keys — the rule each asserts is unchanged

## Verify and Proof

```sh
python3 -c "import ast; ast.parse(open('resources/board/transitions.py').read())"
grep -n 'def hand_over\|def transcript_tokens' resources/board/transitions.py
bash prds/the-board-runs-itself/tokens-per-transition/probe/verify.sh </dev/null | sed -n '/^## the transition hands/,/^## status/p'
bash prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh </dev/null | tail -1
```
