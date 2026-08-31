---
complexity: 1
footprint:
  - references/parts/states.md
  - references/parts/handles.md
---

# spec02 — the two prose lines: the way back, named where parking is

Two one-line additive edits, both already in the tree from the probe. Both files are shared with live analysts on `the-board-asks-for-itself` and `check-crosses-member-boundaries`: re-read before touching, keep to the one line each.

## What the probe already left in the tree

- `references/parts/states.md`, the parked paragraph (after "…until that child is `done`."): one sentence — `` `release <prd> open` is the way back — the one target: it clears `claim:` and files the PRD as claimable work; a parked container is `collect`'s, and `release` says so. ``
- `references/parts/handles.md`, the `park a derived PRD` row: the `defer <prd>` cell ends `; `release <prd> open` is its inverse, the one way back from any parked state`.

Left to do: nothing but the checks below; the sentence and the cell stay on one line each so a needle can read them.

## Acceptance

- [x] `grep -c 'release <prd> open. is the way back' references/parts/states.md` prints `1`, on the line directly after the parked paragraph's `until that child is \`done\`.`
- [x] `grep -c 'defer <prd>.*release <prd> open. is its inverse' references/parts/handles.md` prints `1`, and that line is still a table row (`| park a derived PRD` … `| \`pearde defer\` |`).
- [x] `python3 resources/index.py check` prints nothing and exits 0 — neither file lost an anchor.

## Verify and Proof

```sh
grep -c 'release <prd> open. is the way back' references/parts/states.md
grep -n 'park a derived PRD.*release <prd> open. is its inverse' references/parts/handles.md
python3 resources/index.py check; echo "exit=$?"
```
