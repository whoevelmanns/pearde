---
state: done
origin: requested
actual: 0.8h
commit: e32a0de
priority: 62
complexity: 18
blast-radius: mid
repo: pearde
workflow: probe-then-spec
needs:
  - specced-is-a-command
  - brief-is-printed
footprint:
  - resources/board/specs.py
  - resources/board/brief.py
  - resources/board/transitions.py
  - prds/the-board-runs-itself/brief-is-printed/probe/verify.sh
  - references/settings.md
  - references/parts/workers.md
  - references/templates/prd.md
---

# too-big-splits-itself — a PRD over the size limit becomes children, and nobody is asked

When this is done, a PRD whose build turns out bigger than one sitting is
split into children by the analyst's table and `pearde refine`, with the limit
a number in `settings.md` rather than a judgment, and a child that is itself
too big splits again.

## Contract

Two keys in `prds/settings.md`, both read by the analyst brief and by
`pearde specced`:

| key | default | means |
|---|---|---|
| `split-above` | 40 | a spec set whose `complexity` sums above this is REFINE, not SPECCED |
| `specs-above` | 6 | a spec set with more files than this is REFINE, not SPECCED |

- **The analyst brief carries both numbers**, filled by `pearde brief`: *a
  build whose specs would sum above `<split-above>` or count above
  `<specs-above>` returns REFINE with a `## Split` table, never SPECCED.*
- **`pearde specced` refuses a spec set over either limit** — `over
  split-above: 58 > 40 — REFINE it` — so a verdict that ignored the brief
  cannot land.
- **Loop step 3 becomes `pearde refine <prd> < report`** when
  `the-loop-is-commands` rewrites it. The model creates no directory.
- **Depth is unbounded.** A child over the limit is REFINEd in its turn; the
  parent stays non-dispatchable until every child is `done`, as today.
- `pearde add` with a body over 60 lines, or holding more than one "When this
  is done", prints `big — expect a split` on its first line and gates
  nothing.
- The parent keeps its contract as written. `refine` writes the split under
  `## Children` in the parent — the one place a reader sees where the line
  fell.

## Rules

- The numbers are the board's — a board of small repos sets them low; a
  master board reads each member's own.
- A split is the analyst's — the brief asks for the table, and the command
  materialises it. The orchestrator writes no child by hand. No usable table
  is still a drill, per @references/drill.md, and the drill writes its tree
  through `pearde refine` too.
- A REFINE on a PRD whose `complexity` is already under the limit is allowed
  — the limit forces a split; it never forbids one.

## Files

| file | change |
|---|---|
| `references/settings.md` | the two keys |
| `references/parts/workers.md` | the clause in the analyst brief, with the two placeholders |
| `resources/board/specs.py` | the two refusals in `specced`; the `big` line in `add` |
| `resources/board/brief.py` | the two placeholders |
| `references/templates/prd.md` | the comment names the limit and where a split lands |

## Verify

- `pearde brief big/second` prints the two numbers from the copy's `settings.md`;
  change a key and the brief changes.
- Seven specs of 10 with `specs-above: 6` → `pearde specced` exits 1 with
  `over specs-above: 7 > 6`.
- Three specs summing 58 with `split-above: 40` → exit 1 with `over
  split-above: 58 > 40`.
- A `## Split` piped to `refine` on that PRD → children created, parent
  `open`, parent carrying `## Children`, `scan` gating the parent on them.
- `pearde add` with a 70-line body → first line `big — expect a split`, the
  PRD created `open`.

## Report

DONE 17/17 · commit e32a0de · probe 60/60 · audited at HEAD: 47/47 73/73
