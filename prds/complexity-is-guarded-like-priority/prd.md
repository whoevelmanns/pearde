---
state: done
origin: derived
actual: 0.9h
commit: c150ed5
from: workflows-on-the-board/workflow-seed
priority: 70
complexity: 26
blast-radius: high
repo: pearde
footprint:
  - resources/board/plan.py
  - prds/complexity-is-guarded-like-priority/probe
---

# complexity-is-guarded-like-priority — one typo must not take the board down

When this is done, a spec carrying `complexity: high` costs the board a
reported problem, not a stack trace, and `scan` still answers.

The decision to fix this now rather than park it is the user's, taken
2026-08-28 against the alternative of finishing the deliverable first. The
measurement and the roads not taken are in
`prds/memos/one-typo-crashes-every-round.md`; this PRD builds it.

## The consequence, named

`resources/board/plan.py:244`, inside `spec_data`:

```python
est += float(fm.get("complexity", 0) or 0) or hours(fm.get("est", ""))
```

`spec_data` is called for every live PRD by `compute_plan`, which is called by
`cmd_scan` — step 1 of every round. One spec file anywhere on the board with a
non-numeric `complexity` takes down the scan, the plan, the progress line and
the view, for **every session working that board**, and the traceback names no
PRD.

**Reproduced**, fixture: a scratch board outside the repo with one `specced`
PRD whose `specs/spec01.md` carries `complexity: x`.

```
File ".../resources/board/plan.py", line 244, in spec_data
    est += float(fm.get("complexity", 0) or 0) or hours(fm.get("est", ""))
ValueError: could not convert string to float: 'x'
```

`complexity` is written by hand by an analyst on every spec — it is one of the
two keys @references/parts/contract.md requires — so the population of writers
is every worker the board has ever dispatched and the failure mode is a typo.

The file already knows the answer. At `:823`, three lines from the same read:

```python
    pr = float(p["fm"].get("priority", 0))
except (TypeError, ValueError):
    pr = 0.0
```

Two weights, read the same way, one guarded. That is not a considered
asymmetry.

## The decision this PRD has to make

`priority` chooses `0.0` silently. **A weight must not.** A `complexity` that
silently becomes `0` makes a PRD weightless, which moves it in the plan and in
the progress percentage — a wrong number that looks like a real one. The
contract here is: a bad value is reported and the PRD falls back to the board
average the way an unscored PRD already does, so the plan degrades to "we do
not know this one's size" rather than to "this one is free".

## Files

| file                       | change                                                                                                   |
|----------------------------|--------------------------------------------------------------------------------------------------------------|
| `resources/board/plan.py`  | every read of a frontmatter number is guarded, found by **census over the file** rather than by memory — `spec_data`, `weight_of`, `progress_terms`, `gantt_payload` and `write_history` all read `complexity`, and `hours()` already tolerates a bad string. A bad value falls back to the unscored path and is reported once per PRD, not per read |

## Rules

- **Report, do not swallow.** A guarded read that says nothing turns a typo
  into a silently wrong plan, which is worse than the crash it replaced.
- **The census is the work.** Fixing `:244` alone leaves the next reader of
  the same key to crash instead. Enumerate every `float(` over frontmatter in
  the file and say which are guarded, before changing any.

## Verify

- The fixture above: `scan` completes, names the PRD and the bad value, and
  the PRD is weighed at the board average.
- A census in the report: every `float(` over frontmatter in `plan.py`, each
  marked guarded or not, before and after.
- `bash prds/workflows-on-the-board/workflow-seed/probe/verify.sh` and the
  three sibling harnesses hold at their committed totals.
