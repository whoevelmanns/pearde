---
complexity: 5
footprint:
  - resources/doctor.sh
  - references/parts/doctor.md
---

# spec02 — the `workflows` row in doctor

A library whose steps name atomics nobody wrote is silent from the outside: it
looks exactly like a library that is fine, right up to the worker sent
nowhere. The `workflows` row is that check, sitting after `memos` in
@resources/doctor.sh and shaped like it — `off` when there is no
`workflows/`, `broken` when a file fails `python3 resources/workflows.py
check`, each problem echoed under the row with the fix beneath. Not
`--fix`-able: what a step should name is its author's to say.

Unlike `memos:`, a `workflows:` pointing elsewhere is not a foreign system
mirrored read-only — it is the library itself, shared between boards, so the
row checks it in full and says where it sits.

**Stands.** The block is in `doctor.sh` after the `memos` block and before
`questions`, and @references/parts/doctor.md carries the table row and its
bullet. All three states were exercised against scratch boards. What is left
is to re-run them and tick the boxes.

## Acceptance

- [x] `bash resources/doctor.sh` on this board prints `workflows off` while
      `prds/workflows/` is absent
- [x] On a board whose library has a failing file the row reads `broken`, the
      count line names workflows and atomics, every problem line from
      `workflows.py check` is echoed under it, and doctor exits 1
- [x] On a board whose library is clean the row reads `ok` with the two counts
- [x] An external library reports ` · shared library at <path>` on the `ok`
      row
- [x] @references/parts/doctor.md's part table has a `workflows` row between
      `memos` and `questions`, and a bullet saying what it reads and that it
      is not `--fix`-able
- [x] `doctor.sh`'s header comment lists `workflows` among the parts that need
      a board in scope
- [x] `bash -n resources/doctor.sh` is silent

## Verify and Proof

```sh
bash -n resources/doctor.sh
bash resources/doctor.sh | grep workflows
T=$(mktemp -d); mkdir -p "$T/prds/workflows"
printf -- '---\nlanguage: English\n---\n' > "$T/prds/settings.md"
printf -- '---\natomic: bad\nsubject: s\ndate: nope\n---\n\n# bad\n\n## Do\n\n1. x\n\n## Done when\n\n- x\n' > "$T/prds/workflows/bad.md"
bash resources/doctor.sh "$T" | grep -A2 workflows
sed -i.bak 's/date: nope/date: 2026-08-28/' "$T/prds/workflows/bad.md"
bash resources/doctor.sh "$T" | grep workflows
rm -rf "$T"
```
