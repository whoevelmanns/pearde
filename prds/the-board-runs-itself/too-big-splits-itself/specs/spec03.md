---
complexity: 4
workflow: implement-a-spec
footprint:
  - resources/board/transitions.py
  - references/templates/prd.md
---

# spec03 — `add` says `big — expect a split`, and the template says where the split lands

`transitions.add` prints `big — expect a split` as its first output line when
the body has more than `BIG_LINES` (60) non-blank-trimmed lines or holds more
than one "When this is done" (case-insensitive), then creates the PRD `open`
exactly as before — the line gates nothing. The template's leading comment
names the two limits and says a split lands under `## Children` with the
contract above it untouched.

`resources/board/transitions.py` is not in the PRD's `footprint:` — the PRD's
`## Files` table puts the `big` line in `specs.py`, but `add` lives in
`transitions.py`; this spec widens the footprint by that one file.

**Stands from the probe:** all of it. **Left:** run the harness, tick the
boxes.

## Acceptance

- [x] on a copy of the example board, a 70-line body piped to `pearde add a big one --body -` exits 0, its first line is `big — expect a split`, the progress line follows, and `a-big-one/prd.md` is `state: open`
- [x] a body holding two `When this is done` prints the same first line
- [x] a 60-line body and a one-line body print no `big` line
- [x] `references/templates/prd.md` names `split-above` and `specs-above` and says the split lands `under `## Children``
- [x] the transitions-are-commands (74) and one-command (70) harnesses are unchanged

## Verify and Proof

```sh
bash prds/the-board-runs-itself/too-big-splits-itself/probe/verify.sh
grep -n 'big — expect a split' resources/board/transitions.py
grep -n 'split-above\|## Children' references/templates/prd.md
bash prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh | tail -1    # 74 pass
```
