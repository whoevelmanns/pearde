---
atomic: place-the-file
subject: put a new file under the root its kind belongs to
date: 2026-08-28
updated: 2026-08-28
runs: 2
---

# place-the-file — the right root, before the first line of content

## Do

1. Pick the root from what the file is, per @index.md: markdown somebody reads
   lives under `references/`, anything executed — a script, its config, its
   data — lives under `resources/`, whole. A self-contained tool's own manual
   ships inside the tool.
2. Write the file at that path — or move it there: a probe file under
   `prds/<prd>/probe/` is untracked, so it is `mv`, not `git mv`.
3. `python3 resources/index.py check` and confirm the new path is now named as
   on disk with no row. That line is the proof the map sees it, and the next
   step is what clears it.

## Done when

- The file exists at the chosen path and `git status --short` lists it.
- `python3 resources/index.py check` names exactly this path as unmapped, and
  no other path that was not already unmapped at baseline.

## Fails when

| seen | means | do |
|------|-------|----|
