---
state: done
origin: requested
actual: 1.0h
commit: 646fd4f
priority: 72
complexity: 20
blast-radius: mid
repo: pearde
workflow: probe-then-spec
footprint:
  - resources/board/example
  - resources/board/plan.py
  - resources/board/viewtest.js
  - resources/index.py
  - references/files.md
---

# an-example-board — one small board every check runs against, and the quickstart walks

When this is done, `resources/board/example/prds/` is a board of eight PRDs (six directories,
two of them children)
that puts one row in every band of the pressure order, and every harness in
this repo points at a copy of it instead of building a temp fixture of its
own. It is also the board the README's quickstart opens.

## Contract

| PRD | state | is there to show |
|---|---|---|
| `landed` | `done`, `commit:`, `actual:` | the landed band, and a `commit:` a reader can follow |
| `building` | `claimed`, specs with boxes `3/5`, `claim:` 40 minutes old | in flight, a bar half full, a holding time |
| `finished` | `claimed`, every box `[x]`, `prd.md` clean | **to collect** — the band that leads every list |
| `asking` | `question`, a `## Questions` round in @references/drill.md's format, three answers each | waiting on you, rendered as picks |
| `next` | `open`, `needs: building` | gated, and what it is gated on |
| `big` | `open` parent, children `big/first` (`done`) and `big/second` (`open`) | the tree, a parent that weighs zero, work flowing to leaves |

Beside them: `settings.md` (`language: English`, `name: example`), one memo,
one workflow with two atomics, and a `README.md` in the directory saying what
each PRD is for in one line each.

## Rules

- **Copied, never run in place.** A harness copies the directory to a temp
  dir and runs there — a check that ticks a box in the example changes what
  every other check sees.
- **Dates are written, not stamped.** The claim's `started` is a fixed
  timestamp; a rendered "held 40m" grows with the clock, and the harness
  normalises it as `viewtest.js` already normalises "held 3m".
- **One row in the manifest.** `@resources/board/example/` is a directory row
  per `prds/memos/a-manifest-row-can-name-a-directory.md` — a fixture is data
  the tools read, and its file count is not structure. `index.py` learns the
  row here: an anchor ending in `/` covers every path beneath it, and a
  directory row naming nothing on disk is still reported. The snapshots row
  `@resources/scout/snapshots/` folds in the same commit — the decided but
  deferred `snapshots-fold-to-one-row`, absorbed.
- No `.plan.json`, `.round.md` or `.history.jsonl` inside it. A copy
  generates its own.
- `python3 @resources/board/plan.py example <dir>` copies it. `pearde init
  --example` will call that once `init-asks-nothing` lands.

## Files

| file | change |
|---|---|
| `resources/board/example/` | the board above, and its `README.md` |
| `resources/board/plan.py` | `example <dir>` — copy, refuse an existing non-empty dir |
| `resources/board/viewtest.js` | `--example` opens a copy; the snapshots under `--snap` are keyed `example` |
| `prds/*/probe/*.sh` on this board, `verify.sh` harnesses | point at a copy where they built a fixture of their own |
| `resources/index.py` | the trailing-`/` rule in both directions of `check()` |
| `references/files.md` | the two directory rows — example and snapshots — replacing the per-file snapshot row |

## Verify

- `python3 resources/board/plan.py scan <copy>` prints all five sections
  non-empty: collect 1, waiting on you 1, in flight 1, ready 1, gated ≥ 1.
- `node resources/board/viewtest.js --example` exits 0 and snapshots six
  views.
- `python3 resources/index.py check` is silent with both directory rows in
  place and both snapshots on disk; `touch resources/scout/nope.tsv` prints
  its line; a row `@resources/nosuchdir/` prints a line. Both removed after.
- `git status --porcelain resources/board/example` is empty after every
  harness in this repo has run once.

## Report

DONE 14/14 · commit 646fd4f · harnesses 47/47 73/73 39/39 · probe 43/43 · viewtest --example 35/35, --check 47/47
