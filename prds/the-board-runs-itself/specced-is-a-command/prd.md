---
state: done
origin: requested
actual: 0.6h
commit: a6e9577
priority: 66
complexity: 16
blast-radius: mid
repo: pearde
workflow: probe-then-spec
needs:
  - transitions-are-commands
footprint:
  - resources/board/specs.py
  - references/parts/workers.md
  - references/templates/spec.md
---

# specced-is-a-command — spec files on disk decide `specced`, and a split table decides children

When this is done, `specced` is granted by a command that read the spec files,
and a REFINE verdict becomes child PRDs by a command that read the analyst's
table. The model creates no directory and sums no number.

## Contract

**`pearde specced <prd> [--blast high|mid|low] [--workflow <slug>|none]`**

Reads every `specs/*.md`. Refuses, naming file and line, on:

| check | why |
|---|---|
| no `specs/` or no spec file | `specced` requires spec files on disk — @references/parts/states.md |
| `complexity` missing, not an integer, or outside 1–100 | the weight the board schedules by |
| `## Acceptance` missing, or holding no box | nothing moves while the worker works |
| `## Verify and Proof` missing, or holding no fenced `sh` block | `collect` has nothing to run |
| a box that asks the worker to commit — matches `commit the`, `commit message`, `git commit`; a box that *checks* a `commit:` key is not one | committing is the orchestrator's act — @references/parts/workers.md |
| a `workflow:` on a spec naming no workflow in the library | a route was asked for and nothing was found |

Warns, and does not refuse, on a spec with no `footprint:` — the PRD's own
then stands for it, per @references/parts/contract.md — and on a verify
block that names no path under the footprint, the whole-workspace smell.

On success: `complexity:` = the sum, `blast-radius:` from `--blast`,
`workflow:` from `--workflow` when given, state `specced`, `claim:` cleared,
the progress line.

**`pearde refine <prd> [< report]`**

Reads a `## Split` table from stdin — the block the analyst's REFINE report
ends with:

```
## Split

| child | contract | needs |
|---|---|---|
| <dir-name> | <one line — what exists when it is done> | <sibling dir names, comma-separated, or —> |
```

Creates `prds/<prd>/<child>/prd.md` per row from the template: `state: open`,
`origin`, `priority`, `repo` and `workflow` inherited from the parent, `needs:`
as given, the contract as the body's first paragraph. Sets the parent `open`.
Writes the same table into the parent under `## Children`. Prints one line per
child. Refuses a child directory that exists, a `needs` naming no sibling in the
table, and an empty table.

## Rules

- **The analyst's report ends in the block the command parses.** SPECCED ends
  with `## Scores` — `complexity: N` · `blast-radius: x` · `workflow: <slug>
  | none fit`; REFINE ends with `## Split`. @references/parts/workers.md
  carries both, verbatim.
- The orchestrator's own spec, per
  `prds/memos/the-orchestrator-may-write-a-spec.md`, goes through the same
  command — the gate does not know who wrote the file.
- `refine` never edits an existing child. A second split on the same parent
  adds the rows that are new and refuses the rest by name.

## Files

| file | change |
|---|---|
| `resources/board/specs.py` | new — `specced`, `refine`, registered through `COMMANDS` |
| `references/parts/workers.md` | the two report blocks in the analyst brief; "the orchestrator sums" leaves |
| `references/templates/spec.md` | unchanged in shape; the comment names the command that reads it |

## Verify

On a copy of the example board:

- a spec with a box reading "commit the change" → exit 1 naming the file and
  line, no write;
- `big/second` set `analyzing --force`, given two specs of 8 and 12 →
  `specced`, `complexity: 20`, one progress line; the same on `next` (still
  `open`) exits 1 naming the state;
- a `## Split` of three rows piped in → three directories, the parent `open`
  and carrying `## Children`, `scan` showing the parent gated on all three;
- the same table piped again → exit 1 naming the three existing children,
  tree unchanged.

## Report

DONE · committed · harnesses 47/47 73/73 39/39
