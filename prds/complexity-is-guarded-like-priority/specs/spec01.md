---
complexity: 26
footprint:
  - resources/board/plan.py
  - prds/complexity-is-guarded-like-priority/probe/verify.sh
---

# spec01 — no number in plan.py is read off a file a person typed without a guard, and a bad one is said out loud

`resources/board/plan.py` read hand-written numbers with a bare `float()` in
seven places. One of them, `spec_data:244`, is reached by `cmd_scan` — step 1
of every round — so `complexity: x` on any spec file on the board took down the
scan, the plan, the progress line and the view for every session, with a
traceback that named no PRD.

This unit routes every such read through three functions — `bad_value`, `num`,
`dur` — and makes the fallback the one the callers already agree on. A bad
value reads as **0.0, exactly what an unscored value reads as**, because
`compute_plan` and `weight_of` already weigh an unscored PRD at the board
average and `progress_terms` already leaves it out of the average it computes.
So the plan degrades to "we do not know this one's size", never to "this one is
free". What is not allowed to be silent is the typo: every bad value is
reported on stderr, naming the file, the key and the value, **once per (file,
key, value)** rather than once per read — `complexity` is read by five
functions in a round and one typo is one problem.

`priority` is now read by the same function as `complexity`. The asymmetry the
PRD names is gone in both directions: `priority` had two guards catching
`(TypeError, ValueError)` and two catching only `ValueError`, so a
`priority:` written as a list crashed `compute_plan` and `vision_json`.

**All of it already stands in the tree** — the probe built it in the footprint
file itself, because a guard has no meaning outside the function it guards.
The only file the probe added is
`prds/complexity-is-guarded-like-priority/probe/verify.sh`. What is left for an
implementer is to run the boxes below and restore any that has moved.

## What the build changed, by site

| site | was | now |
|------|-----|-----|
| `hours()` | `float(m.group(1))` — `..` and `1.2.3` match the shape and raise | `try/except ValueError` → `0.0`. This refutes the PRD's "`hours()` already tolerates a bad string" |
| `strip_comment()` | `\s+#.*$` — a value that is ONLY a comment kept the comment TEXT, because `KEY_RE` had already eaten the leading spaces | `(^\|\s+)#.*$`. The PRD template's own `est:   # the weight…` line parsed to that sentence; `hours()` swallowed it, `dur()` reported it, which is how it was found |
| `spec_data` | unguarded `complexity`, `est` | `num` / `dur`, labelled `<rel>/specs/<file>` |
| `claim_ttl` | `hours(v)` could raise | reports and falls back to 30 minutes |
| `gantt_payload` | unguarded `complexity` ×2, `est` ×3, `actual`; guarded `priority` ×2 | `num` / `dur`, labelled by `rel` |
| `write_history` | unguarded `complexity`, `est` | `num` / `dur`; the loop now carries `rel` so the report can name the PRD |
| `calib_rows` | guarded `complexity`, unguarded `est`/`actual` | `num` / `dur` |
| `compute_plan` | unguarded `complexity`, `est`, `weight-default`; `prio` caught `ValueError` only | `num` / `dur` |
| `weight_of` | unguarded `complexity`, `est` | `num` / `dur` |
| `progress_terms` | unguarded `complexity`, `weight-default` | `num`, labelled by `rel` |
| `vision_json` | `prio` caught `ValueError` only; unguarded `est` | `num` / `dur` |

`plan_workers`'s `int(board_settings(...))` was already inside a `try` and is
left alone.

## Acceptance

Every box below is asserted by
`prds/complexity-is-guarded-like-priority/probe/verify.sh`, which builds each
fixture board in a fresh `mktemp -d` removed at exit.

- [x] `bash prds/complexity-is-guarded-like-priority/probe/verify.sh` ends in `0 fail`.
- [x] The PRD's own fixture — one `specced` PRD whose `specs/spec01.md` carries `complexity: x`, beside one PRD at `complexity: 30` — leaves `scan` at exit 0 with a `counts:` line, no `Traceback` on stderr.
- [x] That fixture's stderr names the spec file (`typo/specs/spec01.md`), the key, the value `'x'` and the words `weighed as unscored`, and does so **exactly once** across the whole `scan`.
- [x] In that fixture the bad PRD is weighed at the board average — `scan` prints `typo · p50 · w30`, not `w0`.
- [x] `plan`, `status`, `gantt` and `calibrate` all exit 0 on that same board.
- [x] `complexity: high` on a `prd.md` (not a spec) is reported naming the PRD, and that PRD is weighed at the board average.
- [x] `est: ..`, `est: 1.2.3` and `est: ..h` each leave `scan` at exit 0 and are each reported; `est: 0h` — an honest zero — is not reported.
- [x] A `priority:` written as a YAML list leaves `scan` and `gantt` at exit 0 and is reported.
- [x] `weight-default: many`, `gantt-day: ..` and `claim-ttl: ..` in `prds/settings.md` each leave the command that reads them at exit 0 and are each reported naming `settings.md`.
- [x] `write_history` on a board holding `complexity: nope` completes and reports it; `calibrate` on that board exits 0.
- [x] A board with no bad value writes **nothing** to stderr — `wc -c` of stderr is 0 — and a number written as a quoted string (`complexity: "30"`) is still read as 30.
- [x] `est:   # the weight, only when complexity is absent. Not a duration` reads as empty: exit 0, stderr empty. `est: 4h  # trailing note` still reads as 4. `repo: a#b` keeps its `#`.
- [x] The census holds over the file: `resources/board/plan.py` makes exactly 3 `float()` calls — inside `hours()`'s `try`, inside `claim_ttl()`'s `isdigit` branch, inside `num()`'s `try` — none of them reading `["fm"].get` or `settings.get`, and the file parses.
- [x] `python3 resources/board/plan.py scan prds` on this repo's own board exits 0 and reports no bad value.

## Verify and Proof

```sh
# the whole contract, over fixtures built in a temp dir at run time
bash prds/complexity-is-guarded-like-priority/probe/verify.sh

# the census, read straight off the file — every remaining float() is guarded
grep -n 'float(' resources/board/plan.py
grep -c 'float(.*\["fm"\]\.get\|float(fm\.get\|float(settings\.get' resources/board/plan.py   # 0

# the three functions every hand-written number now goes through
grep -n 'def bad_value\|def num(\|def dur(' resources/board/plan.py

# the file still parses, and the repo's own board still scans in silence
python3 -c 'import ast,io; ast.parse(io.open("resources/board/plan.py").read())'
python3 resources/board/plan.py scan prds
```
