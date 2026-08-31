---
complexity: 4
footprint:
  - resources/board/transitions.py
  - prds/memos/two-holes-the-flag-probe-found.md
  - prds/nothing-left-open/the-line-tells-the-truth/probe/verify.sh
---

# spec02 — `set --force` clears a `claim:` the target state cannot carry, and the memo says so

`--force` skips the gate, not the bookkeeping. `claim` writes `claim:` into
exactly two states — `analyzing` and `claimed` (`EDGES`) — and `release` and
`retry` clear it on every other edge. A forced move into any other state
now clears it too, before the line is printed, so the line's `ready` and
`collect` terms count the PRD as the state it is in and `brief` stops
reading it as held. `--dry` writes nothing, and forcing the state the PRD is
already in is refused with the claim intact.

## What already stands (the probe built it in place)

- `resources/board/transitions.py`: `CLAIM_STATES = ("analyzing",
  "claimed")` above `cmd_set`, and in `cmd_set` — before `transition()` —
  `if force and to not in CLAIM_STATES and not args.dry:` scan, resolve,
  and `editlib.del_key(<prd.md>, "claim")` when the state differs and
  `planlib.claim_of(prd["fm"])` holds. Nothing in `transition()` moved.
- `prds/memos/two-holes-the-flag-probe-found.md` frontmatter: `status:
  decided`.
- The probe's section B, 18 checks, green.

## What is left

The memo's `## Decision` paragraph still opens with the word `Open.` — with
`status: decided` on the file, that paragraph says what closed the two
holes: both landed in this PRD, hole 1 as spec01, hole 2 as this spec. One
sentence replaces `Open.`; the two numbered findings stay as the record of
what was found.

## Acceptance

- [ ] On a copy of the example board, `python3 resources/board/transitions.py set building open --force --as engineer --board <copy>/prds` exits 0, prints `▸ building: claimed → open · forced · done`, and `grep -c '^claim: ' <copy>/prds/building/prd.md` is 0
- [ ] `python3 resources/board/brief.py building --board <copy>/prds --as engineer` no longer prints `held`
- [ ] `set building open --force --dry --as engineer --board <copy>/prds` exits 0 and leaves `claim:` in place
- [ ] `set building claimed --force …` on a `claimed` PRD exits 1 and leaves `claim:` in place
- [ ] `set building analyzing --force …` keeps `claim:` — a claim-carrying target
- [ ] `set building deferred --force …` and `set building shelved --force …` each leave no `claim:`
- [ ] `grep -c '^status: decided' prds/memos/two-holes-the-flag-probe-found.md` is 1 and `grep -c '^Open\.' prds/memos/two-holes-the-flag-probe-found.md` is 0
- [ ] `python3 resources/memos.py check prds` prints nothing about `two-holes-the-flag-probe-found`

## Verify and Proof

```sh
bash prds/nothing-left-open/the-line-tells-the-truth/probe/verify.sh </dev/null
grep -n -E '^status:|^Open\.' prds/memos/two-holes-the-flag-probe-found.md
python3 resources/memos.py check prds 2>&1 | grep two-holes || echo memo-clean
```
