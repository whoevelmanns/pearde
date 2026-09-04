---
memo: windows-only-changes-stay-in-the-fork-never-a-pr-to-febreeze-upstream
kind: decision     # decision | note
status: decided    # open | decided | superseded
subject: windows-only changes stay in the fork, never a PR to febreeze upstream
date: 2026-09-01
# updated:         # only on a substantive revision; never for a path fix
# prds:            # board-relative PRD dirs this memo governs
#   - <prd-dir>
# supersedes:      # the slug this replaces
# superseded_by:   # the slug that replaced this
---
<!-- Unlike a prd.md, a memo's keys are a CLOSED set: an undeclared key is a
     typo and @resources/doctor.sh fails on it. @references/memo.md is the
     format. -->

# windows-only-changes-stay-in-the-fork-never-a-pr-to-febreeze-upstream — platform code stays where it can be tested

## Decision

Any change that exists only because this machine runs Windows — path
separators, PowerShell/Git-Bash quirks, CRLF handling, Windows-only tool
integrations — lands only in the `fork` remote
(`whoevelmanns/pearde`). It is never proposed as a pull request to `origin`
(`yesitsfebreeze/pearde`).

## Why

pearde is a general-purpose skill meant to work for whoever installs it, on
whatever OS they run. Upstream's baseline is not Windows-tested; a
Windows-only workaround would either not apply to other installs or would
need a runtime OS guard, adding complexity upstream has no way to verify
for a platform it doesn't run. The fork sync already showed the cost of
letting local changes drift from origin: today's sync attempt found
`origin/main` 41 commits ahead with conflicts against local changes here,
and had to be aborted rather than resolved automatically. Sending
Windows-only patches upstream as PRs would add review latency (a
maintainer who can't test on Windows deciding on Windows-only code) without
fixing that drift — it would just make it two-directional.

## Alternatives considered

**Upstream every fix, let febreeze decide what's Windows-specific** —
rejected: puts review burden on an upstream maintainer for platform code
they cannot verify locally, and blocks a fix landing here until that
review happens, when the fix is needed on this machine now.

**Gate Windows code behind a runtime OS check, submit it upstream anyway** —
rejected as the default: adds a conditional-complexity tax to every future
upstream sync, for a platform branch upstream never exercises. Worth doing
case-by-case if a specific fix turns out to matter beyond this machine, but
not as the default path.

## Consequences

- Windows-specific fixes accumulate only in `whoevelmanns/pearde` and never
  reach `yesitsfebreeze/pearde` via PR.
- A future `pearde fork sync` may keep hitting the same conflict class —
  that stays a per-sync manual resolution; this memo does not try to solve
  it.
- A Windows-only fix that turns out to matter beyond this machine (a real
  cross-platform bug the Windows path just happened to surface) needs a
  separate, deliberately-generalized PR — this default does not cover that
  case automatically.
