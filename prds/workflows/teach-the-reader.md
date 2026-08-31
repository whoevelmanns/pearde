---
atomic: teach-the-reader
subject: make one reader parse the key and one check fail on a bad value
date: 2026-08-28
runs: 0
---

# teach-the-reader — the row turned into behaviour

## Do

1. Find the one script under `resources/` that already owns this format. A
   format has one reader; a second parser is two that drift.
2. Parse the key there, and apply the default the contract row states.
3. Add the failing case to that script's check: the value that is not allowed,
   named in the message, with the file and the key in it.
4. Build a fixture in a directory made at run time — `D=$(mktemp -d)` — write
   a file carrying a bad value, run the check against it, and confirm it exits
   non-zero and names the key. Never leave a fixture inside `prds/`.
5. Add or extend the row in `resources/doctor.sh` so the check has a place a
   person reads it.

## Done when

- The temp fixture with a bad value makes the check exit non-zero, and the
  message names the key and the file.
- The same check is silent on the real tree.
- `bash resources/doctor.sh` prints a row for it, and the fixture directory is
  gone.

## Fails when

| seen | means | do |
|------|-------|----|
