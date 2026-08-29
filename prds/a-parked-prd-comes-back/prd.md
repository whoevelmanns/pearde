---
state: done
origin: requested
actual: 0.5h
commit: 0035cf0
priority: 63
complexity: 7
blast-radius: mid
repo: pearde
workflow: probe-then-spec
footprint:
  - resources/board/transitions.py
  - references/parts/states.md
  - references/parts/handles.md
---

# a-parked-prd-comes-back — `release <prd> open` accepts a parked state, so an un-park runs through the tool

When this is done, a PRD the user parked (`deferred`, or any state outside
the nine — @references/parts/states.md calls it the user's own) comes back
with `pearde release <prd> open`, and the only other way — a hand-written
`state:` — stays the edit the guard refuses.

## The consequence, named

The user parked three derived PRDs on 2026-08-28 on a stated condition: the
deliverable finishes first, the derived tree comes back afterwards. The
condition was met on 2026-08-29 and the tool could not carry it out:

```
pearde release check-crosses-member-boundaries open --as engineer
→ refused: is `deferred` — analyzing → refine|question|open, claimed → blocked|failed
```

`transitions.py`'s edge table has no edge out of a parked state, so parking
is a one-way door — the same shape as the container `collect-keeps-its-word`
closed, from the other side: the board is wired to refuse the one edit that
would carry out the user's instruction.

## The rule

- `release <prd> open` accepts a source state that is parked — `deferred`,
  or any word outside the nine — and moves it to `open`, clearing `claim:`
  and writing the transition row. No other target: a parked PRD comes back
  as claimable work, and what it needs next is the analyst's to say.
- `defer <prd>` stays the way in. The pair is named together in
  @references/parts/handles.md: `defer` parks, `release … open` un-parks.
- The refusal text for every other parked transition names the way out:
  `is <state> (parked) — release <prd> open brings it back`.
- A parked PRD that is a container (children all done, nothing of its own)
  is still not `open`'s business: `release` says so and points at `collect`.

## Files

| file | change |
|---|---|
| `resources/board/transitions.py` | the edge; the refusal text; the container case |
| `references/parts/states.md` | one sentence under the parked paragraph: the way back |
| `references/parts/handles.md` | the `defer` row names `release … open` as its inverse |

## Verify

- On a copy of the example board: `set big/second later --force`, then `release big/second open` exits 0, the line reads `later → open`, `claim:` absent, one row in `.transitions.jsonl`; `release big/second specced` exits 1 naming the one target.
- `defer big/second` then `release big/second open` round-trips; `set big/second specced --force` then `release big/second open` still refuses as today (not parked — `analyzing → open` is a live edge and always was; the first draft of this line said `analyzing` and was wrong).
- `transitions-are-commands/probe/verify.sh` (74) and `one-predicate-for-dispatchable/probe/verify.sh` (53) green, or each moved line named.
