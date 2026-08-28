---
complexity: 8
footprint:
  - references/parts/workers.md
  - references/drill.md
---

# spec02 — the brief opens with the workflow, and the drill attaches one

A dispatched worker whose PRD or spec names a workflow gets one fixed block at
the top of its brief, and the drill writes `workflow:` onto a child while it
is writing the tree rather than leaving it for later.

Standing after the probe: both files are written and the probe harness asserts
the block's load-bearing sentences. What is left is review of the wording, and
the one gap named in the report — no mechanism refuses to dispatch a PRD whose
slug does not resolve; the rule is stated, the scan marks it, and the
orchestrator acts on it.

## Acceptance

- [x] `references/parts/workers.md` carries the workflow block verbatim as the
      PRD's `## The block` gives it, introduced as opening the brief
      immediately after the persona line when `workflow:` is set.
- [x] The block's surrounding rules say: no key means no block and the brief is
      unchanged; a spec's own `workflow:` overrides the PRD's for that unit and
      the report carries one `## Workflow` section per workflow followed; a
      worker never writes under `workflows/`; an unresolvable slug is not
      dispatched until it is fixed or removed; a member resolves against its
      own board's library, then the master's.
- [x] The analyst's SPECCED verdict in the same file asks the report to name
      the workflow followed, or `workflow: none fit`, and says a recurring job
      is a finding in the report and never a file the worker writes.
- [x] `references/drill.md`'s `## Output` tells the drill to attach a workflow
      as it writes the tree, names `workflows.py list` as the library and
      `## Use when` as the fit test, and says a branch nothing fits carries no
      key.
- [x] The drill edit is confined to `## Output` and adds to it rather than
      replacing it: the paragraph appears exactly once in
      `references/drill.md`, after the `## Output` heading, the section's
      original board-shape paragraph survives beside it, and no section above
      `## Output` mentions `workflow`. Tested against the file itself, never
      against a hunk count — that count moves whenever anybody else's
      uncommitted work in this file lands, and it is not ours to depend on.

## Verify and Proof

```sh
bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh
python3 - <<'EOF'
import io
s = io.open("references/drill.md", encoding="utf-8").read()
needle = "write `workflow: <slug>` on that child"
assert s.count(needle) == 1, "the paragraph must appear exactly once"
head = s.index("\\n## Output")
assert s.index(needle) > head, "the paragraph must live under ## Output"
assert "directory per decision holding a `prd.md`" in s[head:], \\
    "the original ## Output paragraph must survive"
assert "workflow" not in s[:head], "nothing above ## Output mentions it"
assert "@resources/workflows.py list" in s[head:], \\
    "## Output names the library"
assert "## Use when" in s[head:], "## Output names the fit test"
print("drill.md: confined to ## Output, added not replacing")
EOF
python3 resources/questions.py check
```
