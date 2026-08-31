---
atomic: write-the-manifest-row
subject: give a new file its row in the manifest and its place in every scope
date: 2026-08-28
runs: 2
---

# write-the-manifest-row — the two files that point at a third

## Do

1. Add one row for the file in `references/files.md`, in the section for its
   root, as `| @<path> | <what it is> |`. Nothing else points at it.
2. Add its anchor to every Keywords row in `index.md` whose scope it changed.
   A file appears in every scope it belongs to, and the first anchor in a row
   is the file that explains the rest.
3. `grep -n '<path>' references/files.md index.md` and read the hits.

## Done when

- The path appears exactly once in `references/files.md`.
- The path appears in at least one Keywords row of `index.md`, or the report
  says which scope was considered and why none changed.
- `python3 resources/index.py check` no longer names this path.

## Fails when

| seen | means | do |
|------|-------|----|
