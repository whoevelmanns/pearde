---
memo: a-manifest-row-can-name-a-directory
kind: decision
status: decided
subject: A growing data directory gets one manifest row for the directory, not one per file
date: 2026-08-28
prds:
  - snapshots-fold-to-one-row
---

# a-manifest-row-can-name-a-directory — one row for the directory, not one per file

## Decision

`references/files.md` may carry a row naming a **directory** —
`@resources/scout/snapshots/` — and `resources/index.py check` accepts every
file under it as covered. One row per tracked file remains the rule
everywhere else; the directory row is for a place the tools keep writing to,
where the count of files is data rather than structure.

## Why

`resources/scout/snapshots/` gains a dated `.tsv` every time a scout sweep
runs. The manifest enumerated them one row at a time, so every sweep put the
repo's own gate into a red state that nobody had introduced and that no PRD
owned: on 2026-08-28 `python3 resources/index.py check` printed exactly one
problem — `resources/scout/snapshots/2026-08-28.tsv is on disk with no row in
references/files.md` — and `doctor.sh` reported `index broken · 1 problem`.

A gate that goes red on its own schedule stops being a gate. `prds/settings.md`
makes `index.py check` green part of the `done` condition for every PRD on
this board, so a permanently red line means every future transition has to
reason its way around it and decide, one at a time, that this particular red
is not theirs. That is exactly the judgment a gate exists to remove. Two PRDs
in the workflows tree already had to narrow their acceptance checks from
"the check is silent" to greps over their own footprint, and wrote a paragraph
each explaining why.

The manifest's job is to say what is in the tree and what each thing is for. A
directory of dated snapshots is one thing with one purpose; spelling it out
file by file adds no information a reader wanted and costs a red gate per
sweep.

## Alternatives considered

**Gitignore the directory and drop the row** — snapshots become machine-local
regenerable data, like `prds/.plan.json`. It lost because they are not
regenerable: the scout's star-delta is diffed against our own past snapshots
because the stargazers API is gone, so a fresh clone with no history cannot
compute a delta at all. Ignoring them throws away the only copy of the input.

**Keep enumerating, add the row by hand each sweep** — no special case in
`index.py`, the manifest stays literally one row per tracked file. It lost on
the same count that started this: the gate is red from each sweep until a
person notices, and the person who notices is whoever is next trying to close
an unrelated PRD.

## Consequences

- `resources/index.py` gains a prefix match in its `listed`/`disk`
  comparison, and both directions of that comparison have to understand it —
  a directory row must not be reported as `lists @… — not on disk` when the
  directory exists and is empty.
- A file dropped into a covered directory is now invisible to the manifest.
  That is the freedom given up: the directory row trades per-file review for
  a green gate, so a directory only earns one when its contents are data the
  tools write, never source.
- It does **not** fix `guard off — not wired in .claude/settings.json`, the
  other line `doctor.sh` reports on this tree. That is a wiring state, not a
  break, and it is the next memo's problem.
