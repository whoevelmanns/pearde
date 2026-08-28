---
complexity: 4
footprint:
  - references/parts/workflows.md
  - references/language.md
  - references/files.md
  - index.md
---

# spec03 — the folder on one page, and the four registrations

`references/parts/workflows.md` is the folder summarised for a reader
mid-round. The other three files register the new format: two rows in the
shape table, four rows in the manifest, one `@@workflows` scope.

**Stands.** All four files are written; `python3 resources/index.py scope
workflows` resolves to the four anchors.

**Left.** Nothing in this spec's footprint.

## Acceptance

- [x] `references/parts/workflows.md` names @references/workflow.md as the
      format and does not restate the frontmatter set, the steps grammar or
      the report section.
- [x] It holds what the folder contains (the two-kind table and the folder
      rules), `## When a file is written` (a new file by hand or from the
      drill at `runs: 0`; a change only from a run), and the two shapes it is
      not — a workflow engine and a searchable index.
- [x] It carries no attach section and no improve section — `workflow-attach`
      and `workflow-improve` write their own.
- [x] `references/language.md` "Shape per document" gains exactly two rows:
      `atomic | a worker, mid-step | a checklist` and `workflow | a worker,
      cold | a route`.
- [x] `references/files.md` gains one row per new file: `@references/workflow.md`
      under `references/`, `@references/parts/workflows.md` under
      `references/parts/`, and both templates under `references/templates/`.
- [x] `index.md` gains a `@@workflows` row resolving to
      @references/workflow.md · @references/parts/workflows.md · the two
      templates, and nothing else.
- [x] `python3 resources/index.py check` prints no line naming any of the
      seven paths in this PRD's footprint.

## Verify and Proof

```sh
cd /Users/feb/dev/infra/pearde
python3 resources/index.py scope workflows          # the four anchors, in order
grep -n '^| atomic \|^| workflow ' references/language.md            # 2 rows
grep -c '@references/workflow.md |\|@references/parts/workflows.md |\|@references/templates/atomic.md |\|@references/templates/workflow.md |' references/files.md   # 4
grep -n '^## ' references/parts/workflows.md        # When a file is written / The two shapes this is not
# no problem in this PRD's footprint — index.py check names the offending path first
python3 resources/index.py check | grep -E '^(index\.md|references/(workflow|parts/workflows|templates/(atomic|workflow)|language|files)\.md)'   # no output
```
