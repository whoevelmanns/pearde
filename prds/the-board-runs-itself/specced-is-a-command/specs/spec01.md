---
complexity: 12
workflow: implement-a-spec
footprint:
  - resources/board/specs.py
  - prds/the-board-runs-itself/specced-is-a-command/probe
---

# spec01 — `specced` and `refine` land at `resources/board/specs.py`, and the harness points at it

The probe built both commands whole and left them under
`probe/specs.py`, with a harness at `probe/verify.sh` that copies the example
board to a temp dir and drives 90 checks through them. This unit moves the
module to its contract path, `resources/board/specs.py`, exposing
`COMMANDS = {"specced": …, "refine": …}` for the dispatcher `one-command`
builds, and re-points the harness at it. Nothing about the behaviour changes;
the file changes address.

**What already stands** (uncommitted, in the tree):

- `probe/specs.py` — `specced` runs every check in the contract table, refuses
  naming `<file>:<line>` with one line per refusal, warns (and does not
  refuse) on a spec with no `footprint:` and on a verify block naming no
  footprint path, writes `complexity:` (the sum), `blast-radius:` and
  `workflow:` off the flags, clears `claim:`, sets `specced` from `analyzing`
  only, records the row through `transitions.record` and prints the line
  through `transitions.progress_line`. `--check` runs the gate and writes
  nothing — the memo's case, a spec set re-validated on a PRD already past
  `analyzing`. `refine` reads the `## Split` table off stdin, writes each
  child through `transitions.from_template` with `origin`, `from`, `repo`,
  `workflow` and `priority` inherited and `needs:` as given, appends the
  rows under the parent's `## Children` (header once), sets the parent
  `open`, refuses an existing child by name after landing the new rows.
  `--as <id>` or `PEARDE_AS` is required, as every transition takes it.
- `probe/verify.sh` — 90/90 on a copy of `resources/board/example/prds`.
  `SPECS_PY=<path>` overrides the module under test.

**What is left:**

- Move `probe/specs.py` to `resources/board/specs.py`. Drop the `_board_dir()`
  walk-up shim: at its home the module sits beside `plan.py`, `edit.py` and
  `transitions.py`, so `HERE` and `ROOT` resolve the way `transitions.py`
  resolves them.
- `probe/verify.sh`: the default becomes
  `SPECS="${SPECS_PY:-$ROOT/resources/board/specs.py}"`. The harness stays
  where it is — the tree keeps each PRD's harness under its own `probe/`.
- The manifest row for `resources/board/specs.py` in `references/files.md`
  is the orchestrator's edit (named in the analyst's report), not this
  unit's; the last box below reads its effect.

## Acceptance

- [x] `python3 resources/board/specs.py` with no command prints the usage and exits 2; `python3 -c "import sys; sys.path.insert(0,'resources/board'); import specs; print(sorted(specs.COMMANDS))"` prints `['refine', 'specced']`
- [x] `bash prds/the-board-runs-itself/specced-is-a-command/probe/verify.sh` prints `verify: 90/90 checks pass` against `resources/board/specs.py` — its default once moved — and leaves `git status --porcelain resources/board/example` empty
- [x] `grep -c '_board_dir' resources/board/specs.py` prints `0`, and `grep -c '^import\|^from' resources/board/specs.py` shows only `os`, `re`, `sys`, `edit`, `plan`, `transitions`, `workflows`
- [x] on a copy of the example board with `PEARDE_AS=engineer`: `set big/second analyzing --force`, two specs of 8 and 12 → `python3 resources/board/specs.py specced big/second --blast low` prints exactly one `▸ big/second: analyzing → specced …` line and `prd.md` reads `complexity: 20`, `blast-radius: low`, `state: specced`, no `claim:`
- [x] `python3 resources/index.py check` prints no line naming `resources/board/specs.py` (the orchestrator's manifest row is in place) and no line naming `probe/`

## Verify and Proof

```sh
python3 resources/board/specs.py; echo "exit $?"
python3 -c "import sys; sys.path.insert(0,'resources/board'); import specs; print(sorted(specs.COMMANDS))"
grep -c '_board_dir' resources/board/specs.py
bash prds/the-board-runs-itself/specced-is-a-command/probe/verify.sh | tail -1
git status --porcelain resources/board/example
python3 resources/index.py check | grep -c 'resources/board/specs.py\|specced-is-a-command/probe' 
```
