---
complexity: 2
footprint:
  - prds/the-board-runs-itself/one-command/probe/verify.sh
---

# spec03 — one-command's `--help` check counts modes instead of pinning 2

`one-command`'s harness asserts `pearde doctor --help` prints exactly `2`
lines. The rule it is defending is that `--help` prints the mode lines and
never runs the command; the `2` is a second copy of how many modes
`doctor.sh` has, and spec01 added a third. The harness is red on the literal,
not on the rule.

The repair is the same move this whole PRD is: derive the number from the
thing it counts. `pearde.py`'s `usage_lines` builds one help line per usage
row in the script's header comment, so the header is the denominator.

Nothing of this stands — the file belongs to a landed PRD and this run left
it untouched, red, at `53 passed, 1 failed` against a `54 passed, 0 failed`
baseline.

## Acceptance

- [~] the check reads its expected line count from
      `grep -cE '^#   doctor\.sh ' "$R/resources/doctor.sh"`, not from a
      literal
- [~] `bash prds/the-board-runs-itself/one-command/probe/verify.sh` prints
      `54 passed, 0 failed` and exits 0
- [~] adding or removing a usage row in the doctor header does not redden it
- [~] no other check in that harness changed — the rule the check asserts is
      unchanged and its name still says `--help never runs the command`

## Verify and Proof

```sh
bash prds/the-board-runs-itself/one-command/probe/verify.sh
git diff --numstat prds/the-board-runs-itself/one-command/probe/verify.sh
```

## Struck 2026-08-29

All four boxes struck, none ticked. This spec asked to repair
`prds/the-board-runs-itself/one-command/probe/verify.sh`, whose `--help` check
pinned the literal `2` and went red when this PRD added `doctor`'s third usage
row. The session owning that file applied the derived-count fix and committed
it as `98e57af` while this PRD was in flight; the harness reads
`54 passed, 0 failed` with our `doctor.sh` change in place.

Struck rather than ticked because no worker of ours ran these checks, and
struck rather than deleted because the spec is the record of why that file
moved. The repair itself is the one this board has now made four times:
`= "$(grep -cE "^#   doctor\.sh " "$R/resources/doctor.sh")"` in place of
`= 2`, deriving the count from the thing it counts.
