---
atomic: write-the-specs
subject: turn what the build stands up into implementable units
date: 2026-08-28
updated: 2026-08-28
runs: 24
---

# write-the-specs — units another worker can finish

## Do

1. One `prds/<prd>/specs/specNN.md` per implementable unit, from
   @references/templates/spec.md.
2. Frontmatter carries `complexity:` and `footprint:`. The footprints across
   the specs are what the overlap check reads, so a path in two specs is a
   decision, not an accident.
3. Every acceptance box names an output a check can read. Write the box
   spelling inside backticks in any prose about it — the matcher is
   line-based and fence-blind, so a pasted open box becomes a real one.
4. Give each spec a `## Verify and Proof` block whose every command names a
   path from that spec's own `footprint:` — a check that reads a footprint file through a script outside it (`index.py check` on `index.md`) counts as naming it. Never the whole workspace. There is
   no `verify:` frontmatter key — the template's keys are a closed set.
5. Say in each spec what already stands from the build and what is left.
6. `grep -c '^- \[ \]' prds/<prd>/specs/*.md` — every spec has at least one
   box, and none is ticked before an implementer runs it. Then
   `awk '/^```/{f=!f;next} f' prds/<prd>/specs/*.md` and read every command
   back: each must name a path from its own spec's `footprint:`.
7. `pearde specced <prd> --check --as <id>` — the gate that reads the set, writing nothing. It refuses without `--as <id>` or `PEARDE_AS` — the persona is on the line even in check mode — and refuses a file naming line and reason, and a set over `split-above` or `specs-above`.

## Done when

- Every spec has `complexity:`, `footprint:`, acceptance boxes and a
  `## Verify and Proof` block.
- No box asks for a commit message — committing is not the implementer's act.
- No command in any block runs the whole workspace.
- Each spec states what the probe already left in the tree.

## Fails when

| seen | means | do |
|------|-------|----|
| `over split-above: N > 40 — REFINE it` | the set is heavier than the board allows | weigh each spec against the siblings' spec files first; if the weight is honest at that scale the verdict is REFINE with a `## Split` table, never a lower number |
