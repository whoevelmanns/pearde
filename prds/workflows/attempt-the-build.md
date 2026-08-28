---
atomic: attempt-the-build
subject: build the contract until it works or hits something undefined
date: 2026-08-28
runs: 0
---

# attempt-the-build — the attempt is the analysis

## Do

1. Build the thing the contract asks for. Whatever the build passes through
   needs no question; whatever it hits is the finding.
2. Keep the code under `prds/<prd>/probe/` — never at the repo root, where it
   would redden the map check for every later PRD.
3. Build every fixture in a directory made at run time — `D=$(mktemp -d)`,
   removed at exit. A fixture `prd.md` left anywhere under `prds/` becomes a
   real PRD the scan picks up.
4. Write `prds/<prd>/probe/verify.sh` as you go: one line per assertion, a
   count at the end.
5. Stop at the first fork the build cannot pick and cannot build around, and
   record what the build was doing when it hit it. Which verdict that becomes
   is @references/parts/workers.md.

## Done when

- `bash prds/<prd>/probe/verify.sh` prints a count, and the count is quoted.
- `find prds -name prd.md` lists only real PRDs — no fixture among them.
- `git status --short` shows the probe under the PRD folder and nothing at the
  repo root.

## Fails when

| seen | means | do |
|------|-------|----|
