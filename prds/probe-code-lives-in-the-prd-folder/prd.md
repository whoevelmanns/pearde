---
state: superseded
origin: derived
from: workflows-on-the-board
priority: 35
complexity: 0
blast-radius: low
repo: pearde
footprint:
  - references/parts/workers.md
---

# probe-code-lives-in-the-prd-folder — the analyst brief says to leave the probe, not where

## Superseded 2026-08-28

Absorbed by `the-board-runs-itself/brief-is-printed`, commit `2ae39b4`, which
made a worker's brief one command's output rather than something composed by
hand — so the probe's location and the paste-a-box rule land in the printed
brief rather than in prose a dispatcher has to remember to copy.

The contract is satisfied, not abandoned. What this file keeps is the evidence
for why the rule exists at all, all of it measured rather than argued: six
probe scripts left at the repo root took `index.py check` from one problem to
seven; a worker's own draft put 8 phantom open boxes into a `prd.md` and 9 into
a spec by quoting box spellings outside backticks; and a fixture `prd.md` under
`prds/` moved the board from 13 PRDs to 14 and the progress line from 51% to
47%. Three different ways to break a board with a probe, none of them obvious
before somebody did it.

## Deferred 2026-08-28

Parked by the user when @references/parts/derived.md's tripwire fired: three
derived PRDs live against three requested, which is the board working on
itself. The deliverable — the `workflows-on-the-board` tree — finishes first,
and the derived tree comes back as its own round with nothing half-built.

Nothing here is withdrawn. The finding stands as measured; only its place in
the queue moved.

When this is done, an analyst reading its own brief puts its probe scripts
inside the PRD folder, and a board that has just specced something still has a
green `index.py check`.

## The consequence, named

@references/parts/workers.md tells the analyst: *"Leave the probe code in the
tree, uncommitted, on every verdict — it is pass one, and the next worker
continues it."* It does not say where in the tree, so the obvious reading is
the repo root.

That breaks the gate. `resources/index.py check` wants a row in
`references/files.md` for every file on disk that git can see, and probe
scripts have none. On 2026-08-28 an analyst on `finished-counts-both-files`
left six scripts in `probe/` at the repo root and the check went from one
problem to seven. `prds/settings.md` § Deliverable makes that check green part
of `done` for every PRD on this board, so the next PRD to transition inherits
six red lines that are not its own and has to reason its way past each one.

`resources/index.py` already excludes `prds/` from the scan — `board()` at
`resources/index.py:73`. A probe inside the PRD folder it belongs to costs the
manifest nothing and sits next to the specs it produced.

## Files

| file                            | change                                                                                                  |
|---------------------------------|-----------------------------------------------------------------------------------------------------------|
| `references/parts/workers.md`   | the analyst brief's "leave the probe code in the tree" gains its location: `prds/<prd>/probe/`, with one clause saying why — `prds/` is outside the manifest scan, so the probe costs no row and travels with the PRD that produced it |
| `references/parts/workers.md`   | a second clause, for every worker and not only the analyst: probe output quoted into a PRD or a spec is backtick-quoted first. The box matcher is line-based and knows nothing about code fences, so a pasted `- [ ]` is a real box |
| `references/parts/workers.md`   | a third clause: a probe's FIXTURES are built in a temp dir at run time, never written under `prds/` — a directory holding `prd.md` anywhere under the board is a PRD, and a fixture one moves the board's own counts |

## The second consequence — pasted output plants real boxes

The implementer of `finished-counts-both-files` hit this while writing its own
evidence: `body_has_open_box` reads lines, not markdown, so quoting a box
spelling into a report plants that box. Its first draft put **8** phantom open
boxes into `prd.md` and **9** phantom acceptance boxes into `specs/spec01.md` —
`acceptance` read 17/25 and `body_has_open_box` said `True` on a PRD whose
real boxes were all closed. A PRD in that state is one the `collect` gate
refuses for a reason that exists only in its own evidence.

It fixed its own probes to emit backtick-quoted labels, because a line
starting with a backtick is not a list item. The rule has to be in the brief:
the PRD most likely to quote box spellings is the one about the matcher, and
that is exactly the PRD that cannot afford phantom boxes.

`finished-counts-both-files` widened the matcher, which makes this **strictly
more likely** — five more spellings now count.

## The third consequence — a fixture `prd.md` becomes a real PRD

`_scan_one` at `resources/board/plan.py:178` walks the whole board and admits
any directory holding `prd.md`. A probe that writes a fixture PRD under its own
folder therefore adds it to the board. Measured by the `workflow-attach`
analyst with a fixture at
`prds/workflows-on-the-board/workflow-attach/probe/fixture-scratch/prd.md`,
created and removed: the board went from 13 PRDs to 14 and the progress line
from `done 5/10 · 51%` to `done 5/11 · 47%`.

So the location rule this PRD writes is necessary but not sufficient. The brief
has to say the other half too: **fixtures go in a temp dir at run time, never
under `prds/`.** The `workflow-attach` probe already does this — `mktemp -d`
per run — and that is the shape to name.

## Rules

- The brief is handed to a worker verbatim. It says where, or the worker
  picks, and the worker picked the root twice already.
- Do not add a manifest exemption for `probe/`. The directory row decided in
  `prds/memos/a-manifest-row-can-name-a-directory.md` is for data the tools
  write; probe code is source, and source that lives outside `prds/` earns its
  row like everything else.

## Verify

- The word `probe` in @references/parts/workers.md appears with a path beside
  it, and the brief says probe output is backtick-quoted before it is pasted.
- A fresh analyst dispatch, run to SPECCED, leaves `python3 resources/index.py
  check` printing no line naming a probe script.
