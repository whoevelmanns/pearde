# The board

The layout the scan walks and the progress line counts.

```
prds/
  settings.md       # board settings — @references/settings.md
  vision.md         # where the board is going — @references/templates/vision.md
  memos/            # decision records — @references/memo.md
    <slug>.md
  workflows/        # how a kind of job is done — @references/workflow.md
    <slug>.md
  <prd-name>/
    prd.md          # frontmatter state + the request
    specs/          # analyst-written, one implementable unit per file
      spec-<name>.md
    <child-prd>/    # a sub-PRD from refine
      prd.md
```

- A directory holding `prd.md` is a PRD. A subdirectory holding its own is a
  child PRD.
- `specs/`, `memos/` and `workflows/` hold no `prd.md`, so scan walks past
  all three.
- `vision.md` is one file beside `settings.md`, not a PRD: `vision:` in one
  sentence, `terminals:` naming the PRDs whose completion is it, `edges:` for
  a dependency nobody wrote as `needs:`. How the plan reads it is
  @references/parts/order.md.
- A parent with children is **not dispatchable** until every child is `done`:
  work flows to the leaves. What that gate tests exactly — leaf, container,
  parked child, `needs:`, footprint, `workflow:` — is one function,
  `plan.dispatchable`, and it is written out once, under **The command is the
  gate** in @references/parts/states.md. `scan`'s ready band and `claim` both
  read that one function, so what the scan offers is what `claim` takes.
