---
complexity:          # analyst — 1-100, this unit's share of the PRD's weight
# est:               # OPTIONAL record. Nothing schedules on time; do not
#                    #   estimate duration. Price COMPUTE cost here instead,
#                    #   in the units it is spent in, when it changes scope.
# workflow:          # OPTIONAL — a slug in prds/workflows/, overriding the
#                    #   PRD's for this unit only. @references/workflow.md
footprint:           # analyst — every dir/file this spec touches; the
  - <dir/or/file>    #   orchestrator unions a PRD's footprints to avoid
  - <dir/or/file>    #   dispatching overlapping PRDs
---
<!-- Add your own keys freely. Nothing outside complexity, footprint and
     workflow is read. -->

# specNN — <one-line goal>

<What this unit delivers, in two or three sentences. ONE implementable unit per
spec file: an implementer finishes it in one sitting from this file plus the
PRD, without reading the sibling specs.>

## Acceptance

- [ ] <a concrete, observable check that can FAIL — behavior, not effort>
- [ ] <…>

<!-- The implementer ticks a box [x] only for a check it actually ran, quoting
     the output in its report — and ticks it WHEN it runs it, not in a batch
     at the end: these boxes are the only thing on the board that moves while
     a run is in flight, and the plan is drawn from them.
     Never write a box that asks for a commit or a commit message — the
     orchestrator commits the PRD on the transition that lands it. -->

## Verify and Proof

```sh
<command(s) that exercise the acceptance boxes — tests, build, lint;
the implementer runs these and quotes the output.
Scope them to this PRD's footprint: a whole-workspace command inherits every
other node's flake.>
```
