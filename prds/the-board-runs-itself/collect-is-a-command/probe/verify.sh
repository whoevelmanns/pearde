#!/usr/bin/env bash
# collect-is-a-command — the probe's harness.
#
# Builds a board under its own `git init` in a temp dir, with a tiny repo and
# a one-line verify script, and runs `resources/board/collect.py` against a
# fresh copy per scenario. Never the real board. One line per assertion, a
# count at the end.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
COLLECT="$ROOT/resources/board/collect.py"
PASS=0; FAIL=0
export PEARDE_PORT=1          # nothing listens there — the daemon is "down"
export GIT_AUTHOR_NAME=probe GIT_AUTHOR_EMAIL=probe@x \
       GIT_COMMITTER_NAME=probe GIT_COMMITTER_EMAIL=probe@x

ok()   { PASS=$((PASS+1)); echo "  ok   $1"; }
bad()  { FAIL=$((FAIL+1)); echo "  FAIL $1"; [ -n "${2:-}" ] && echo "       got:  $2"; [ -n "${3:-}" ] && echo "       want: $3"; }
eq()   { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1" "$2" "$3"; fi; }
has()  { if printf '%s' "$2" | grep -qF -- "$3"; then ok "$1"; else bad "$1" "$2" "contains: $3"; fi; }
lacks(){ if printf '%s' "$2" | grep -qF -- "$3"; then bad "$1" "$2" "without: $3"; else ok "$1"; fi; }

TOP="$(mktemp -d)"
trap 'rm -rf "$TOP"' EXIT

# ── the fixture ──────────────────────────────────────────────────────────────
# $D is a repo; $D/prds is the board. `finished` is claimed with its one spec
# box ticked after the initial commit (the worker's tick is dirty, in the
# union); `src/lib.txt` is the worker's code (untracked, in the union);
# `building` is claimed at 1/2; `landed` is done.
fixture() {
  D="$TOP/$1"; mkdir -p "$D"; ( cd "$D" && git init -q -b main )
  mkdir -p "$D/src" "$D/other" "$D/prds/finished/specs" "$D/prds/building/specs" "$D/prds/landed"
  echo 'grep -q hello src/lib.txt' > "$D/verify.sh"
  cat > "$D/prds/settings.md" <<EOF
---
name: fixture
language: English
workers: 1
pipeline: 1
${2:-}
---
EOF
  cat > "$D/prds/finished/prd.md" <<'EOF'
---
state: claimed
origin: requested
claim: impl-1 2026-08-28 10:00
priority: 50
complexity: 5
repo: fixture
workflow: implement-a-spec
footprint:
  - verify.sh
---

# finished — the lib says hello, and one call closes it

Body. No box here.
EOF
  cat > "$D/prds/finished/specs/spec01.md" <<'EOF'
---
complexity: 5
footprint:
  - src
---

# spec01 — the lib says hello

## Acceptance

- [ ] `src/lib.txt` holds `hello`

## Verify and Proof

```sh
bash verify.sh
```
EOF
  cat > "$D/prds/building/prd.md" <<'EOF'
---
state: claimed
origin: requested
claim: impl-2 2026-08-28 11:00
priority: 40
complexity: 5
footprint:
  - other
---

# building — half done
EOF
  cat > "$D/prds/building/specs/spec01.md" <<'EOF'
---
complexity: 5
footprint:
  - other
---

# spec01 — two boxes

## Acceptance

- [x] one
- [ ] two

## Verify and Proof

```sh
true
```
EOF
  cat > "$D/prds/landed/prd.md" <<'EOF'
---
state: done
origin: requested
priority: 30
complexity: 3
commit: 0000000
---

# landed — already done
EOF
  ( cd "$D" && git add -A && git commit -q -m "fixture" )
  [ "${NOWORK:-}" = 1 ] || work
}
# the worker's run: the code, and the box ticked
work() {
  echo hello > "$D/src/lib.txt"
  sed -i '' 's/- \[ \] `src/- [x] `src/' "$D/prds/finished/specs/spec01.md"
}
run() { ( cd "$D" && PEARDE_AS=engineer python3 "$COLLECT" --board "$D/prds" "$@" ) 2>&1; }
ncommits() { ( cd "$D" && git rev-list --count HEAD ); }
paths()    { ( cd "$D" && git show --name-only --format= "${1:-HEAD~1}" | sort | tr '\n' ' ' ); }   # HEAD~1: the code commit; HEAD is `<prd> — record`
fm()       { grep -m1 "^$2:" "$D/prds/$1/prd.md" | sed "s/^$2: *//"; }

# ── A. collect finished ───────────────────────────────────────────────────────
echo "A. collect finished"
fixture a
OUT="$(run finished)"; RC=$?
eq  "A exit 0" "$RC" "0"
eq  "A two commits on top of the fixture — the code, then the record" "$(ncommits)" "3"
eq  "A commit paths equal the footprint union plus the record" "$(paths)" "prds/finished/prd.md prds/finished/specs/spec01.md src/lib.txt "
SHA="$( cd "$D" && git rev-parse --short HEAD~1 )"
eq  "A prd.md carries commit: <sha>" "$(fm finished commit)" "$SHA"
has "A prd.md carries actual: <n>h" "$(fm finished actual)" "h"
eq  "A state done" "$(fm finished state)" "done"
eq  "A claim cleared" "$(fm finished claim)" ""
eq  "A the progress line printed once" "$(printf '%s\n' "$OUT" | grep -c '^▸ finished: claimed → done')" "1"
has "A the line carries the persona last" "$(printf '%s\n' "$OUT" | grep '^▸')" "· as engineer"
has "A the line says the round file is owed" "$OUT" "round file owed"
has "A the daemon being down is said, not fatal" "$OUT" "daemon down"
eq  "A transition row appended" "$(grep -c '"to": "done"' "$D/prds/.transitions.jsonl")" "1"
MSG="$( cd "$D" && git log -1 --format=%B HEAD~1 )"
WANT="$(printf 'finished — the lib says hello, and one call closes it\n\nspec01: the lib says hello\n\nprd: prds/finished\n')"
eq  "A git log -1 --format=%B matches commits.md line for line" "$MSG" "$WANT"
eq  "A building left alone" "$(fm building state)" "claimed"
# a second collect on the same PRD is refused — it is done
OUT="$(run finished)"; RC=$?
eq  "A collecting a done PRD exits 1" "$RC" "1"
has "A ...naming the state" "$OUT" "state is \`done\`"

# ── B. the verify made to exit 1 ─────────────────────────────────────────────
echo "B. red verify"
fixture b
echo 'echo boom; exit 1' > "$D/verify.sh"
OUT="$(run finished)"; RC=$?
eq  "B exit 1" "$RC" "1"
has "B the output printed" "$OUT" "boom"
has "B the exit named" "$OUT" "spec01: exit 1"
eq  "B git log unchanged" "$(ncommits)" "1"
eq  "B prd.md unchanged" "$( cd "$D" && git diff --stat -- prds/finished/prd.md )" ""
has "B nothing written, said" "$OUT" "nothing written"
OUT="$(run finished --fail)"; RC=$?
eq  "B --fail exits 1" "$RC" "1"
eq  "B --fail sets failed" "$(fm finished state)" "failed"
eq  "B --fail clears the claim" "$(fm finished claim)" ""
has "B --fail writes ## Failure" "$(cat "$D/prds/finished/prd.md")" "## Failure"
has "B ## Failure holds the output" "$(sed -n '/^## Failure/,$p' "$D/prds/finished/prd.md")" "boom"
eq  "B --fail commits nothing" "$(ncommits)" "1"
has "B --fail prints the line" "$OUT" "▸ finished: claimed → failed"

# ── C. a file dirtied outside the footprint ──────────────────────────────────
echo "C. inherited"
fixture c
echo stray > "$D/stray.txt"
OUT="$(run finished)"; RC=$?
eq  "C exit 0" "$RC" "0"
has "C listed as inherited" "$(printf '%s\n' "$OUT" | grep -A1 'inherited, not added')" "stray.txt"
eq  "C listed once" "$(printf '%s\n' "$OUT" | grep -c 'stray.txt')" "1"
lacks "C not added" "$(paths)" "stray.txt"
eq  "C still dirty after" "$( cd "$D" && git status --porcelain -- stray.txt )" "?? stray.txt"
eq  "C collected all the same" "$(fm finished state)" "done"
has "C the count on the line" "$(printf '%s\n' "$OUT" | grep '^▸')" "inherited 1"
fixture c2
echo stray > "$D/stray.txt"
OUT="$(run finished --widen stray.txt)"; RC=$?
eq  "C --widen <path> exits 0" "$RC" "0"
has "C --widen commits it" "$(paths)" "stray.txt"
has "C --widen names it in the message" "$( cd "$D" && git log -1 --format=%B HEAD~1 )" "widen: stray.txt"
has "C --widen names it on the line" "$(printf '%s\n' "$OUT" | grep '^▸')" "widened stray.txt"

# ── D. no argument ───────────────────────────────────────────────────────────
echo "D. no argument"
fixture d
OUT="$(run)"; RC=$?
eq  "D exit 0" "$RC" "0"
eq  "D finished collected" "$(fm finished state)" "done"
eq  "D building left alone" "$(fm building state)" "claimed"
eq  "D one line" "$(printf '%s\n' "$OUT" | grep -c '^▸')" "1"
OUT="$(run)"; RC=$?
eq  "D nothing left: exit 0" "$RC" "0"
has "D nothing left: said" "$OUT" "nothing finished"

# ── E. --dry ─────────────────────────────────────────────────────────────────
echo "E. --dry"
fixture e
OUT="$(run finished --dry)"; RC=$?
eq  "E exit 0" "$RC" "0"
eq  "E no commit" "$(ncommits)" "1"
eq  "E prd.md unchanged" "$(fm finished state)" "claimed"
has "E prints what 3 would add" "$OUT" "would add: prds/finished/specs/spec01.md, src/lib.txt"
has "E prints what 4 would say" "$OUT" "spec01: the lib says hello"
eq  "E .transitions.jsonl not written" "$(test -f "$D/prds/.transitions.jsonl" && echo yes || echo no)" "no"

# ── F. --trust ───────────────────────────────────────────────────────────────
echo "F. --trust"
fixture f
echo 'exit 1' > "$D/verify.sh"
OUT="$(run finished --trust)"; RC=$?
eq  "F exit 0 with a red verify" "$RC" "0"
has "F the line says trusted" "$(printf '%s\n' "$OUT" | grep '^▸')" "· trusted ·"
eq  "F done" "$(fm finished state)" "done"

# ── G. the gate ──────────────────────────────────────────────────────────────
echo "G. gate"
fixture g 'gate: echo gate-red; false'
OUT="$(run finished)"; RC=$?
eq  "G red gate exits 1" "$RC" "1"
has "G the gate's output printed" "$OUT" "gate-red"
eq  "G no commit" "$(ncommits)" "1"
fixture g2 'gate: true'
OUT="$(run finished)"; RC=$?
eq  "G green gate: exit 0" "$RC" "0"
has "G the gate ran and is in the report" "$OUT" "commit "

# ── H. clean tree ────────────────────────────────────────────────────────────
echo "H. clean tree"
fixture h
( cd "$D" && git add -A && git commit -q -m "the worker's commit" )
OUT="$(run finished)"; RC=$?
eq  "H exit 0" "$RC" "0"
eq  "H two commits — the record lands on a clean tree too" "$(ncommits)" "4"
eq  "H commit: names the record, never none" "$(fm finished commit)" "$( cd "$D" && git rev-parse --short HEAD~1 )"
eq  "H done" "$(fm finished state)" "done"

# ── I. what the tool wrote rides ─────────────────────────────────────────────
echo "I. riders"
fixture i
run finished > /dev/null
eq  "I the record is not owed — it is in its own commit" "$(cat "$D/prds/.claims/riders" 2>/dev/null | grep -c 'prds/finished/prd.md')" "0"
sed -i '' 's/- \[ \] two/- [x] two/' "$D/prds/building/specs/spec01.md"
OUT="$(run building)"; RC=$?
eq  "I the next collect is not stopped by the last one's record" "$RC" "0"
lacks "I finished's record is not on building's commit" "$(paths)" "prds/finished/prd.md"
lacks "I nothing rides on the line" "$(printf '%s\n' "$OUT" | grep '^▸')" "rides "
eq  "I building's own record is not owed either" "$(cat "$D/prds/.claims/riders" 2>/dev/null | grep -c 'prds/building/prd.md')" "0"
fixture i2
sed -i '' 's/^commit: 0000000/commit: 1111111/' "$D/prds/landed/prd.md"    # somebody's edit, no baseline
OUT="$(run finished)"; RC=$?
eq  "I2 exit 0" "$RC" "0"
lacks "I2 a foreign dirty prd.md is inherited without a baseline" "$(paths)" "prds/landed/prd.md"

# ── J. the finished condition ────────────────────────────────────────────────
echo "J. open boxes"
fixture j
printf '\n* [ ] a box in the body\n' >> "$D/prds/finished/prd.md"
OUT="$(run finished)"; RC=$?
eq  "J exit 1" "$RC" "1"
has "J names the file" "$OUT" "prds/finished/prd.md"
has "J names the box" "$OUT" "* [ ] a box in the body"
eq  "J no commit" "$(ncommits)" "1"
fixture j2
sed -i '' 's/- \[x\] `src/- [ ] `src/' "$D/prds/finished/specs/spec01.md"
OUT="$(run finished)"; RC=$?
eq  "J2 an open spec box exits 1" "$RC" "1"
has "J2 names the spec" "$OUT" "prds/finished/specs/spec01.md"
OUT="$(run building)"; RC=$?
eq  "J3 building (1/2) exits 1" "$RC" "1"
OUT="$(run landed)"; RC=$?
eq  "J4 a done PRD exits 1" "$RC" "1"
OUT="$(run nosuch)"; RC=$?
eq  "J5 no such PRD exits 1" "$RC" "1"

# ── K. --also ────────────────────────────────────────────────────────────────
echo "K. --also"
fixture k
mkdir -p "$D/prds/workflows"; echo 'atomic: x' > "$D/prds/workflows/x.md"
OUT="$(run finished --also "$D/prds/workflows/x.md")"; RC=$?
eq  "K --also without --also-note is usage" "$RC" "2"
OUT="$(run finished --also "$D/prds/workflows/x.md" --also-note "the fixture taught nothing")"; RC=$?
eq  "K exit 0" "$RC" "0"
has "K the file is on the commit" "$(paths)" "prds/workflows/x.md"
has "K named in the message" "$( cd "$D" && git log -1 --format=%B HEAD~1 )" "workflow: implement-a-spec — the fixture taught nothing"

# ── L. flags ─────────────────────────────────────────────────────────────────
echo "L. flags"
fixture l
OUT="$(run finished --bogus)"; RC=$?
eq  "L unknown flag is usage" "$RC" "2"
OUT="$(run finished --widen)"; RC=$?
eq  "L --widen without a path is usage" "$RC" "2"
OUT="$(run finished --as skeptic)"; RC=$?
has "L --as sets the persona term" "$(printf '%s\n' "$OUT" | grep '^▸')" "· as skeptic"

# ── N. the baseline: a file holding inherited and new hunks ──────────────────
echo "N. baseline hunks"
NOWORK=1 fixture n
# somebody's diff before the claim: a tracked file in the footprint, one edit
printf 'one\ntwo\nthree\nfour\nfive\nsix\nseven\neight\nnine\nten\n' > "$D/src/big.txt"
( cd "$D" && git add src/big.txt && git commit -q -m "big" )
sed -i '' 's/^two$/two-theirs/' "$D/src/big.txt"
OUT="$(run --snapshot finished)"; RC=$?
eq  "N --snapshot exits 0" "$RC" "0"
eq  "N the diff recorded" "$(grep -c '^+two-theirs' "$D/prds/.claims/finished/diff")" "1"
# the worker's run, and its edit on the same file, far from theirs
work
sed -i '' 's/^nine$/nine-ours/' "$D/src/big.txt"
OUT="$(run finished)"; RC=$?
eq  "N exit 0" "$RC" "0"
has "N the file is on the commit" "$(paths)" "src/big.txt"
has "N the worker's hunk landed" "$( cd "$D" && git show HEAD:src/big.txt )" "nine-ours"
lacks "N the inherited hunk did not" "$( cd "$D" && git show HEAD:src/big.txt )" "two-theirs"
has "N the inherited hunk is still in the tree" "$(cat "$D/src/big.txt")" "two-theirs"
eq  "N the file stays dirty by exactly that hunk" "$( cd "$D" && git diff --numstat -- src/big.txt | cut -f1,2 )" "$(printf '1\t1')"
has "N said on the line" "$(printf '%s\n' "$OUT" | grep '^▸')" "by hunk src/big.txt"

# ── O. inside the footprint, older than the claim ────────────────────────────
echo "O. the stop"
NOWORK=1 fixture o
echo theirs > "$D/src/theirs.txt"                  # untracked, in the footprint
run --snapshot finished > /dev/null
work
OUT="$(run finished)"; RC=$?
eq  "O exit 1" "$RC" "1"
has "O the path listed" "$OUT" "src/theirs.txt"
eq  "O no commit" "$(ncommits)" "1"
eq  "O prd.md unchanged" "$(fm finished state)" "claimed"
OUT="$(run finished --widen src/theirs.txt)"; RC=$?
eq  "O --widen takes it" "$RC" "0"
has "O and it is on the commit" "$(paths)" "src/theirs.txt"
NOWORK=1 fixture o2
printf 'a\n' > "$D/src/old.txt"; ( cd "$D" && git add src/old.txt && git commit -q -m old )
printf 'b\n' > "$D/src/old.txt"
run --snapshot finished > /dev/null                # every hunk of old.txt predates the claim
work
OUT="$(run finished)"; RC=$?
eq  "O2 a tracked file whose every hunk predates the claim stops" "$RC" "1"
has "O2 named" "$OUT" "src/old.txt"
fixture o3
printf 'a\n' > "$D/src/old.txt"; ( cd "$D" && git add src/old.txt && git commit -q -m old )
printf 'b\n' > "$D/src/old.txt"
touch -t 202608280900 "$D/src/old.txt"             # no baseline: mtime before the claim (10:00)
OUT="$(run finished)"; RC=$?
eq  "O3 no baseline: mtime before the claim stops" "$RC" "1"
has "O3 named" "$OUT" "src/old.txt"

# ── P. the gate against the baseline ─────────────────────────────────────────
echo "P. gate baseline"
NOWORK=1 fixture p 'gate: echo known-red; false'
run --snapshot finished > /dev/null
work
eq  "P the gate recorded" "$(head -1 "$D/prds/.claims/finished/gate")" "exit 1"
OUT="$(run finished)"; RC=$?
eq  "P a red gate whose every line is in the baseline is green" "$RC" "0"
has "P said" "$OUT" "known"
fixture p2 'gate: echo known-red; echo NEW-red; false'
mkdir -p "$D/prds/.claims/finished"; : > "$D/prds/.claims/finished/diff"; : > "$D/prds/.claims/finished/untracked"
printf 'exit 1\nknown-red\n' > "$D/prds/.claims/finished/gate"
OUT="$(run finished)"; RC=$?
eq  "P2 a new line is red" "$RC" "1"
has "P2 printed" "$OUT" "NEW-red"
eq  "P2 no commit" "$(ncommits)" "1"

# ── Q. a rename in the footprint ─────────────────────────────────────────────
echo "Q. rename"
NOWORK=1 fixture q
printf 'a\n' > "$D/src/a.txt"; ( cd "$D" && git add src/a.txt && git commit -q -m a )
run --snapshot finished > /dev/null
work
( cd "$D" && git mv src/a.txt src/b.txt )
OUT="$(run finished)"; RC=$?
eq  "Q exit 0" "$RC" "0"
has "Q the new name is on the commit" "$(paths)" "src/b.txt"
eq  "Q the old name is gone from HEAD" "$( cd "$D" && git ls-tree --name-only HEAD src/ | grep -c a.txt )" "0"

# ── R. the daemon is up ──────────────────────────────────────────────────────
# `serve.py` keeps its registry in state/ beside the script and re-plans every
# board it knows — so the daemon here is an isolated copy of the scripts on a
# spare port, and the real registry is proven untouched at the end.
echo "R. report posted"
fixture r
SRV="$TOP/srv/resources"; mkdir -p "$SRV/board"
cp "$ROOT"/resources/*.py "$SRV/"
cp "$ROOT"/resources/board/*.py "$ROOT"/resources/board/*.css "$ROOT"/resources/board/*.js "$SRV/board/"
REG="$ROOT/resources/board/state/serve.json"
REG_BEFORE="$( [ -f "$REG" ] && cksum < "$REG" )"
SPARE="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')"
export PEARDE_PORT="$SPARE"
trap 'PEARDE_PORT="$SPARE" python3 "$SRV/board/serve.py" stop >/dev/null 2>&1; rm -rf "$TOP"' EXIT
ENS="$( cd "$D" && python3 "$SRV/board/serve.py" ensure "$D/prds" 2>&1 )"; RC=$?
eq  "R the daemon came up on the spare port and registered the fixture" "$RC" "0"
has "R ...under the board's declared name" "$ENS" "registered fixture"
OUT="$(run finished)"; RC=$?
eq  "R exit 0" "$RC" "0"
has "R the line says report posted" "$(printf '%s\n' "$OUT" | grep '^▸')" "report posted"
lacks "R ...and not daemon down" "$OUT" "daemon down"
has "R ## Report is in prd.md" "$(cat "$D/prds/finished/prd.md")" "## Report"
has "R ## Report holds the verify's exit" "$(sed -n '/^## Report/,$p' "$D/prds/finished/prd.md")" "spec01: exit 0"
eq  "R done" "$(fm finished state)" "done"
has "R the daemon knows the fixture" "$(python3 "$SRV/board/serve.py" status 2>&1)" "$D/prds"
PEARDE_PORT="$SPARE" python3 "$SRV/board/serve.py" stop >/dev/null 2>&1
export PEARDE_PORT=1
eq  "R the real registry is untouched" "$( [ -f "$REG" ] && cksum < "$REG" )" "$REG_BEFORE"
eq  "R the copy's registry never learned the fixture" "$(tr -d '[:space:]' < "$SRV/board/state/serve.json" 2>/dev/null)" "[]"

# ── S. the snapshot record, and --dry after it ───────────────────────────────
echo "S. snapshot"
NOWORK=1 fixture s
echo stray > "$D/stray.txt"
run --snapshot finished > /dev/null
eq  "S the record is at, diff, gate, untracked" "$(ls "$D/prds/.claims/finished" | tr '\n' ' ')" "at diff gate untracked "
work
OUT="$(run finished --dry)"; RC=$?
eq  "S --dry after the snapshot exits 0" "$RC" "0"
has "S --dry lists the inherited path" "$(printf '%s\n' "$OUT" | grep -A1 'inherited, not added')" "stray.txt"
eq  "S --dry writes nothing to prd.md" "$( cd "$D" && git status --porcelain -- prds/finished/prd.md )" ""
eq  "S --dry commits nothing" "$(ncommits)" "1"

# ── M. COMMANDS ──────────────────────────────────────────────────────────────
echo "M. COMMANDS"
eq "M the module exposes COMMANDS['collect']" "$( cd "$ROOT/resources/board" && python3 -c 'import collect; print(sorted(collect.COMMANDS))' )" "['collect']"

# ── Z. every commit the harness made ─────────────────────────────────────────
echo "Z. .claims never committed"
eq  "Z no path under prds/.claims/ on any commit above" "$(for d in "$TOP"/*/; do [ -d "$d/.git" ] && ( cd "$d" && git log --name-only --format= ); done | grep -c 'prds/.claims/')" "0"

echo
echo "$((PASS+FAIL)) checks · $PASS pass · $FAIL fail"
[ "$FAIL" -eq 0 ]
