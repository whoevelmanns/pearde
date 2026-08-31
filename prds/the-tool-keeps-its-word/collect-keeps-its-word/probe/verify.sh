#!/usr/bin/env bash
# collect-keeps-its-word — the probe's harness.
#
# Every fixture is a copy of `resources/board/example` under its own
# `git init` in a temp dir; scratch lives in a second temp dir. Each of the
# three failures is reproduced first on the code as it stood at e8b262d
# (`git show` into scratch — the tree is never checked out), then measured
# on the tree's `resources/board/collect.py`. Rule 3 stands on
# `dispatchable()` in plan.py — `one-predicate-for-dispatchable`'s — and
# reads it from the tree, so this harness is red until that PRD's hunk is
# in the tree. One line per assertion, a count at the end.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
COLLECT="$ROOT/resources/board/collect.py"
EXAMPLE="$ROOT/resources/board/example"
PINNED=e8b262d                # the last commit before this probe's edits
PASS=0; FAIL=0
export PEARDE_PORT=1          # nothing listens there — the daemon is "down"
export GIT_AUTHOR_NAME=probe GIT_AUTHOR_EMAIL=probe@x \
       GIT_COMMITTER_NAME=probe GIT_COMMITTER_EMAIL=probe@x

ok()   { PASS=$((PASS+1)); echo "  ok   $1"; }
bad()  { FAIL=$((FAIL+1)); echo "  FAIL $1"; [ -n "${2:-}" ] && echo "       got:  $2"; [ -n "${3:-}" ] && echo "       want: $3"; }
eq()   { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1" "$2" "$3"; fi; }
has()  { if printf '%s' "$2" | grep -qF -- "$3"; then ok "$1"; else bad "$1" "$2" "contains: $3"; fi; }
lacks(){ if printf '%s' "$2" | grep -qF -- "$3"; then bad "$1" "$2" "without: $3"; else ok "$1"; fi; }

TOP="$(mktemp -d)"; W="$(mktemp -d)"
trap 'rm -rf "$TOP" "$W"' EXIT

# ── the two collects: the pinned one, and the tree's ─────────────────────────
# the scripts import from `resources/` beside `board/`, so the copy keeps
# that layout
OLD="$W/old/resources"; mkdir -p "$OLD/board"
for f in $(git -C "$ROOT" ls-tree -r --name-only "$PINNED" resources/ | grep '^resources/\(board/\)\?[^/]*\.py$'); do
  git -C "$ROOT" show "$PINNED:$f" > "$OLD/${f#resources/}"
done

run_old()     { ( cd "$D" && python3 "$OLD/board/collect.py" --board "$D/prds" "$@" ) 2>&1; }
run()         { ( cd "$D" && PEARDE_AS=engineer python3 "$COLLECT" --board "$D/prds" "$@" ) 2>&1; }
scan_collect(){ ( cd "$D" && python3 "$ROOT/resources/board/plan.py" scan "$D/prds" 2>/dev/null | sed -n '/^collect/,/^$/p' ); }
snap()        { run --snapshot "${1:-finished}" > /dev/null; }
ncommits()    { ( cd "$D" && git rev-list --count HEAD ); }
subject()     { ( cd "$D" && git log -1 --format=%s "${1:-HEAD}" ); }
paths()       { ( cd "$D" && git show --name-only --format= "${1:-HEAD}" | sort | tr '\n' ' ' ); }
fm()          { grep -m1 "^$2:" "$D/prds/$1/prd.md" | sed "s/^$2: *//"; }
at()          { ( cd "$D" && git show "$1:$2" ); }
short()       { ( cd "$D" && git rev-parse --short "$1" ); }
setline()     { python3 -c 'import sys; p,n,t=sys.argv[1],int(sys.argv[2]),sys.argv[3]; L=open(p).read().splitlines(True); L[n-1]=t+"\n"; open(p,"w").write("".join(L))' "$@"; }
insafter()    { python3 -c 'import sys; p,n,t=sys.argv[1],int(sys.argv[2]),sys.argv[3]; L=open(p).read().splitlines(True); L[n:n]=[t+"\n"]; open(p,"w").write("".join(L))' "$@"; }

# ── the fixture: the example board, its own repo ─────────────────────────────
fixture() {
  D="$TOP/$1"; mkdir -p "$D"; cp -R "$EXAMPLE/." "$D/"
  python3 - "$D/prds/finished/specs/spec01.md" <<'EOF'
import re, sys; p = sys.argv[1]; t = open(p).read()
open(p, "w").write(re.sub(r"```sh\n.*?```", "```sh\ntrue\n```", t, flags=re.S))
EOF
  find "$D" -type f -exec touch {} +
  ( cd "$D" && git init -q -b main && git add -A && git commit -q -m fixture )
}
# rule 1's shape: HEAD's record says `analyzing` with three open boxes; the
# claim wrote `claimed` and the analyst a paragraph before the snapshot
record_fixture() {
  fixture "$1"
  cat > "$D/prds/finished/prd.md" <<'EOF'
---
state: analyzing
origin: requested
priority: 55
complexity: 10
blast-radius: low
footprint:
  - src/util.py
---

# finished — every box closed, a worker still holding it

## Acceptance

- [ ] the helper is written
- [ ] a test covers it
- [ ] the test suite passes
EOF
  ( cd "$D" && git add -A && git commit -q -m "analyzing" )
  setline "$D/prds/finished/prd.md" 2 "state: claimed"
  insafter "$D/prds/finished/prd.md" 2 "claim: impl-1 2026-08-28 12:00"
  printf '\nThe analyst wrote this paragraph before the claim.\n' >> "$D/prds/finished/prd.md"
  snap
  sed -i '' 's/^- \[ \] /- [x] /' "$D/prds/finished/prd.md"
  mkdir -p "$D/src"; echo 'def helper(): return 1' > "$D/src/util.py"
}

# ── A. the record lands whole ────────────────────────────────────────────────
echo "A. reproduced at $PINNED: the record staged by hunk"
record_fixture a1
OUT="$(run_old finished)"; RC=$?
eq  "A1 the old collect exits 0" "$RC" "0"
has "A1 ...and says by hunk on the board's own record" "$OUT" "by hunk prds/finished/prd.md"
eq  "A1 HEAD's record says analyzing" "$(at HEAD prds/finished/prd.md | grep -m1 '^state:')" "state: analyzing"
eq  "A1 ...with the three ticks under it" "$(at HEAD prds/finished/prd.md | grep -c '^- \[x\]')" "3"
eq  "A1 the tree says done" "$(fm finished state)" "done"
has "A1 ...and the folder is dirty after its own collect" "$( cd "$D" && git status --porcelain -- prds/finished )" "M prds/finished/prd.md"

echo "A. the record lands whole, commit: in a second commit"
record_fixture a2
N0="$(ncommits)"
OUT="$(run finished)"; RC=$?
eq  "A2 exit 0" "$RC" "0"
eq  "A2 two commits on top" "$(ncommits)" "$((N0 + 2))"
eq  "A2 HEAD is the record commit" "$(subject)" "finished — record"
eq  "A2 ...carrying only prd.md" "$(paths)" "prds/finished/prd.md "
eq  "A2 HEAD~1 carries the code and the record" "$(paths HEAD~1)" "prds/finished/prd.md src/util.py "
eq  "A2 HEAD~1's record says done" "$(at HEAD~1 prds/finished/prd.md | grep -m1 '^state:')" "state: done"
eq  "A2 ...with the three ticks" "$(at HEAD~1 prds/finished/prd.md | grep -c '^- \[x\]')" "3"
has "A2 ...and actual:" "$(at HEAD~1 prds/finished/prd.md)" "actual: "
lacks "A2 ...and no claim:" "$(at HEAD~1 prds/finished/prd.md)" "claim:"
has "A2 ...and the analyst's paragraph, the baseline hunk, whole" "$(at HEAD~1 prds/finished/prd.md)" "The analyst wrote this paragraph"
lacks "A2 HEAD~1 does not carry commit:" "$(at HEAD~1 prds/finished/prd.md)" "commit:"
eq  "A2 HEAD's commit: names HEAD~1" "$(at HEAD prds/finished/prd.md | grep -m1 '^commit:')" "commit: $(short HEAD~1)"
eq  "A2 the tree's commit: is the same" "$(fm finished commit)" "$(short HEAD~1)"
eq  "A2 the folder is clean" "$( cd "$D" && git status --porcelain -- prds/finished )" ""
lacks "A2 the line does not say by hunk on the record" "$OUT" "by hunk prds/finished"
has "A2 the line names the record commit" "$(printf '%s\n' "$OUT" | grep '^▸')" "record $(short HEAD)"
has "A2 the line names the code commit" "$(printf '%s\n' "$OUT" | grep '^▸')" "commit $(short HEAD~1)"
eq  "A2 nothing owed for the record" "$(grep -c 'prds/finished' "$D/prds/.claims/riders" 2>/dev/null || echo 0)" "0"
eq  "A2 one transition row" "$(grep -c '"to": "done"' "$D/prds/.transitions.jsonl")" "1"
# a clean tree: the worker committed everything — the record still lands
fixture a3
sed -i '' 's/^claim: .*/claim: impl-1 2026-08-28 12:00/' "$D/prds/finished/prd.md"
( cd "$D" && git add -A && git commit -q -m "the worker's commit" )
OUT="$(run finished)"; RC=$?
eq  "A3 clean tree: exit 0" "$RC" "0"
eq  "A3 HEAD~1 is the record, alone" "$(paths HEAD~1)" "prds/finished/prd.md "
eq  "A3 commit: names it — never none" "$(fm finished commit)" "$(short HEAD~1)"
eq  "A3 the folder is clean" "$( cd "$D" && git status --porcelain -- prds/finished )" ""
# --dry writes nothing and says where the record goes
record_fixture a4
OUT="$(run finished --dry)"; RC=$?
eq  "A4 --dry exit 0" "$RC" "0"
has "A4 --dry names the record and the second commit" "$OUT" "record:    prds/finished/prd.md"
eq  "A4 --dry leaves the state" "$(fm finished state)" "claimed"
eq  "A4 --dry commits nothing" "$(ncommits)" "2"

# ── B. a hunk with two authors ───────────────────────────────────────────────
lines_fixture() {
  fixture "$1"; mkdir -p "$D/src"
  printf 'line%d\n' 1 2 3 4 5 6 7 8 9 10 11 12 > "$D/src/util.py"
  ( cd "$D" && git add src/util.py && git commit -q -m lines )
}
echo "B. reproduced at $PINNED: the merged hunk goes as the worker's"
lines_fixture b1
setline "$D/src/util.py" 10 "line10-theirs"; snap; setline "$D/src/util.py" 11 "line11-ours"
eq  "B1 the diff is one merged hunk" "$( cd "$D" && git diff -U0 HEAD -- src/util.py | grep -c '^@@' )" "1"
OUT="$(run_old finished)"; RC=$?
eq  "B1 the old collect exits 0" "$RC" "0"
has "B1 ...and commits the foreign line as the worker's" "$(at HEAD src/util.py)" "line10-theirs"

echo "B. refused, named, nothing staged; --widen takes it; one line apart both land right"
lines_fixture b2
setline "$D/src/util.py" 10 "line10-theirs"; snap; setline "$D/src/util.py" 11 "line11-ours"
N0="$(ncommits)"
OUT="$(run finished)"; RC=$?
eq  "B2 exit 1" "$RC" "1"
has "B2 named: file and line" "$OUT" "two authors on one hunk: src/util.py:10"
has "B2 ...and the way out" "$OUT" "--widen src/util.py"
eq  "B2 nothing committed" "$(ncommits)" "$N0"
eq  "B2 the index is HEAD" "$( cd "$D" && git diff --cached --stat | wc -l | tr -d ' ' )" "0"
eq  "B2 the PRD is still claimed" "$(fm finished state)" "claimed"
eq  "B2 the record is untouched" "$( cd "$D" && git status --porcelain -- prds/finished )" ""
OUT="$(run finished --widen src/util.py)"; RC=$?
eq  "B2 --widen exits 0" "$RC" "0"
has "B2 --widen commits both lines" "$(at HEAD~1 src/util.py | grep -c 'theirs\|ours')" "2"
has "B2 --widen said on the line" "$(printf '%s\n' "$OUT" | grep '^▸')" "widened src/util.py"
lines_fixture b3
setline "$D/src/util.py" 10 "line10-theirs"; snap; setline "$D/src/util.py" 12 "line12-ours"
OUT="$(run finished)"; RC=$?
eq  "B3 one untouched line between: exit 0" "$RC" "0"
has "B3 the worker's line is in HEAD~1" "$(at HEAD~1 src/util.py)" "line12-ours"
lacks "B3 the foreign line is not" "$(at HEAD~1 src/util.py)" "line10-theirs"
has "B3 ...and stays in the tree" "$(cat "$D/src/util.py")" "line10-theirs"
has "B3 by hunk on the line" "$(printf '%s\n' "$OUT" | grep '^▸')" "by hunk src/util.py"
# a foreign insertion right above the worker's change merges too
lines_fixture b4
insafter "$D/src/util.py" 9 "line9-theirs-inserted"; snap; setline "$D/src/util.py" 11 "line10-ours"
OUT="$(run finished)"; RC=$?
eq  "B4 a merged insertion is refused" "$RC" "1"
has "B4 named at the working line" "$OUT" "two authors on one hunk: src/util.py:10"
# a baseline hunk that was undone is gone, not merged — no refusal
lines_fixture b5
setline "$D/src/util.py" 10 "line10-theirs"; snap; setline "$D/src/util.py" 10 "line10"; setline "$D/src/util.py" 11 "line11-ours"
OUT="$(run finished)"; RC=$?
eq  "B5 a baseline hunk undone before collect is not two authors" "$RC" "0"
has "B5 the worker's line landed" "$(at HEAD~1 src/util.py)" "line11-ours"
# the PRD's own folder is never a candidate: adjacent edits there go whole
record_fixture b6
insafter "$D/prds/finished/prd.md" 12 "- [x] a fourth box, the worker's, right under the analyst's lines"
OUT="$(run finished)"; RC=$?
eq  "B6 the record with adjacent hunks goes whole" "$RC" "0"
eq  "B6 ...four ticks in HEAD~1" "$(at HEAD~1 prds/finished/prd.md | grep -c '^- \[x\]')" "4"

# ── C. a container reaches done ──────────────────────────────────────────────
# `big` from the example, `second` set done; the children's `commit:` are real
# shas in this repo — `first`'s older, `second`'s newer.
container_fixture() {
  fixture "$1"
  S1="$(short HEAD)"
  echo "x" > "$D/touch.txt"; ( cd "$D" && git add touch.txt && git commit -q -m second-landed )
  S2="$(short HEAD)"
  sed -i '' "s/^commit: .*/commit: $S1/" "$D/prds/big/first/prd.md"
  sed -i '' "s/^state: open/state: done/" "$D/prds/big/second/prd.md"
  printf 'commit: %s\nactual: 2h\n' "$S2" > "$W/keys"
  python3 - "$D/prds/big/second/prd.md" "$W/keys" <<'EOF'
import sys; p = sys.argv[1]; t = open(p).read(); keys = open(sys.argv[2]).read()
open(p, "w").write(t.replace("---\n\n# second", keys + "---\n\n# second", 1))
EOF
  ( cd "$D" && git add -A && git commit -q -m "children done" )
}
echo "C. reproduced at $PINNED: a parent whose children are all done has no way to done"
container_fixture c1
OUT="$(run_old big)"; RC=$?
eq  "C1 the old collect refuses it" "$RC" "1"
has "C1 ...on its state" "$OUT" "state is \`open\`"
lacks "C1 the old scan does not list it under collect" "$( cd "$D" && python3 "$OLD/board/plan.py" scan "$D/prds" 2>/dev/null | sed -n '/^collect/,/^$/p' )" "· big ·"

echo "C. scan lists it, collect closes it in one commit"
SCAN="$(scan_collect)"
has "C2 scan lists big under collect — compute_plan's one list, the row without a why" "$SCAN" "· big · p62 · w14"
lacks "C2 ...and not big/first" "$SCAN" "big/first"
N0="$(ncommits)"
OUT="$(run big --dry)"; RC=$?
eq  "C2 --dry exit 0" "$RC" "0"
has "C2 --dry says the phrase" "$OUT" "container: every child done — pearde collect closes it"
has "C2 --dry names the sum and the sha" "$OUT" "actual: 3h · commit: $S2"
eq  "C2 --dry writes nothing" "$(fm big state)" "open"
OUT="$(run big)"; RC=$?
eq  "C2 exit 0" "$RC" "0"
eq  "C2 done" "$(fm big state)" "done"
eq  "C2 actual is the children's sum" "$(fm big actual)" "3h"
eq  "C2 commit: is the last child's" "$(fm big commit)" "$S2"
eq  "C2 one commit" "$(ncommits)" "$((N0 + 1))"
eq  "C2 its subject" "$(subject)" "big — done: every child landed"
eq  "C2 its paths: the parent's prd.md alone" "$(paths)" "prds/big/prd.md "
eq  "C2 clean under it" "$( cd "$D" && git status --porcelain -- prds/big )" ""
has "C2 the line" "$(printf '%s\n' "$OUT" | grep '^▸ big: open → done')" "container, 2 children"
eq  "C2 a transition row" "$(grep -c '"prd": "big"' "$D/prds/.transitions.jsonl")" "1"
OUT="$(run big)"; RC=$?
eq  "C2 collecting it again is refused" "$RC" "1"
# the trap: a parent with children AND work of its own is not a container
container_fixture c3
mkdir -p "$D/prds/big/specs"
cat > "$D/prds/big/specs/spec01.md" <<'EOF'
---
complexity: 3
footprint:
  - src
---

# spec01 — the parent's own unit

## Acceptance

- [ ] the parent's own box

## Verify and Proof

```sh
true
```
EOF
( cd "$D" && git add -A && git commit -q -m "own spec" )
lacks "C3 a parent with its own spec is not listed under collect" "$(scan_collect)" "· big ·"
OUT="$(run big)"; RC=$?
eq  "C3 ...and collect refuses it" "$RC" "1"
has "C3 ...on its state — ordinary held work, the specs decide" "$OUT" "state is \`open\`"
eq  "C3 nothing written" "$(fm big state)" "open"
container_fixture c4
printf '\n- [ ] the parent has a box of its own\n' >> "$D/prds/big/prd.md"
( cd "$D" && git add -A && git commit -q -m "own box" )
OUT="$(run big)"; RC=$?
eq  "C4 a parent with an open box of its own is refused" "$RC" "1"
eq  "C4 nothing written" "$(fm big state)" "open"
fixture c5    # as shipped: `second` still open
OUT="$(run big)"; RC=$?
eq  "C5 a child still open: refused" "$RC" "1"
lacks "C5 ...and not listed" "$(scan_collect)" "· big ·"
# a parent that holds work of its own and finished it: the ordinary path, two commits
container_fixture c6
mkdir -p "$D/prds/big/specs"
sed -e 's/- \[ \] the parent/- [x] the parent/' "$TOP/c3/prds/big/specs/spec01.md" > "$D/prds/big/specs/spec01.md"
sed -i '' 's/^state: open/state: claimed/' "$D/prds/big/prd.md"
insafter "$D/prds/big/prd.md" 2 "claim: impl-big 2026-08-28 12:00"
( cd "$D" && git add -A && git commit -q -m "own work, claimed" )
N0="$(ncommits)"
OUT="$(run big)"; RC=$?
eq  "C6 a parent that finished its own work goes the ordinary way" "$RC" "0"
eq  "C6 ...two commits" "$(ncommits)" "$((N0 + 2))"
eq  "C6 ...the record commit last" "$(subject)" "big — record"
lacks "C6 ...never as a container" "$OUT" "container"

# ── D. the daemon is up: ## Report is in the commit ──────────────────────────
echo "D. the posted report is in the commit"
record_fixture d1
SRV="$W/srv/resources"; mkdir -p "$SRV/board"
cp "$ROOT"/resources/*.py "$SRV/"
cp "$ROOT"/resources/board/*.py "$ROOT"/resources/board/*.css "$ROOT"/resources/board/*.js "$SRV/board/"
REG="$ROOT/resources/board/state/serve.json"
REG_BEFORE="$( [ -f "$REG" ] && cksum < "$REG" )"
SPARE="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')"
export PEARDE_PORT="$SPARE"
trap 'PEARDE_PORT="$SPARE" python3 "$SRV/board/serve.py" stop >/dev/null 2>&1; rm -rf "$TOP" "$W"' EXIT
ENS="$( cd "$D" && python3 "$SRV/board/serve.py" ensure "$D/prds" 2>&1 )"; RC=$?
eq  "D the daemon came up on a spare port" "$RC" "0"
OUT="$(run finished)"; RC=$?
eq  "D exit 0" "$RC" "0"
has "D report posted" "$(printf '%s\n' "$OUT" | grep '^▸')" "report posted"
has "D ## Report is in HEAD~1" "$(at HEAD~1 prds/finished/prd.md)" "## Report"
has "D ...holding the verify's exit" "$(at HEAD~1 prds/finished/prd.md | sed -n '/^## Report/,$p')" "spec01: exit 0"
eq  "D the folder is clean" "$( cd "$D" && git status --porcelain -- prds/finished )" ""
PEARDE_PORT="$SPARE" python3 "$SRV/board/serve.py" stop >/dev/null 2>&1
export PEARDE_PORT=1
eq  "D the real registry is untouched" "$( [ -f "$REG" ] && cksum < "$REG" )" "$REG_BEFORE"

# ── Z. hygiene ───────────────────────────────────────────────────────────────
echo "Z. hygiene"
eq  "Z no path under prds/.claims/ on any commit above" "$(for d in "$TOP"/*/; do [ -d "$d/.git" ] && ( cd "$d" && git log --name-only --format= ); done | grep -c 'prds/.claims/')" "0"
# the bare `collect` reads scan's band: the held-and-finished, and the container
container_fixture z1
OUT="$(run)"; RC=$?
eq  "Z the bare collect exits 0" "$RC" "0"
eq  "Z ...and closes finished" "$(fm finished state)" "done"
eq  "Z ...and big" "$(fm big state)" "done"
eq  "Z two lines" "$(printf '%s\n' "$OUT" | grep -c '^▸')" "2"

echo
echo "$((PASS+FAIL)) checks · $PASS pass · $FAIL fail"
[ "$FAIL" -eq 0 ]
