#!/usr/bin/env bash
# complexity-is-guarded-like-priority — every hand-written number in plan.py is
# guarded, and a bad one is REPORTED and weighed at the board average rather
# than silently at zero.
#
# Every fixture is a board built in a fresh `mktemp -d` and removed at exit —
# a `prd.md` left anywhere under `prds/` becomes a real PRD the scan picks up.
set -u
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
PLAN="$ROOT/resources/board/plan.py"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
pass=0; fail=0
ok()   { pass=$((pass+1)); }
no()   { fail=$((fail+1)); echo "FAIL: $1"; }
check(){ if [ "$2" = "$3" ]; then ok; else no "$1 — want [$3] got [$2]"; fi; }
has()  { if grep -qF -- "$3" "$2"; then ok; else no "$1 — no [$3] in $(basename "$2")"; fi; }
hasnt(){ if grep -qF -- "$3" "$2"; then no "$1 — unwanted [$3]"; else ok; fi; }

board() {                      # a fresh board; echoes its prds dir.
  # `B=$(board)` runs this in a subshell, so a counter kept here would never
  # reach the caller and every fixture would land on ONE board.
  local d; d=$(mktemp -d "$TMP/board.XXXXXX"); mkdir -p "$d/prds"
  echo "$d/prds"
}
prd() {                        # prd <board> <name> <frontmatter-lines...>
  local b=$1 name=$2; shift 2
  mkdir -p "$b/$name"
  { echo "---"; printf '%s\n' "$@"; echo "---"; echo; echo "# $name"; } \
    > "$b/$name/prd.md"
}
spec() {                       # spec <board> <prd> <file> <frontmatter-lines...>
  local b=$1 name=$2 f=$3; shift 3
  mkdir -p "$b/$name/specs"
  { echo "---"; printf '%s\n' "$@"; echo "---"; echo; echo "# $f"; } \
    > "$b/$name/specs/$f"
}
settings() { local b=$1; shift; { echo "---"; printf '%s\n' "$@"; echo "---"; } > "$b/settings.md"; }
run() {                        # run <board> <cmd...> -> $OUT/$ERR/$RC
  local b=$1; shift
  OUT="$TMP/out.$$"; ERR="$TMP/err.$$"
  python3 "$PLAN" "$@" "$b" >"$OUT" 2>"$ERR" </dev/null; RC=$?
}

echo "── 1. the PRD's own fixture: a spec carrying \`complexity: x\` ──"
B=$(board); prd "$B" typo "state: specced" "priority: 50" "complexity: 0"
spec "$B" typo spec01.md "complexity: x" "footprint:" "  - src/a.py"
prd "$B" other "state: open" "priority: 40" "complexity: 30"
run "$B" scan
check "scan exits 0"                     "$RC" 0
has   "scan still answers"               "$OUT" "counts:"
has   "the report names the spec file"   "$ERR" "typo/specs/spec01.md"
has   "the report names the key"         "$ERR" "complexity:"
has   "the report names the bad value"   "$ERR" "'x'"
has   "the report says how it is weighed" "$ERR" "weighed as unscored"
check "reported ONCE, not once per read" "$(grep -c "typo/specs/spec01.md" "$ERR")" 1
# `other` is the only scored PRD, so the board average is 30: the bad PRD is
# weighed at "we do not know this one's size", never at zero.
has   "the bad PRD is weighed at the board average" "$OUT" "typo · p50 · w30"
hasnt "no traceback"                     "$ERR" "Traceback"

echo "── 2. every other command on the same board ──"
for c in plan status gantt calibrate; do
  run "$B" $c
  check "$c exits 0 with a bad complexity on the board" "$RC" 0
done

echo "── 3. the same typo on prd.md, not on a spec ──"
B=$(board); prd "$B" bad "state: open" "priority: 50" "complexity: high"
prd "$B" good "state: open" "priority: 50" "complexity: 20"
run "$B" scan
check "scan exits 0"                     "$RC" 0
has   "the report names the PRD"         "$ERR" "bad — complexity: 'high'"
has   "weighed at the board average"     "$OUT" "bad · p50 · w20"

echo "── 4. hours() — the shape matches, the number does not ──"
# the PRD says hours() 'already tolerates a bad string'. It does not: a value
# matching ^[\d.]+$ reaches float() and raises. REFUTED, fixtures below.
for v in ".." "1.2.3" "..h"; do
  B=$(board); prd "$B" e "state: open" "priority: 50" "est: $v"
  run "$B" scan
  check "est: $v — scan exits 0"         "$RC" 0
  has   "est: $v — reported"             "$ERR" "e — est: '$v'"
done
B=$(board); prd "$B" e "state: open" "priority: 50" "est: 0h" "complexity: 5"
run "$B" scan
check "est: 0h — scan exits 0"           "$RC" 0
hasnt "est: 0h — an honest zero is not reported" "$ERR" "est:"

echo "── 5. priority as a list — TypeError, which two guards did not catch ──"
B=$(board); prd "$B" p "state: open" "complexity: 10" "priority:" "  - 1" "  - 2"
run "$B" scan
check "scan exits 0"                     "$RC" 0
has   "reported"                         "$ERR" "p — priority:"
run "$B" gantt
check "gantt exits 0"                    "$RC" 0

echo "── 6. settings.md is hand-written too ──"
B=$(board); prd "$B" a "state: open" "priority: 50"      # nothing scored
settings "$B" "weight-default: many"
run "$B" scan
check "weight-default — scan exits 0"    "$RC" 0
has   "weight-default reported"          "$ERR" "settings.md — weight-default: 'many'"
B=$(board); prd "$B" a "state: open" "priority: 50" "complexity: 10"
settings "$B" "gantt-day: .."
run "$B" gantt
check "gantt-day — gantt exits 0"        "$RC" 0
has   "gantt-day reported"               "$ERR" "settings.md — gantt-day: '..'"
B=$(board); prd "$B" a "state: claimed" "claim: bob 2026-08-28 10:00" \
  "priority: 50" "complexity: 10"
settings "$B" "claim-ttl: .."
run "$B" scan
check "claim-ttl — scan exits 0"         "$RC" 0
has   "claim-ttl reported"               "$ERR" "settings.md — claim-ttl: '..'"

echo "── 7. write_history and calib_rows read complexity too ──"
B=$(board); prd "$B" h "state: done" "priority: 50" "complexity: nope" "actual: 4h"
prd "$B" h2 "state: open" "priority: 50" "complexity: 12"
python3 - "$PLAN" "$B" >"$TMP/wh.out" 2>"$TMP/wh.err" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("planlib", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.write_history(sys.argv[2])
print("history written")
PY
check "write_history exits 0"            "$?" 0
has   "write_history did not crash"      "$TMP/wh.out" "history written"
has   "write_history reported the bad value" "$TMP/wh.err" "h — complexity: 'nope'"
run "$B" calibrate
check "calibrate exits 0"                "$RC" 0

echo "── 8. a clean board says nothing ──"
B=$(board); prd "$B" a "state: open" "priority: 50" "complexity: 10" "est: 2h"
prd "$B" b "state: done" "priority: 10" "complexity: 5" "actual: 3h"
settings "$B" "workers: 3" "weight-default: 50" "gantt-day: 8h"
run "$B" scan
check "clean board — scan exits 0"       "$RC" 0
hasnt "clean board — nothing reported"   "$ERR" "is not a number"
check "clean board — stderr is empty"    "$(wc -c <"$ERR" | tr -d ' ')" 0
# a number written as a quoted string is still a number
B=$(board); prd "$B" q "state: open" "priority: \"50\"" "complexity: \"30\""
run "$B" scan
check "quoted numbers still read"        "$RC" 0
hasnt "quoted numbers are not reported"  "$ERR" "is not a number"
has   "quoted complexity is the weight"  "$OUT" "q · p50 · w30"

echo "── 9. the census, asserted over the file ──"
# every remaining float() in plan.py sits inside a guard; no float() reads
# frontmatter or settings directly any more.
check "no float() over fm.get"       "$(grep -c 'float(.*\[\"fm\"\]\.get\|float(fm\.get' "$PLAN")" 0
check "no float() over settings.get" "$(grep -c 'float(settings\.get' "$PLAN")" 0
check "no int() over settings.get unguarded" \
      "$(grep -c 'int(board_settings' "$PLAN")" 1     # inside plan_workers' try
# 3 calls, each inside a guard: hours()'s try, claim_ttl()'s isdigit, num()'s
# try. The 4th `grep` hit is the word in the block comment above `bad_value`.
check "float() CALLS remaining"      "$(grep -c '^ *[a-z].*float(' "$PLAN")" 3
# The line above counts. This one reads the RULE. A grep census is spelling-
# and indent-dependent — `EST = float(x)`, or a call at module level, slips
# past it — so the rule is asserted over the syntax tree instead: every
# `float()` anywhere in the file sits inside one of the three functions that
# guard it. A new unguarded read of a hand-written number fails here whatever
# it is named and however it is laid out. This is the only mechanism the rule
# has — nothing on this repo runs this harness for you.
LOOSE=$(python3 - "$PLAN" <<'CENSUS'
import ast, sys
tree = ast.parse(open(sys.argv[1], encoding="utf-8").read())
guards = {"hours", "num", "claim_ttl"}


def calls(node):
    return {n.lineno for n in ast.walk(node)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == "float"}


inside = set()
for fn in ast.walk(tree):
    if isinstance(fn, ast.FunctionDef) and fn.name in guards:
        inside |= calls(fn)
print(" ".join(str(ln) for ln in sorted(calls(tree) - inside)))
CENSUS
)
check "every float() sits in hours/num/claim_ttl" "$LOOSE" ""
has   "num() exists"                 "$PLAN" "def num(fm, key, where="
has   "dur() exists"                 "$PLAN" "def dur(fm, key, where="
has   "bad_value() exists"           "$PLAN" "def bad_value(where, key, v):"
python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" "$PLAN" 2>/dev/null
check "plan.py parses"               "$?" 0

echo "── 10. a value that is ONLY a comment is an empty value ──"
# found by the report: the PRD template ships `est:   # the weight, only when
# complexity is absent`, and KEY_RE ate the leading spaces, so strip_comment's
# `\s+#` did not match and every reader of `est` got the comment TEXT.
# NO `complexity:` on this fixture, deliberately. `plan.py` reads the weight as
# `num(fm, "complexity") or dur(fm, "est")`, so any non-zero complexity
# short-circuits the `or` and `est` is never read at all — the two checks below
# then pass on a board where nothing parsed the line they are about, and the
# `\s+#.*$` regression they exist to catch sails through them. Absent
# complexity is also what the template line itself describes.
B=$(board); prd "$B" c "state: open" "priority: 50" \
  "est:   # the weight, only when complexity is absent. Not a duration"
run "$B" scan
check "a comment-only est — scan exits 0"  "$RC" 0
hasnt "a comment-only est is not reported" "$ERR" "is not a number"
check "a comment-only est is empty, so it is silent" "$(wc -c <"$ERR" | tr -d ' ')" 0
B=$(board); prd "$B" c "state: open" "priority: 50" "est: 4h  # trailing note" \
  "complexity: 0"
run "$B" scan
has   "a trailing comment is still stripped" "$OUT" "c · p50 · w4"
B=$(board); prd "$B" c "state: open" "priority: 50" "complexity: 3" "repo: a#b"
run "$B" scan
check "a # inside a word is not a comment"  "$RC" 0
hasnt "…and is not reported"                "$ERR" "is not a number"
# ...and the VALUE still holds its `#`. The two lines above do not say that:
# `repo: a` would exit 0 and be just as silent, so read the parsed value back.
# The regression this catches is not the old `\s+#.*$` — that one leaves `a#b`
# alone and breaks the comment-ONLY case, which the `wc -c` check above already
# fails on. It is the NAIVE simplification, `#.*$`: it cuts `a#b` to `a` and
# passes every other check in this section, both comment cases included. That
# is what the `^` alternative in `(^|\s+)` is holding open, and without the
# line below nothing on this board would notice it going.
python3 - "$PLAN" "$B/c/prd.md" >"$TMP/repo.txt" 2>&1 <<'REPO'
import importlib.util, sys
sp = importlib.util.spec_from_file_location("planlib", sys.argv[1])
m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
print("repo=" + str(m.parse_prd(sys.argv[2])[0].get("repo")))
REPO
has   "…and the # survives into the value"  "$TMP/repo.txt" "repo=a#b"

echo "── 11. the real board is unmoved ──"
run "$ROOT/prds" scan
check "the repo's own board scans"       "$RC" 0
hasnt "the repo's own board reports nothing bad" "$ERR" "is not a number"

echo
echo "$((pass+fail)) checks · $pass pass · $fail fail"
[ "$fail" -eq 0 ]
