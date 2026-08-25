# The board

The layout the scan walks and the progress line counts.

```
prds/
  settings.md       # board settings — @references/settings.md
  memos/            # decision records — @references/memo.md
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
- `specs/` and `memos/` hold no `prd.md`, so scan walks past both.
- A parent with children is **not dispatchable** until every child is `done`.
  Work flows to the leaves.
