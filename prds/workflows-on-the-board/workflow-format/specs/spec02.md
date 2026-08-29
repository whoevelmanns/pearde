---
complexity: 6
footprint:
  - references/templates/atomic.md
  - references/templates/workflow.md
---

# spec02 — the two templates a cold reader writes from

One atomic and one workflow, commented the way @references/templates/memo.md
is: placeholders in the frontmatter, and HTML comments carrying the rule that
the placeholder cannot show.

**Stands.** Both files are written and both parse.

**Left.** Nothing.

## Acceptance

- [x] `references/templates/atomic.md` carries `atomic:`, `subject:`, `date:`
      live, and `updated:`/`runs:` commented out — the optional keys shown
      without being set.
- [x] `references/templates/workflow.md` carries the same set with
      `workflow:` as the slug key.
- [x] Each template's frontmatter comment names the closed set, the one-slug-
      key rule, the sibling template, and @references/workflow.md as the
      format.
- [x] The atomic body holds `# <slug> — …`, `## Do` numbered, `## Done when`
      as plain bullets, and `## Fails when` as `| seen | means | do |` — with
      the comment that the table is empty at `runs: 0` and filled only from a
      run.
- [x] The workflow body holds `# <slug> — …`, `## Use when` with the
      near-miss bullet, and `## Steps` as `| # | atomic | why | on failure |`
      with one `stop` row and one `→ N` row — and the comment that `→ 1` on
      every row is a list, not a workflow.
- [x] Both files parse with `parse` from @resources/memos.py: frontmatter is
      not `None`, the slug key is present, and the title is returned.
- [x] Neither template names an agent, tool, hook or vendor.

## Verify and Proof

```sh
cd /Users/feb/dev/infra/pearde
python3 - <<'PY'
import sys; sys.path.insert(0, "resources")
from memos import parse
for t in ("atomic", "workflow"):
    fm, title, body = parse(f"references/templates/{t}.md")
    assert fm is not None, f"{t}: no frontmatter fence"
    assert t in fm, f"{t}: slug key missing"
    assert ("workflow" if t == "atomic" else "atomic") not in fm, f"{t}: two slug keys"
    assert {"subject", "date"} <= set(fm), f"{t}: required key missing"
    assert title, f"{t}: no title"
    print(t, "parses:", sorted(fm), "|", title)
PY
grep -c '^## ' references/templates/atomic.md      # 3
grep -c '^## ' references/templates/workflow.md    # 2
```
