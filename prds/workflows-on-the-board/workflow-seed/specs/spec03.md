---
complexity: 14
workflow: implement-a-spec
footprint:
  - prds/workflows-on-the-board/workflow-seed/probe
---

# spec03 — the harness that measures the library, and the four-harness gate

One script that measures spec01 and spec02 and proves the format's check can
fail. Every fixture it needs is built in a directory made at run time and
removed on exit: a fixture `prd.md` left under `prds/` becomes a real PRD, and
a probe at the repo root reddens the map check for every later PRD.

**What already stands.** `prds/workflows-on-the-board/workflow-seed/probe/verify.sh`
prints `68 checks · 68 pass · 0 fail`. It enumerates the library from disk
rather than from a list it holds, so a nineteenth file added later is measured
by the same run. Its negative controls copy the real library into `$(mktemp -d)`,
break one file at a time, and assert the check catches each — `runs: -1`, a
step naming no file, and a PRD routed to an atomic — then restore and re-assert
clean.

**What is left.** Keep the four harnesses passing together. Three of them are
committed and were recorded before this PRD's first edit; breaking one is a
failure, not a finding. This harness's own gates stay scoped to what this PRD
owns: a gate that pins the whole tree's map state, or the whole install's
doctor rows, fails on other nodes' work in flight and measures the tree's worst
neighbour.

## Acceptance

- [x] `bash prds/workflows-on-the-board/workflow-seed/probe/verify.sh` exits 0
      and its last line reads `N checks · N pass · 0 fail`.
- [x] The harness builds every fixture under `$(mktemp -d)` and removes it on
      exit: after a run, `git status --porcelain` lists no new path, and
      `find prds -path '*/probe/*' -name prd.md` returns nothing.
- [x] The harness's negative controls each make
      `python3 resources/workflows.py check` exit non-zero, and each is
      restored to clean inside the same run by copying the pristine file back,
      never by a reverse substitution on a value.
- [x] No negative control substitutes on a value the library currently holds:
      each names its victim from the library at run time, rewrites the key
      whatever it holds, and asserts the fixture really differs from the
      original before asserting the check rejects it — so a control that has
      stopped breaking anything fails loudly instead of passing vacuously.
- [x] The atomic-coverage check enumerates `prds/workflows/*.md` from the
      directory. Adding an atomic that no workflow names makes the harness
      fail; removing that file makes it pass again.
- [x] The harness asserts no path this PRD wrote appears in
      `python3 resources/index.py check`, matched on paths anchored at the repo
      root and named file by file — never a substring, and never a directory
      prefix except `prds/workflows/`, which is wholly this PRD's deliverable.
      Every other unmapped path, including any pre-existing one, is reported
      and not gated: a path this PRD does not own is no more ours to require
      present than to require absent.
- [x] The three committed harnesses still print their recorded counts:
      `39/39`, `47/47`, `73/73`.

## Verify and Proof

```sh
bash prds/workflows-on-the-board/workflow-seed/probe/verify.sh; echo "exit $?"
git status --porcelain | grep -c 'workflow-seed/probe' 
find prds -path '*/probe/*' -name prd.md && echo "STRAY FIXTURE" || echo "no stray fixture"
bash prds/workflows-on-the-board/workflow-reader/verify.sh | tail -1
bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh | tail -1
bash prds/workflows-on-the-board/workflow-improve/probe/verify.sh | grep -E '^[0-9]+/[0-9]+ checks'
```
