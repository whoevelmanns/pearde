---
complexity: 6
footprint:
  - references/workflow.md
  - references/parts/workflows.md
  - references/settings.md
  - references/parts/board.md
  - references/files.md
  - index.md
---

# spec03 — the library on the board's own documents

Putting `workflows.py` on disk closes four open ends in the documents. The
`workflows` key gets its row in @references/settings.md, with the one line
that says how it differs from `memos:` — elsewhere is the library, not a
mirror. `workflows/` joins the layout in @references/parts/board.md, walked
past like `memos/`. @references/parts/workflows.md gets the four verbs in a
`sh` block, the way @references/parts/memos.md carries its own. And
@references/workflow.md's `## The check` names the file by anchor instead of
as a bare path — the box `workflow-format`'s spec01 struck, closed here
because only this PRD puts the file where an anchor can resolve.

**Stands.** All six files are edited and `python3 resources/index.py check`
names no line for any of them. What is left is to re-run the check and read
the six diffs once for language and for a claim the reader does not actually
make.

**Out of scope, and known.** `python3 resources/index.py check` is not
globally silent on this tree: `resources/scout/snapshots/2026-08-28.tsv` is
untracked with no row in @references/files.md, and that line predates this
work. Do not add the row and do not delete the file. The boxes below verify
this footprint, not global silence.

## Acceptance

- [x] @references/settings.md's key table has a `workflows` row, default
      `workflows/`, relative to `prds/`, saying elsewhere is the shared
      library and gets the whole check — not a read-only mirror
- [x] @references/parts/board.md's layout block shows `workflows/` with its
      `<slug>.md`, and the bullet says `specs/`, `memos/` and `workflows/`
      hold no `prd.md` so scan walks past all three
- [x] @references/parts/workflows.md carries a `sh` block with all four verbs
      and their one-line outputs, plus a paragraph saying what `brief` is for
- [x] @references/workflow.md `## The check` opens with
      `@resources/workflows.py`, not a bare path
- [x] @references/files.md has a row for `@resources/workflows.py` in the
      `resources/` section
- [x] @index.md's `@@workflows` scope resolves to `@resources/workflows.py`
      alongside the format, the part and the two templates
- [x] `python3 resources/index.py check` prints no line naming any file in
      this spec's footprint

## Verify and Proof

```sh
python3 resources/index.py check | grep -E '^(index\.md|references/(workflow|settings|files|parts/board|parts/workflows)\.md|resources/workflows\.py)' \
  && echo "a line names this footprint" || echo "no line names this footprint"
python3 resources/index.py scope workflows
grep -n 'workflows' references/settings.md references/parts/board.md references/files.md index.md
grep -n 'resources/workflows.py' references/workflow.md references/parts/workflows.md
```
