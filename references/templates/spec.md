---
est:                 # analyst — wall clock for one implementer run, e.g. 2h
footprint:           # analyst — every dir/file this spec will touch; the
  - <dir/or/file>    #   orchestrator unions a PRD's footprints to avoid
  - <dir/or/file>    #   dispatching overlapping PRDs
---
<!-- add your own keys freely; nothing outside est and footprint is read -->

# specNN — <one-line goal>

<What this unit delivers, in two or three sentences. ONE implementable unit
per spec file: an implementer should be able to finish it in one sitting
from this file plus the PRD, without reading the sibling specs.>

## Acceptance

- [ ] <a concrete, observable check that can FAIL — behavior, not effort>
- [ ] <…>

<!-- the implementer ticks a box [x] only for a check it actually ran,
     quoting the output in its report -->

## Verify and Proof

```sh
<command(s) that exercise the acceptance boxes — tests, build, lint;
the implementer runs these and quotes the output>
```
