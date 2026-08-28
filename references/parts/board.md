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
- A parent with children is **not dispatchable** until every child is `done`.
  Work flows to the leaves.
