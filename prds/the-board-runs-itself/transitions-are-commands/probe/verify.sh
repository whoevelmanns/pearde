#!/usr/bin/env bash
# transitions-are-commands — the probe's harness. One line per assertion, a
# count at the end. The board is built in a temp dir and removed at exit;
# nothing here touches the real board.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
T="$REPO/resources/board/transitions.py"
D="$(mktemp -d)"
S="$(mktemp -d)"     # scratch outside the fixture's git repo
trap 'rm -rf "$D" "$S"' EXIT
python3 "$HERE/fixture.py" "$D" >/dev/null
B="$D/prds"
export PEARDE_AS=engineer
( cd "$D" && git init -q && git add -A && git -c user.name=p -c user.email=p@p commit -qm fixture )

pass=0; fail=0; pend=0
ok()   { pass=$((pass+1)); echo "  ok   $1"; }
bad()  { fail=$((fail+1)); echo "  FAIL $1"; [ -n "${2:-}" ] && echo "       $2"; }
check() { if [ "$2" = "0" ]; then ok "$1"; else bad "$1" "${3:-}"; fi; }
# A check red on a finding outside this PRD's footprint: counted apart, so
# the count says what this tree can close and what waits on another file.
pending() { if [ "$2" = "0" ]; then ok "$1"; else pend=$((pend+1)); echo "  PEND $1"; echo "       ${3:-}"; fi; }
run()  { OUT="$(python3 "$T" "$@" --board "$B" 2>"$S/err")"; RC=$?; ERR="$(cat "$S/err")"; }
state() { sed -n 's/^state: *\([a-z-]*\).*/\1/p' "$B/$1/prd.md" | head -1; }
refused() { # name, expected substring, cmd...
  local name="$1" want="$2"; shift 2
  run "$@"
  if [ "$RC" = "1" ] && [[ "$ERR" == *"$want"* ]]; then ok "$name"; else bad "$name" "rc=$RC err=$ERR"; fi
}
clean() { ( cd "$D" && git status --porcelain ) ; }

echo "persona"
OUT="$(env -u PEARDE_AS python3 "$T" set next open --force --board "$B" 2>&1)"; RC=$?
check "no --as and no PEARDE_AS exits 1" "$([ "$RC" = 1 ] && [[ "$OUT" == *PEARDE_AS* ]]; echo $?)" "$OUT"
check "nothing written by the refused command" "$([ -z "$(clean)" ]; echo $?)" "$(clean)"

echo "forbidden transitions — each exits 1 naming the gate, nothing written"
refused "claim gated on needs names building"          "needs: building"        claim next impl-1
refused "claim a claimed PRD"                          "is \`claimed\`"          claim building impl-9
refused "claim with a footprint clash names both"      "src/shared"             claim clash impl-3
refused "  …and the clashing PRD"                      "building"               claim clash impl-3
refused "claim with a dangling workflow names the slug" "no-such-route"         claim dangling impl-3
refused "claim a parent names the live child"          "leaf"                   claim big impl-3
refused "  …the child by name"                         "second"                 claim big impl-3
refused "claim a name that is nothing"                 "no PRD named"           claim nosuch impl-3
refused "release to question with no round"            "no \`## Questions\`"    release probing question
refused "release to question with a bad round"         "recommended"            release badround question
refused "release analyzing → failed is not an edge"    "analyzing → refine"     release probing failed
refused "release to blocked with no needs"             "needs:"                 release building blocked
refused "release to failed with no ## Failure"         "## Failure"             release building failed
refused "set without --force on a non-edge"            "no command moves"       set next done
refused "set without --force on a gated edge is gated" "needs: building"        set next claimed --worker impl-1
refused "retry needs failed"                           "not failed"             retry next
refused "unblock needs blocked"                        "not blocked"            unblock next
refused "answer a question that is not there"          "Q9"                     answer asking Q9 "x"
refused "add a taken slug"                             "taken"                  add "next"
refused "defer a held PRD"                             "held"                   defer probing
check "git diff empty after every refusal" "$([ -z "$(clean)" ]; echo $?)" "$(clean)"
check ".transitions.jsonl not created by a refusal" "$([ ! -e "$B/.transitions.jsonl" ]; echo $?)"

echo "the gated PRD"
run claim next impl-1
check "claim next exits 1" "$([ "$RC" = 1 ]; echo $?)"
run set building done --force
check "set --force exits 0" "$([ "$RC" = 0 ]; echo $?)" "$ERR"
check "the line says forced" "$([[ "$OUT" == "▸ building: claimed → done · forced · "* ]]; echo $?)" "$OUT"
run claim next impl-1
check "claim next now succeeds" "$([ "$RC" = 0 ]; echo $?)" "$ERR"
check "state is claimed" "$([ "$(state next)" = claimed ]; echo $?)"
check "claim: impl-1 <now> written" "$(grep -q '^claim: impl-1 20[0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]$' "$B/next/prd.md"; echo $?)"
NUM="$(cd "$D" && git diff --numstat prds/next/prd.md | cut -f1,2)"
check "the diff is two lines written: state changed, claim added (numstat 2 1)" "$([ "$NUM" = "$(printf '2\t1')" ]; echo $?)" "$NUM"
check "the line opens with the transition" "$([[ "$OUT" == "▸ next: specced → claimed · done "* ]]; echo $?)" "$OUT"
check "as <persona> is last" "$([[ "$OUT" == *" · as engineer" ]]; echo $?)" "$OUT"
check "@<w> workers from settings" "$([[ "$OUT" == *" @2 workers · "* ]]; echo $?)" "$OUT"

echo "the progress terms equal scan's"
SCAN="$(python3 "$REPO/resources/board/plan.py" scan "$B" 2>/dev/null | sed -n 's/^progress: //p')"
run set clash open --force
check "scan's terms after the move are on the line" "$([[ "$OUT" == *"$(python3 "$REPO/resources/board/plan.py" scan "$B" 2>/dev/null | sed -n 's/^progress: //p')"* ]]; echo $?)" "line=$OUT"
check "  …and they moved (the line is not stale)" "$([ "$SCAN" != "$(python3 "$REPO/resources/board/plan.py" scan "$B" 2>/dev/null | sed -n 's/^progress: //p')" ]; echo $?)"
check "ready/blocked/collect are on the line" "$([[ "$OUT" == *" · ready "*" · blocked "*" · collect 1 @"* ]]; echo $?)" "$OUT"

echo "answer"
run answer asking Q1 "paint it red"
check "Q1 answered, exit 0" "$([ "$RC" = 0 ]; echo $?)" "$ERR"
check "still question after one" "$([ "$(state asking)" = question ]; echo $?)"
run answer asking Q2 "12px"
check "Q2 answered, exit 0" "$([ "$RC" = 0 ]; echo $?)" "$ERR"
run answer asking Q3 "go"
check "Q3 answered, exit 0, and the line moves it" "$([ "$RC" = 0 ] && [[ "$OUT" == "▸ asking: question → open · "* ]]; echo $?)" "$OUT $ERR"
check "asking is open" "$([ "$(state asking)" = open ]; echo $?)"
N="$(grep -c '^\*\*Q[123]\*\* \*(answered 20[0-9-]* [0-9:]*)\* — ' "$B/asking/prd.md")"
check "three stamped lines under ## Answers" "$([ "$N" = 3 ]; echo $?)" "$N"
# `badround` is on this board to be refused, so the check is read per PRD —
# the gate reads it the same way — and `asking`'s lines are the ones owed silence
QL="$(python3 "$REPO/resources/questions.py" check "$B" 2>&1 | grep '^asking:')"
check "questions.py check silent on asking — a numbered line under a ### head is an answer" "$([ -z "$QL" ]; echo $?)" "$QL"
refused "a second answer to Q1 exits 1 with answered" "answered" answer asking Q1 "again"

echo "release, retry, unblock, defer"
run release probing refine
check "analyzing → refine" "$([ "$RC" = 0 ] && [ "$(state probing)" = refine ]; echo $?)" "$ERR"
check "claim: cleared" "$(! grep -q '^claim:' "$B/probing/prd.md"; echo $?)"
run set asking analyzing --force
run release asking question
check "analyzing → question with a round the check accepts" "$([ "$RC" = 0 ] && [ "$(state asking)" = question ]; echo $?)" "${ERR:0:160}"
[ "$(state asking)" = question ] || run set asking question --force
run retry broke
check "failed → open" "$([ "$RC" = 0 ] && [ "$(state broke)" = open ]; echo $?)" "$ERR"
check "## Failure is gone" "$(! grep -q '^## Failure' "$B/broke/prd.md"; echo $?)"
check "  …and stands under ## History with its text" "$(grep -q '^## History' "$B/broke/prd.md" && grep -q 'fixture was missing' "$B/broke/prd.md"; echo $?)"
check "  …frontmatter untouched but state" "$(grep -q '^priority: 25$' "$B/broke/prd.md" && grep -q '^blast-radius: low$' "$B/broke/prd.md"; echo $?)"
run unblock stuck
check "blocked → specced when needs are done" "$([ "$RC" = 0 ] && [ "$(state stuck)" = specced ]; echo $?)" "$ERR"
run claim stuck impl-4
check "  …and claim then takes it" "$([ "$RC" = 0 ] && [ "$(state stuck)" = claimed ]; echo $?)" "$ERR"
run defer big/second
check "open → deferred" "$([ "$RC" = 0 ] && [ "$(state big/second)" = deferred ]; echo $?)" "$ERR"
check "  …and scan parks it" "$(python3 "$REPO/resources/board/plan.py" scan "$B" 2>/dev/null | grep -q '^parked: big/second'; echo $?)"
refused "defer twice" "already" defer big/second

echo "add"
run add "A brand new thing" --priority 7 --body - <<< "The body, from stdin."
check "add exits 0 and prints — → open" "$([ "$RC" = 0 ] && [[ "$OUT" == "▸ a-brand-new-thing: — → open · "* ]]; echo $?)" "$OUT $ERR"
F="$B/a-brand-new-thing/prd.md"
check "state open, origin requested, priority 7" "$(grep -q '^state: open' "$F" && grep -q '^origin: requested' "$F" && grep -q '^priority: 7' "$F"; echo $?)"
check "the title line" "$(grep -q '^# A brand new thing$' "$F"; echo $?)"
check "the body from stdin" "$(grep -q '^The body, from stdin\.$' "$F"; echo $?)"
check "the template's comments survive" "$(grep -q 'Ordering reads three axes' "$F"; echo $?)"
check "  …and no template placeholder title" "$(! grep -q '<Title' "$F"; echo $?)"
run add "Under big" --parent big
check "add --parent files under the parent" "$([ "$RC" = 0 ] && [ -f "$B/big/under-big/prd.md" ]; echo $?)" "$ERR"

echo "memory"
ROWS="$(wc -l < "$B/.transitions.jsonl" | tr -d ' ')"
check ".transitions.jsonl has one row per state move (13)" "$([ "$ROWS" = 13 ]; echo $?)" "$ROWS"
check "every row is {t,prd,from,to,calls,reads,refused,tokens}" "$(TR="$B/.transitions.jsonl" python3 -c 'import json,os
for l in open(os.environ["TR"]):
    r=json.loads(l); assert sorted(r)==["calls","from","prd","reads","refused","t","to","tokens"], r'; echo $?)"
check "the add row is from null" "$(grep -q '"from": null, "prd": "a-brand-new-thing", "reads": [^,]*, "refused": [^,]*, "t": "20[^"]*", "to": "open"' "$B/.transitions.jsonl"; echo $?)"
check ".history.jsonl byte-identical" "$(cd "$D" && git diff --quiet -- prds/.history.jsonl; echo $?)"
STRAY="$(cd "$D" && git status --porcelain | grep -v 'prds/[a-z/-]*prd.md$' | grep -v '^?? prds/a-brand-new-thing/$' | grep -v '^?? prds/big/under-big/$' | grep -v '^?? prds/.transitions.jsonl$' | grep -v '^?? prds/.claims/$')"
check "only prd.md files, the two new PRDs, .transitions.jsonl and .claims/ moved" "$([ -z "$STRAY" ]; echo $?)" "$STRAY"

echo "master board — @<member>/<rel> writes at the member's real path"
M="$(mktemp -d)"; mkdir -p "$M/prds"
printf -- '---\nname: master\nmembers:\n  - example: %s\n---\n' "$B" > "$M/prds/settings.md"
OUT="$(python3 "$T" set @example/landed open --force --board "$M/prds" 2>&1)"; RC=$?
check "set @example/landed from the master exits 0" "$([ "$RC" = 0 ]; echo $?)" "$OUT"
check "  …the member's prd.md moved" "$([ "$(state landed)" = open ]; echo $?)"
check "  …the row landed in the member's .transitions.jsonl" "$(grep -q '"prd": "landed"' "$B/.transitions.jsonl" && [ ! -e "$M/prds/.transitions.jsonl" ]; echo $?)"
check "  …the line names the qualified PRD" "$([[ "$OUT" == "▸ @example/landed: done → open · forced · "* ]]; echo $?)" "$OUT"
rm -rf "$M"

echo "COMMANDS"
check "COMMANDS exposes the nine names" "$(python3 -c "
import sys; sys.path.insert(0,'$REPO/resources/board'); import transitions as t
assert sorted(t.COMMANDS)==['add','answer','claim','defer','release','retry','set','sweep','unblock'], sorted(t.COMMANDS)
assert all(callable(f) for f in t.COMMANDS.values())
"; echo $?)"

echo
echo "$((pass+fail+pend)) checks · $pass pass · $fail fail · $pend pending on resources/questions.py"
[ "$fail" = 0 ]
