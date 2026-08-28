---
complexity: 14
workflow: add-a-file-to-the-skill
footprint:
  - resources/board/brief.py
  - resources/doctor.sh
  - references/files.md
  - references/parts/handles.md
  - prds/the-board-runs-itself/brief-is-printed/probe/verify.sh
---

# spec01 — `brief.py` lands under `resources/board/` and the dispatcher finds it

The probe built the whole command at
`prds/the-board-runs-itself/brief-is-printed/probe/brief.py`; it passes
104/104 of the probe's own harness against a copy of the example board. It
runs from `prds/` only by walking up to the skill root, and `pearde.py`
discovers `COMMANDS` in `resources/board/*.py` alone — so the file moves,
the map gets its row, and the `briefs` row of `doctor` goes from `off` to
`ok`. Nothing in the module changes for the move: `skill_root()` already
works from either place.

**Already stands from the probe:** the module (every case of the PRD's
Verify, `--check`, the consult); the `briefs` row in `resources/doctor.sh`
(prints `off` while the module is absent, `ok`/`broken` once it is there);
the harness, which prefers `resources/board/brief.py` when it exists and
falls back to the probe copy.

**Left:** the move; the manifest row; the handle row losing its `pending`
mark; the doctor header comment naming `briefs` among the rows that always
report.

## Acceptance

- [x] `resources/board/brief.py` exists and `prds/the-board-runs-itself/brief-is-printed/probe/brief.py` does not — moved, not copied
- [x] `python3 resources/pearde.py help` lists `pearde brief` with the line `the worker's brief for one PRD, or a consultant's — one command's output` and no `not yet — brief-is-printed` line, exit 0
- [x] `python3 resources/pearde.py brief big/second --board <copy>/prds` on `python3 resources/board/plan.py example <copy>` prints a first line `# brief big/second · analyst · as engineer · wf none · repo <copy>`, exit 0
- [x] `python3 resources/pearde.py brief building --board <copy>/prds` exits 1 with `held` on stderr
- [x] `bash resources/doctor.sh` prints `  briefs      ok      5 blocks in references/parts/workers.md · every placeholder named`
- [x] the comment block at the top of `resources/doctor.sh` names `briefs` among the rows that always report
- [x] `references/files.md` carries a row for `@resources/board/brief.py`, and `python3 resources/index.py check` prints no line naming `brief.py` or `brief-is-printed/probe`
- [x] the `brief` row in `references/parts/handles.md` carries no `pending` mark and names `@resources/board/brief.py`
- [x] `bash prds/the-board-runs-itself/brief-is-printed/probe/verify.sh` prints `verify: 104/104 checks pass` against the moved module
- [x] `bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh` prints `47/47`, `workflow-improve` `73/73`, `workflow-reader` `39/39`, `one-command` `70 passed, 0 failed`

## Verify and Proof

```sh
python3 resources/pearde.py help | grep -E 'pearde brief|not yet — brief'
D=$(mktemp -d); python3 resources/board/plan.py example "$D/ex" >/dev/null
python3 resources/pearde.py brief big/second --board "$D/ex/prds" | head -1
python3 resources/pearde.py brief building --board "$D/ex/prds"; echo "exit=$?"
rm -rf "$D"
bash resources/doctor.sh | grep -E '^  briefs '
python3 resources/index.py check | grep -E 'brief' ; echo "index lines naming brief: ${PIPESTATUS[1]}"
grep -n 'brief' references/files.md references/parts/handles.md
bash prds/the-board-runs-itself/brief-is-printed/probe/verify.sh | tail -1
bash prds/the-board-runs-itself/one-command/probe/verify.sh | tail -1
```
