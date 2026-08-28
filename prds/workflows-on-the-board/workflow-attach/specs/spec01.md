---
complexity: 8
footprint:
  - references/parts/contract.md
  - references/templates/prd.md
  - references/templates/spec.md
  - references/parts/workflows.md
---

# spec01 — `workflow:` is a contract key on a PRD and on a spec

The key exists in the frontmatter contract and in both templates a writer
copies from, and `references/parts/workflows.md` says what attaching one
means. Nothing reads it yet — spec02 hands it to a worker and spec03 marks it
on the scan line.

Standing after the probe: all four files are written and the probe harness
asserts them. What is left is review of the wording.

## Acceptance

- [x] `references/parts/contract.md` carries a `workflow` row in the `prd.md`
      table, naming the three writers (user, drill, orchestrator on `specced`)
      and the three readers (the brief, `workflows.py check`, the scan line).
- [x] The same file carries a `workflow` row in the `specNN.md` table saying it
      overrides the PRD's for that unit only.
- [x] The same file's defaults table says a missing `workflow` reads as none.
- [x] `references/templates/prd.md` carries the key, commented out, beside
      `repo:`, and the template's own key list mentions it.
- [x] `references/templates/spec.md` carries the key, commented out, beside
      `footprint:`, and its "nothing outside … is read" line mentions it.
- [x] Both templates still parse: `python3 resources/memos.py` frontmatter
      reader returns a mapping with no `workflow` key from either commented
      template — a commented key is absent, not empty.
- [x] `references/parts/workflows.md` has an `## Attached` section with the two
      rows, the missing-reads-as-none rule, the dangling-and-atomic break, and
      the master resolution order.
- [x] `references/parts/contract.md`'s `specNN.md` table carries a row for the
      file itself, saying the analyst writes the specs and the orchestrator may
      add one only to close a rule the PRD's own body already states — a
      requirement the PRD does not make being REFINE — and citing
      `prds/memos/the-orchestrator-may-write-a-spec.md`. Without it `spec04`,
      written by the orchestrator, has no author the contract admits.
- [x] `python3 resources/index.py check` prints nothing this spec added.

## Verify and Proof

```sh
bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh
python3 resources/index.py check
grep -c 'the-orchestrator-may-write-a-spec' references/parts/contract.md   # 1
python3 - <<'PY'
import sys; sys.path.insert(0, "resources")
from memos import parse
for p in ("references/templates/prd.md", "references/templates/spec.md"):
    fm, _, _ = parse(p)
    assert fm is not None, p
    assert "workflow" not in fm, (p, "a commented key must read as absent")
print("both templates parse, neither exposes a workflow key")
PY
```
