---
memo: two-holes-the-flag-probe-found
kind: note
status: decided
subject: collect defaults the persona silently where every transition refuses, and `set --force` leaves a stale `claim:`
date: 2026-08-29
prds:
  - an-unknown-flag-refuses
  - the-tool-keeps-its-word/collect-keeps-its-word
---

# two-holes-the-flag-probe-found — small, real, and not in the PRD that found them

## Decision

Open. Two defects the `an-unknown-flag-refuses` analyst measured on a copy
of the example board while probing every writing verb, outside its contract:

1. `collect` with neither `--as` nor `PEARDE_AS` writes `· as engineer` —
   silently. Every transition refuses that case (`the-next-line-runs` allows
   it for `add` alone, and says `(default)` on the line). `collect` is the
   one verb that commits, and its line is the record.
2. `set <prd> <state> --force` moves the state and leaves `claim:` in place
   (`analyzing → open` forced, `claim: w1` kept); `brief` then reports the
   PRD `held`. `--force` skips the gate; it should still clear what the
   target state cannot carry.

## Why

Both are one clause each in `transitions.py`/`collect.py`, and both change
what ships — a line that lies about who acted, a PRD that reads as held after
the user un-held it. Filed as a note rather than a PRD because the derived
count is at two live against four requested and the user has asked for the
plan's PRDs, not for every hole a probe turns up; whoever next opens either
file takes both.

## Alternatives considered

**Fold into `an-unknown-flag-refuses`.** Its contract is flags; these are not.
A PRD that grows a second job at spec time is the shape `too-big` refuses.

**A PRD each.** Two one-clause PRDs cost four dispatches for two lines.

## Consequences

- Until fixed, run `collect` with `--as` or `PEARDE_AS` set, and after any
  `set --force` check `claim:` by hand.
