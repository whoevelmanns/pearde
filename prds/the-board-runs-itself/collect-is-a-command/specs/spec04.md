---
complexity: 4
workflow: implement-a-spec
footprint:
  - references/parts/commits.md
---

# spec04 — commits.md opens with the command, and the path rules stay as the spec of step 3

@references/parts/commits.md names `collect` in its first paragraph and says
in one sentence what the command does. The scope rules below it are what step
3 does: the inherited record under `prds/.claims/<prd>/`, the stop and
`--widen <path>`, the by-hunk commit, and `commit:` riding the next collect.
The message shape gains the `widen: <path>` line. Nothing on the page is
removed — the four committed harnesses under `prds/workflows-on-the-board/`
match its lines by phrase, and every one of those phrases stays.

## What stands

The probe made the edit. `references/parts/commits.md` is modified in the
tree, uncommitted: the opening paragraph, the two bullets under **Scope**,
the `widen:` line in the message block and the sentence under it. The four
harnesses read `47/47`, `73/73`, `verify: 39/39` and `68 checks · 66 pass ·
2 fail` after the edit — the first three equal to their baseline, the fourth
a sibling's untracked harness that moved on its own paths.

## What is left

Nothing to write. The implementer reads the page once against the command as
it stands and closes the boxes. A sentence the tool now enforces that the
page still states as advice to the orchestrator — `git add` by path, the
message shape — stays: the PRD says the path rules remain as the spec of
step 3, and `the-loop-is-six-commands` is where prose the loop no longer
executes is deleted.

## Acceptance

- [x] `grep -c 'The command is `collect`' references/parts/commits.md` prints `1`, and that paragraph is the first after the title's one-line rule
- [x] `grep -c 'widen: <path>' references/parts/commits.md` prints `1`, inside the fenced message block
- [x] `grep -c 'rides the next collect' references/parts/commits.md` prints `1`
- [x] `grep -c 'prds/.claims/<prd>/' references/parts/commits.md` prints `1`
- [x] `bash prds/workflows-on-the-board/workflow-improve/probe/verify.sh` ends `73/73 checks pass` and `bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh` ends `47/47 checks pass` — the five `commits.md` phrases they grep are intact

## Verify and Proof

```sh
grep -c 'The command is `collect`' references/parts/commits.md
grep -c 'widen: <path>' references/parts/commits.md
grep -c 'rides the next collect' references/parts/commits.md
grep -c 'prds/.claims/<prd>/' references/parts/commits.md
```

The two sibling harnesses the last box names run from the repo root; they read
this footprint and are not part of it.
