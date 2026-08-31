---
complexity: 7
workflow: implement-a-spec
footprint:
  - resources/guard.py
  - references/parts/guard.md
---

# spec02 — the guard refuses a `state:` written by hand

`guard.py pre` matched on `Edit|Write` reads the tool input, and an edit that
changes the `state:` line of a `prd.md` — or writes a new `prd.md` carrying
one — is denied naming `pearde set <prd> <state>` (or `pearde add` /
`pearde refine` for a new file). A body edit passes. A `pearde set` run
through Bash is never matched, and the board's own tools (`pearde.py`,
`resources/board/*.py`) are never refused as a repeated read. `guard.md`
carries the row, the second `PreToolUse` entry in the wiring block, and the
sentence that the refusal is a mechanism exactly where the block is wired.

**Already in the tree from the probe:** `TOOLS`, `STATE_RE`, `fm_state`,
`after_edit`, `state_by_hand` and the `Edit|Write` branch at the top of
`pre()` in guard.py; the guard.md row, block and sentences. The hook is not
wired in this repo's `.claude/settings.json` and must not be — the harness
feeds `guard.py pre` hook JSON on stdin over a temp copy of the example
board. Nothing is left to write.

## Acceptance

- [x] an `Edit` hook payload turning `state: open` into `state: specced` in `<copy>/prds/next/prd.md` prints a `permissionDecision` of `deny` whose reason contains `pearde set next specced`
- [x] the same payload changing only the `# next` title line prints nothing and exits 0
- [x] a `Write` payload whose `content` keeps the state passes; one that changes it is denied naming `pearde set`; one creating `prds/fresh/prd.md` with a `state:` is denied naming `pearde add`
- [x] a payload on `specs/x.md`, or on a `prd.md` outside any board, passes
- [x] a `Bash` payload running `pearde.py set …` passes twice in a row
- [x] `references/parts/guard.md` carries `"matcher": "Edit|Write"` and a table row naming `pearde set`
- [x] `bash resources/doctor.sh` still prints `guard off` for this repo — nothing wired it

## Verify and Proof

```sh
bash prds/the-board-runs-itself/the-loop-is-commands/probe/verify.sh 2>&1 | sed -n '/the guard: a state written by hand/,/^── sweep/p'
grep -n 'matcher": "Edit|Write' references/parts/guard.md
echo '{}' | python3 resources/guard.py pre; echo "rc=$?"
```
