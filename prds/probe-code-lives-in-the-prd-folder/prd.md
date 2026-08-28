---
state: open
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
