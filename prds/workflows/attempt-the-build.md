---
atomic: attempt-the-build
subject: build the contract until it works or hits something undefined
date: 2026-08-28
updated: 2026-08-28
runs: 13
---

# attempt-the-build — the attempt is the analysis

## Do

1. Build the thing the contract asks for. Whatever the build passes through
   needs no question; whatever it hits is the finding.
2. Keep NEW code under `prds/<prd>/probe/` — never at the repo root, where it
   would redden the map check for every later PRD — so a file the PRD's
   footprint places under `resources/` is built under `probe/` and moved by
   its spec. A change that is an **edit to an existing footprint file** cannot
   be staged this way: a guard, a rename or a branch has no meaning outside
   the function it lives in, so it is built in place, in the footprint file
   itself, and the spec records what already stands rather than what to move.
   Say which it was in the report.
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
| every fixture lands on one board, and assertions pass or fail in the wrong sections | the fixture-maker is called as `B=$(mktemp_helper)`, and command substitution runs it in a **subshell** — a counter or path it keeps never reaches the caller, so every call returns the same board | make each fixture with its own `mktemp -d` inside the helper and echo that; never keep state in a helper you call through `$(…)` |
| a patch's anchor text no longer matches a file you read in step 1 | another session moved the file since | re-read it, merge into its current shape, keep your hunk disjoint from theirs, and name the collision in the report |
| the fixture's own git repo shows `?? err` or another scratch file after a refusal | the harness wrote its scratch inside the fixture, so "the diff is empty" cannot pass | keep scratch in a second `mktemp -d` outside the fixture repo |
| `verify.sh` prints a heading and hangs | a line in the harness reads stdin — a bare `cat` or `read` with no file | run it with `</dev/null`, then fix the line |
| a rule reading mtimes fires on a fresh copy of the example | `plan.py example` copies stat too, so the copy carries the example's own timestamps | `find <copy> -type f -exec touch {} +` before the byte-identity check; set them back only in the fixture that tests age |
| a page driver reads a Lit element right after `pearde.apply` and sees the old render | Lit renders on a microtask | `await el.updateComplete` before reading the DOM; and run any `pearde.replace` test last, since it removes the page's own element |
| `touch: out of range or illegal time specification` on **darwin** | `touch -d '<n> minutes ago'` is GNU coreutils; darwin's `touch` takes `-t <YYYYMMDDhhmm.SS>` and `date -v` for arithmetic — a GNU box never sees this row | portable on both: `python3 -c 'import os,time,sys; t=time.time()-120; os.utime(sys.argv[1],(t,t))' <file>`; darwin-only: `touch -t "$(date -v-2M +%Y%m%d%H%M.%S)" <file>` |
| a fixture meant to hold a foreign hunk and a kept one shows a single hunk, and the file goes whole | the two edits touch adjacent lines, and `-U0` merges adjacent changes into one hunk whose body is in neither baseline | leave one untouched line between the foreign edit and the kept one; the merge itself is a finding for the PRD that classifies hunks |
