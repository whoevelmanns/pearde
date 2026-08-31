---
complexity: 3
footprint:
  - references/parts/states.md
  - references/parts/order.md
  - references/parts/board.md
  - prds/memos/a-parked-child-holds-the-parent.md
---

# spec02 — the prose says it once each, and the memo is decided

Three sentences, one per file, each already in place from the probe:
`states.md` — `claim` runs `plan.dispatchable`, the six gates listed, and
under the parked paragraph "A parked child holds its parent"; `board.md` —
the not-dispatchable bullet names the parked child, the container, and the
one function; `order.md` — axis 1 adds "every child `done` — a parked child
holds its parent" and names the function. **Left:** the memo.
`prds/memos/a-parked-child-holds-the-parent.md` moves to `status: decided`,
and its `## Decision` is rewritten to the decision taken: the gate's reading
won — a parked child holds its parent; both readers call `plan.dispatchable`
in `plan.py`, which also refuses a container (`container:`) so `claim` cannot
trap one at `analyzing`; the parent is listed under `gated` with `held by
<child> (parked)`. Keep `## Why`, `## Alternatives considered` and
`## Consequences` as they are — they are the record of how it was found. Add
`the-tool-keeps-its-word/one-predicate-for-dispatchable` to `prds:`.

## Acceptance

- [x] `references/parts/states.md` contains `` `claim` runs `plan.dispatchable` `` and `A parked child holds its parent`
- [x] `references/parts/board.md` contains `` is a container — `collect` closes it, `claim` refuses `` and `plan.dispatchable`
- [x] `references/parts/order.md` axis 1 contains `a parked` / `child holds its parent` and `plan.dispatchable`
- [x] `prds/memos/a-parked-child-holds-the-parent.md` has `status: decided`, a `## Decision` that no longer opens with `Open.`, and lists `the-tool-keeps-its-word/one-predicate-for-dispatchable` under `prds:`
- [x] `python3 resources/memos.py check` is green

## Verify and Proof

```sh
grep -c 'runs `plan.dispatchable`' references/parts/states.md
grep -c 'A parked child holds its parent' references/parts/states.md
grep -c 'is a container — `collect` closes it, `claim` refuses' references/parts/board.md
grep -c 'plan.dispatchable' references/parts/order.md
grep -c '^status: decided' prds/memos/a-parked-child-holds-the-parent.md
! grep -q '^Open\.' prds/memos/a-parked-child-holds-the-parent.md
grep -c 'one-predicate-for-dispatchable' prds/memos/a-parked-child-holds-the-parent.md
python3 resources/memos.py check
```
