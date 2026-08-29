---
complexity: 13
footprint:
  - resources/workflows.py
  - prds/workflows-on-the-board/workflow-reader/verify.sh
---

# spec01 — one reader of the workflow format, and the fixture that proves it

`resources/workflows.py` is the only reader of @references/workflow.md: four
verbs — `list`, `show`, `brief`, `check` — over the library at
`prds/workflows/`. It imports `parse` from @resources/memos.py rather than
growing a second frontmatter parser, and `check` reports every shape in that
file's `## The check`, including the board half a single file cannot see: a
step naming an atomic nobody wrote, and a `workflow:` on a `prd.md` or a spec
naming no workflow in the library — an atomic is a file, so naming one is
this same failure.

**Stands.** The file is on disk, uncommitted, and
`prds/workflows-on-the-board/workflow-reader/verify.sh` — a scratch library
built in a temp dir holding one clean workflow with two atomics and one file
per failure shape — reports `verify: 37/37 checks pass`. What is left is to
re-run it, tick the boxes against real output, and read the file once for
anything the fixture cannot see.

Two decisions the build made that the PRD left to the reader, and that a
re-read should either keep or change deliberately:

- **A `workflows:` pointing at a directory that does not exist** reports one
  line, `settings.md: \`workflows: …\` points at X, which does not exist`, and
  the rest of the check is skipped — @resources/memos.py's shape for the same
  case. One root cause, one line.
- **An inlined atomic's `##` sections are demoted to `####` in `brief`.** The
  PRD says the body goes *under* `### N — <atomic>`; emitted verbatim, an
  atomic's `## Do` sits above the step heading and the outline inverts, so
  step 2 appears nested inside step 1. Fenced blocks are left alone.

## Acceptance

- [x] `python3 resources/workflows.py check` on a library holding one file per
      failure shape prints that shape's line once for that file, and nothing
      for the clean files; exit 1
- [x] The shapes covered are all of @references/workflow.md `## The check`:
      absent and unterminated fence, neither and both slug keys, slug vs
      filename, a missing required key, a key outside the closed set, a
      non-ISO date, an `updated` before its `date`, a `runs` that is not an
      integer ≥ 0, an atomic with no `## Do` and one with no `## Done when`, a
      workflow with no `## Steps`, a non-contiguous `#`, a step naming no file,
      an `on failure` that is neither `stop` nor `→ N` with N earlier, and a
      `workflow:` on a `prd.md` naming no workflow
- [x] A clean library is silent and exits 0
- [x] `brief <workflow>` prints `## Use when`, then per step its table row and
      that atomic's body, in step order, with no level-2 heading left below
      the first — the inlined body sits under its `### N — <atomic>`
- [x] `brief <atomic>` exits 1 and says an atomic is shown, not briefed
- [x] `list` prints workflows before atomics, one row each, with `runs` and
      `updated`
- [x] `show <slug>` prints the file byte-for-byte
- [x] A `workflows:` pointing outside `prds/` gets the whole check, and a
      `workflows:` pointing at nothing reports it
- [x] `python3 resources/workflows.py` on a tree with no `prds/` fails naming
      `workflows:`, not `memos:`
- [x] The file is Python 3 stdlib only and imports `parse` from
      @resources/memos.py — no second frontmatter parser

## Verify and Proof

```sh
bash prds/workflows-on-the-board/workflow-reader/verify.sh
python3 resources/workflows.py check          # silent, exit 0 — no library here yet
python3 resources/workflows.py check /nonexistent-xyz; echo "exit=$?"
grep -n "^import\|^from" resources/workflows.py
```
