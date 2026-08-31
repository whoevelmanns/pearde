---
atomic: attempt-the-build
subject: build the contract until it works or hits something undefined
date: 2026-08-28
updated: 2026-08-29
runs: 24
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
- `git status --short` shows no `?? prds/<slug>/` you did not make — a hand-walked sweep over the board is refused by the guard in a wired repo, and the untracked list answers the same question.
- `git status --short` shows the probe under the PRD folder and nothing at the
  repo root.

## Fails when

| seen | means | do |
|------|-------|----|
| a fixture board built under `mktemp -d` shows up in `serve.py status` after the run, on a path that no longer exists | the probe ran a command whose repair registers whatever board it is handed — `doctor --fix` is one — and the live daemon's registry outlives the temp dir | never run a `--fix`-shaped command against a fixture while a real service is up; point it at a dead port (`PEARDE_PORT=1`) so the repair cannot connect, and check `serve.py status` at the end. `serve.py forget <name>` removes one already landed |
| the probe passes standalone and fails only when the runner that is its own subject runs it | the probe is itself an instance of the population it measures, and inherits the environment that runner sets — a guard variable, a cwd, a port — so it measures the guard instead of the behaviour | clear it explicitly for every fixture invocation (`env -u <VAR>`), keep one assertion that sets it deliberately, and run the harness both ways before quoting a count |
| every fixture lands on one board, and assertions pass or fail in the wrong sections | the fixture-maker is called as `B=$(mktemp_helper)`, and command substitution runs it in a **subshell** — a counter or path it keeps never reaches the caller, so every call returns the same board | make each fixture with its own `mktemp -d` inside the helper and echo that; never keep state in a helper you call through `$(…)` |
| a patch's anchor text no longer matches a file you read in step 1 | another session moved the file since | re-read it, merge into its current shape, keep your hunk disjoint from theirs, and name the collision in the report |
| the fixture's own git repo shows `?? err` or another scratch file after a refusal | the harness wrote its scratch inside the fixture, so "the diff is empty" cannot pass | keep scratch in a second `mktemp -d` outside the fixture repo |
| `verify.sh` prints a heading and hangs | a line in the harness reads stdin — a bare `cat` or `read` with no file | run it with `</dev/null`, then fix the line |
| a rule reading mtimes fires on a fresh copy of the example | `plan.py example` copies stat too, so the copy carries the example's own timestamps | `find <copy> -type f -exec touch {} +` before the byte-identity check; set them back only in the fixture that tests age |
| a page driver reads a Lit element right after `pearde.apply` and sees the old render | Lit renders on a microtask | `await el.updateComplete` before reading the DOM; and run any `pearde.replace` test last, since it removes the page's own element |
| `touch: out of range or illegal time specification` on **darwin** | `touch -d '<n> minutes ago'` is GNU coreutils; darwin's `touch` takes `-t <YYYYMMDDhhmm.SS>` and `date -v` for arithmetic — a GNU box never sees this row | portable on both: `python3 -c 'import os,time,sys; t=time.time()-120; os.utime(sys.argv[1],(t,t))' <file>`; darwin-only: `touch -t "$(date -v-2M +%Y%m%d%H%M.%S)" <file>` |
| a fixture meant to hold a foreign hunk and a kept one shows a single hunk, and the file goes whole | the two edits touch adjacent lines, and `-U0` merges adjacent changes into one hunk whose body is in neither baseline | leave one untouched line between the foreign edit and the kept one; the merge itself is a finding for the PRD that classifies hunks |
| `?? prds/<slug>/` appears mid-run and its `prd.md` is the untouched template | a harness in another PRD's probe calls a transition with no `--board` from a cwd inside the repo, and your edit turned its refusal into a write on the real board | before the first edit, grep every harness for the command with no `--board`; run those from a cwd with no `prds/` above; remove the untracked template PRD, name the row it left in `.transitions.jsonl`, and hand the harness's owner the `--board` line |
| a `sed -n 's/^\(a\|b\)$/\1/p'` extractor captures nothing, or captures `0`, on **darwin** | BSD sed has no `\|` alternation in a basic regex; GNU sed does | `grep -E '^(a|b)'` then `sed 's/^  //'` — portable on both |
| a fixture board made by `cp -R resources/board/example <d>/prds` shows `prds/prds`, and doctor resolves to a board one level too deep | `example` is a repo root, not a board — it holds `prds/` and a README | copy `resources/board/example/prds` to `<d>/prds`; doctor from `<d>` hides the nesting, a command run from inside the board does not |
| an assertion on a path printed by a Python command fails on **darwin** with `/private/var/…` against `/var/…` | `os.getcwd()` returns the real path; `mktemp -d` and bash's `$PWD` keep the symlink | compare against `$(cd "$D" && pwd -P)` — portable on both |
| `ModuleNotFoundError: No module named 'memos'` from a copied `collect.py` or `plan.py` | the board scripts import from `resources/` beside `board/`, and the copy took `resources/board/*.py` alone | copy `resources/*.py` into `<scratch>/resources/` and `resources/board/*.py` into `<scratch>/resources/board/` — the layout, not just the files |
| a `lacks` needle for a PRD name fails on a `scan` band that does not list it | another row's `after <name>` or `needs <name>` bit carries the name | match the row token `· <name> ·`, never the bare name |
| a `--dry` run refuses on a gate the real run passes | the dry branch re-ran a gate that reads the file the real run writes first — `answer`'s gate saw the question still open because the answer is never on disk in a dry run | compute the gate's input on the scan dict in memory (the answer appended to `prd["body"]`, the state moved on `prd["fm"]`) and print the line off that dict; never re-enter `transition()` for a dry run of a two-step write |
| every assertion in a harness passes, or every one fails, regardless of the command's output | the helper is `ok "<label>" "<expr>"` with the expr evaluated inside `ok`, so `$2`/`$3` in the expr name `ok`'s own arguments, not the caller's values | evaluate the test in the caller (`eq() { [ "$2" = "$3" ]; ok "$1" $? "…"; }`) and hand `ok` only a label and an exit code |
