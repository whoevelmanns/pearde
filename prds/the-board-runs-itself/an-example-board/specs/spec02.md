---
complexity: 6
workflow: implement-a-spec
footprint:
  - resources/board/viewtest.js
---

# spec02 — the view's gate opens a copy of the example and snapshots it as `example`

`node resources/board/viewtest.js --example` copies the example board to a
scratch directory through `plan.py example`, renders it with `plan.py gantt`,
opens the page as a file, removes the scratch on exit, and under `--snap`
writes the six views keyed by the board's own name, `example`.

## What already stands (from the probe, uncommitted in the tree)

- `--example` as the first argument: `mkdtempSync`, `plan.py example
  <scratch>`, `plan.py gantt <scratch>`, exit 2 with the step named when
  either fails, `rmSync` on exit. `--snap <dir>` and `--check <dir>` follow
  it as before.
- The normaliser also reads past `holding 40m` / `holding 1.5h` — a claim
  written at a fixed time renders a holding time that grows with the clock.
  Measured: today that string renders only in the inspector, which is not a
  snapshotted section, so the six snapshots were already stable across a
  `--snap` / `--check` pair and across an 8-day shift of `planned_at`.
- The file is shared with another session's hunk (the answered panel
  checks). Both hunks are disjoint; leave theirs.

## What is left

Run it where `playwright-core` resolves — it is not installed at the repo
root; `NODE_PATH=<dir holding playwright-core>` is enough — and tick the
boxes. Nothing in the code is known to be missing. The served code path
(`http://127.0.0.1:8443/board/<name>`) is not opened by `--example`: a
scratch copy is not registered with the daemon, and registering one would
put a deleted directory into the live registry. The round renders as picks
only on that path; on the file path the asks view shows the card without
options, and the gate's asks checks pass on one card.

## Acceptance

- [x] `node resources/board/viewtest.js --example` exits 0 and ends `35/35 passed`, with the line `no ask card failed to read its PRD  (0 of 1)`
- [x] `node resources/board/viewtest.js --example --snap <dir>` writes exactly 12 files, all named `example.<view>.html` / `example.<view>.txt` for the six views
- [x] `node resources/board/viewtest.js --example --check <dir>` right after ends `47/47 passed`
- [x] no `pearde-example-*` directory is left under the temp root after either run
- [x] `node resources/board/viewtest.js` with no argument still exits 2 with the usage line, and the usage names `--example`

## Verify and Proof

```sh
D=$(mktemp -d)
node resources/board/viewtest.js --example --snap "$D/snap" | tail -1
ls "$D/snap" | grep -c '^example\.'
node resources/board/viewtest.js --example --check "$D/snap" | tail -1
ls -d "${TMPDIR:-/tmp}"/pearde-example-* 2>/dev/null | wc -l
rm -rf "$D"
```
