---
complexity: 12
footprint:
  - references/workflow.md
---

# spec01 — references/workflow.md, the one home of the format

The format reference: both frontmatter sets, both bodies, the steps grammar,
the fixed report section, the check list, and the closing argument for the
board with the shapes it beat. What @references/memo.md is to memos.

**Stands.** The file is written and carries every section below.

**Struck, not left.** `## The check` names `resources/workflows.py` as a
bare path because the file is not on disk yet, and an `@` anchor to a missing
file fails `python3 resources/index.py check`. No implementer of this PRD
could ever close that box, so it is struck here and carried as a contract item
on `workflow-reader`, which lands the file and turns the path into
`@resources/workflows.py`.

## Acceptance

- [x] `references/workflow.md` opens with the two-kind table — `atomic:
      <slug>` and `workflow: <slug>`, exactly one slug key, filename equals
      slug.
- [x] `## Atomic` carries the closed key table: `atomic`, `subject`, `date`
      required; `updated`, `runs` optional — and the body table `## Do` ·
      `## Done when` · `## Fails when`.
- [x] `## Workflow` carries the same closed set with `workflow` as slug key,
      and the body table `## Use when` · `## Steps`.
- [x] `### Steps grammar` states all six rules: contiguous `#` from 1, the
      atomic as a slug in the same directory, `why` as one clause, `on
      failure` as `→ N` with N < `#` or `stop`, the back-edge taken at most
      twice, and what `stop` reports.
- [x] `## The report section` shows the fenced `## Workflow <slug>` table with
      the three outcomes and the `### Edits` line, and states that an edit is
      pasted or refused, never rewritten.
- [x] `## The check` lists every shape the check fails on, `## Do`/`## Done
      when` and the steps table included.
- [x] The closing section makes the board argument by citing
      @references/memo.md, and rejects all three shapes named in the PRD: a
      `kind:` key beside one slug key, `atomics/` as a subfolder, a dated log
      section.
- [x] No agent, tool, hook or vendor name appears in the file.
- [~] `## The check` addresses the reader as `@resources/workflows.py`, and
      `python3 resources/index.py check` stays silent on it. Struck: the two
      clauses are mutually exclusive until `resources/workflows.py` is on
      disk — `index.py check` fails an `@` anchor whose target is absent, so
      writing the anchor is what makes the check speak. Carried by
      `workflow-reader`, as a `## Files` row and a `## Verify` bullet.

## Verify and Proof

```sh
cd /Users/feb/dev/infra/pearde
# every required section, one per line
grep -n '^## Atomic$\|^## Workflow$\|^### Steps grammar$\|^## The report section$\|^## The check$\|^## Why the board' references/workflow.md
# the three rejected shapes
grep -c 'kind:` key beside\|`atomics/` as a subfolder\|A dated log section' references/workflow.md   # 3
# no dead anchor introduced by this file
python3 resources/index.py check | grep '^references/workflow.md'   # no output
```
