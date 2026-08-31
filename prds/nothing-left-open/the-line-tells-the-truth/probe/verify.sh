#!/usr/bin/env bash
# the-line-tells-the-truth — the probe's harness.
#
# Four things on a copy of the example board, never the real one: `collect`
# refuses without a persona through transitions.py's one refusal; `set
# --force` clears a `claim:` the target cannot carry; the line's first term
# is `done`; `vision` and `example` declare their flags. One line per
# assertion, a count at the end. Every command carries `--board <copy>`.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
PLAN="$ROOT/resources/board/plan.py"
COLLECT="$ROOT/resources/board/collect.py"
TRANS="$ROOT/resources/board/transitions.py"
BRIEF="$ROOT/resources/board/brief.py"
PEARDE="$ROOT/resources/pearde.py"
STATUS="$ROOT/resources/statusline.sh"
export PEARDE_PORT=1            # nothing listens there — the daemon is "down"
export GIT_AUTHOR_NAME=probe GIT_AUTHOR_EMAIL=probe@x \
       GIT_COMMITTER_NAME=probe GIT_COMMITTER_EMAIL=probe@x
unset PEARDE_AS
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); echo "  ok   $1"; }
bad()  { FAIL=$((FAIL+1)); echo "  FAIL $1"; [ -n "${2:-}" ] && echo "       got:  $2"; [ -n "${3:-}" ] && echo "       want: $3"; }
eq()   { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1" "$2" "$3"; fi; }
has()  { if printf '%s' "$2" | grep -qF -- "$3"; then ok "$1"; else bad "$1" "$2" "contains: $3"; fi; }
lacks(){ if printf '%s' "$2" | grep -qF -- "$3"; then bad "$1" "$2" "without: $3"; else ok "$1"; fi; }

TOP="$(mktemp -d)"; SCRATCH="$(mktemp -d)"
trap 'rm -rf "$TOP" "$SCRATCH"' EXIT
ERR="$SCRATCH/err"

# a fresh copy of the example, a repo around it, one commit, timestamps fresh
fixture() {
  local d="$TOP/$1"
  python3 "$PLAN" example "$d" >/dev/null 2>&1
  find "$d" -type f -exec touch {} +
  ( cd "$d" && git init -q -b main && git add -A && git commit -qm init )
  echo "$d"
}
tree_sum() { ( cd "$1" && git status --porcelain && cat prds/.transitions.jsonl 2>/dev/null ) | md5 -q; }

# ── A. collect refuses without a persona ─────────────────────────────────────
echo "A. collect refuses without a persona"
D="$(fixture a)"; B="$D/prds"
S0="$(tree_sum "$D")"
OUT="$(python3 "$COLLECT" finished --board "$B" 2>"$ERR")"; RC=$?
eq   "A1 collect finished, no --as, no PEARDE_AS → exit 1"   "$RC" "1"
has  "A2 …names PEARDE_AS"                                    "$(cat "$ERR")" "PEARDE_AS"
has  "A3 …names the install line"                             "$(cat "$ERR")" "export PEARDE_AS=engineer"
has  "A4 …is the transitions.py refusal, word for word"       "$(cat "$ERR")" "collect: refused — persona: \`--as <id>\` on the line, or PEARDE_AS in the environment"
eq   "A5 …writes nothing"                                     "$(tree_sum "$D")" "$S0"
lacks "A6 …no line printed"                                   "$OUT" "▸"
OUT="$(python3 "$COLLECT" --snapshot building --board "$B" 2>"$ERR")"; RC=$?
eq   "A7 --snapshot without a persona refuses too"            "$RC" "1"
OUT="$(python3 "$COLLECT" --bogus finished --board "$B" 2>"$ERR")"; RC=$?
eq   "A8 an unknown flag still exits 2, before the persona"   "$RC" "2"
has  "A9 …naming the flag"                                    "$(cat "$ERR")" "unknown flag --bogus"
OUT="$(PEARDE_AS=skeptic python3 "$COLLECT" finished --board "$B" --dry --trust 2>"$ERR")"; RC=$?
eq   "A10 PEARDE_AS alone is read (it was ignored before)"    "$RC" "0"
has  "A11 …the dry line ends with the env persona"            "$OUT" "· as skeptic"
# --trust: the example's spec01 verify wants pytest; the persona is the subject here
OUT="$(python3 "$COLLECT" finished --board "$B" --as engineer --trust 2>"$ERR")"; RC=$?
eq   "A12 --as engineer lands"                                "$RC" "0"
has  "A13 …▸ finished: claimed → done"                        "$OUT" "▸ finished: claimed → done"
has  "A14 …as engineer last"                                  "$(tail -1 <<<"$OUT")" "· as engineer"
eq   "A15 state: done"                                        "$(grep -c '^state: done' "$B/finished/prd.md")" "1"

# ── B. set --force clears a claim the target cannot carry ────────────────────
echo "B. set --force clears a claim the target cannot carry"
D="$(fixture b)"; B="$D/prds"
eq   "B1 building starts claimed with a claim"                "$(grep -c '^claim: ' "$B/building/prd.md")" "1"
OUT="$(python3 "$BRIEF" building --board "$B" --as engineer 2>&1)"; RC=$?
has  "B2 brief says held before"                              "$OUT" "held"
S0="$(tree_sum "$D")"
OUT="$(python3 "$TRANS" set building open --force --dry --as engineer --board "$B" 2>"$ERR")"; RC=$?
eq   "B3 --dry --force exits 0"                               "$RC" "0"
eq   "B4 …writes nothing"                                     "$(tree_sum "$D")" "$S0"
eq   "B5 …claim still there"                                  "$(grep -c '^claim: ' "$B/building/prd.md")" "1"
OUT="$(python3 "$TRANS" set building claimed --force --as engineer --board "$B" 2>"$ERR")"; RC=$?
eq   "B6 forcing the state it is in is refused"               "$RC" "1"
eq   "B7 …claim intact"                                       "$(grep -c '^claim: ' "$B/building/prd.md")" "1"
OUT="$(python3 "$TRANS" set building analyzing --force --as engineer --board "$B" 2>"$ERR")"; RC=$?
eq   "B8 forced into analyzing — a claim-carrying state — exit 0" "$RC" "0"
eq   "B8b …the claim is kept"                                  "$(grep -c '^claim: ' "$B/building/prd.md")" "1"
OUT="$(python3 "$TRANS" set building open --force --as engineer --board "$B" 2>"$ERR")"; RC=$?
eq   "B9 set building open --force exits 0"                   "$RC" "0"
has  "B10 …the line says forced"                              "$OUT" "▸ building: analyzing → open · forced"
eq   "B11 …no claim: left"                                    "$(grep -c '^claim: ' "$B/building/prd.md")" "0"
eq   "B12 …state: open"                                       "$(grep -c '^state: open' "$B/building/prd.md")" "1"
OUT="$(python3 "$BRIEF" building --board "$B" --as engineer 2>&1)"; RC=$?
lacks "B13 brief no longer says held"                         "$OUT" "held"
OUT="$(python3 "$TRANS" set building deferred --force --as engineer --board "$B" 2>"$ERR")"; RC=$?
eq   "B14 forced to deferred — exit 0"                        "$RC" "0"
eq   "B15 …no claim:"                                         "$(grep -c '^claim: ' "$B/building/prd.md")" "0"
OUT="$(python3 "$TRANS" set building shelved --force --as engineer --board "$B" 2>"$ERR")"; RC=$?
eq   "B16 forced to a parked word of the user's own — exit 0" "$RC" "0"
eq   "B17 …no claim:"                                         "$(grep -c '^claim: ' "$B/building/prd.md")" "0"

# ── C. the first term of the line is done ────────────────────────────────────
echo "C. the first term of the line is done"
D="$(fixture c)"; B="$D/prds"
OUT="$(python3 "$PLAN" scan "$B" 2>&1)"
has  "C1 scan: progress: done"                                "$OUT" "progress: done "
lacks "C2 …never asked"                                       "$OUT" "asked"
# <rd>/<rn> only: statusline.sh weights <rp> by `est:` hours, scan by complexity — a finding, not the rename's
PD="$(sed -n 's/^progress: done \([0-9]*\/[0-9]*\) · .*/\1/p' <<<"$OUT")"
OUT="$(python3 "$TRANS" set next claimed --force --as engineer --board "$B" 2>"$ERR")"; RC=$?
has  "C3 the transition line: ▸ next: open → claimed · forced · done" "$OUT" "▸ next: open → claimed · forced · done "
lacks "C4 …never asked"                                       "$OUT" "asked"
OUT="$(cd "$D" && echo '{}' | bash "$STATUS" 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g')"
has  "C5 statusline.sh <<< '{}' renders ▸pearde <rd>/<rn>" "$OUT" "▸pearde $PD "
lacks "C6 …never asked"                                       "$OUT" "asked"
eq   "C7 no reader of the old key is left in resources/ references/ README.md" \
     "$(grep -rl -E '"asked"|<ad>|asked [0-9]+/[0-9]+' "$ROOT/resources" "$ROOT/references" "$ROOT/README.md" | wc -l | tr -d ' ')" "0"

# ── D. vision and example declare their flags ────────────────────────────────
echo "D. vision and example declare their flags"
D="$(fixture d)"; B="$D/prds"
OUT="$(python3 "$PEARDE" vision --bogus --board "$B" 2>"$ERR")"; RC=$?
eq   "D1 pearde vision --bogus → exit 2"                      "$RC" "2"
has  "D2 …names the flag and the list"                        "$(cat "$ERR")" "pearde vision: unknown flag --bogus — vision takes: --board, --json, --next, --check"
OUT="$(python3 "$PEARDE" vision --help 2>&1)"
has  "D3 vision --help prints the same list"                  "$OUT" "takes: --board, --json, --next, --check"
OUT="$(python3 "$PEARDE" vision --check --board "$B" 2>&1)"; RC=$?
eq   "D4 vision --check --board still runs"                   "$RC" "0"
OUT2="$(python3 "$PLAN" vision --check "$B" 2>&1)"
eq   "D5 …the same line plan.py vision --check <board> prints" "$OUT" "$OUT2"
OUT="$(python3 "$PEARDE" vision "$B" --check 2>&1)"; RC=$?
eq   "D6 the positional board still works"                    "$OUT" "$OUT2"
OUT="$(python3 "$PEARDE" vision --board 2>"$ERR")"; RC=$?
eq   "D7 --board with no value → exit 2"                      "$RC" "2"
has  "D8 …says it takes a value"                              "$(cat "$ERR")" "--board takes a value"
OUT="$(python3 "$PEARDE" example --bogus 2>"$ERR")"; RC=$?
eq   "D9 pearde example --bogus → exit 2"                     "$RC" "2"
has  "D10 …names the flag, and that it takes none"            "$(cat "$ERR")" "pearde example: unknown flag --bogus — example takes: no flags"
OUT="$(python3 "$PEARDE" example --help 2>&1)"
has  "D11 example --help prints no flags"                     "$OUT" "takes: no flags"
OUT="$(python3 "$PEARDE" example 2>"$ERR")"; RC=$?
eq   "D12 example with no dir → usage, exit 2"                "$RC" "2"
OUT="$(python3 "$PEARDE" example "$TOP/e" 2>"$ERR")"; RC=$?
eq   "D13 example <dir> still copies"                         "$RC" "0"
eq   "D14 …a board is there"                                  "$(test -f "$TOP/e/prds/settings.md" && echo yes)" "yes"
OUT="$(python3 "$PEARDE" set --bogus x open --board "$B" 2>"$ERR")"; RC=$?
eq   "D15 a transition's own refusal is unchanged (Flags moved, not changed)" "$RC" "2"
has  "D16 …set takes: --as, --board, --worker, --force, --dry" "$(cat "$ERR")" "set takes: --as, --board, --worker, --force, --dry"

# ── E. collect commits through a private index ───────────────────────────────
# The checkout's index is every session's. A sibling's staged hunk in a file
# outside the footprint must not ride the landing, must still be staged
# afterwards, and a sibling's next plain commit must not revert the landing.
echo "E. collect commits through a private index"
D="$(fixture e)"; B="$D/prds"
echo "other" > "$D/other.txt"; ( cd "$D" && git add other.txt && git commit -qm other )
echo "sibling line" >> "$D/README.md"; ( cd "$D" && git add README.md )
echo "unstaged elsewhere" >> "$D/other.txt"
eq   "E1 a sibling's hunk is staged before collect"        "$(cd "$D" && git diff --cached --name-only)" "README.md"
H0="$(cd "$D" && git rev-parse HEAD)"
OUT="$(cd "$D" && python3 "$COLLECT" finished --as engineer --trust --board "$B" 2>"$ERR")"; RC=$?
eq   "E2 collect finished lands, exit 0"                    "$RC" "0"
eq   "E3 …two commits on top: the landing, the record"      "$(cd "$D" && git rev-list --count "$H0"..HEAD)" "2"
lacks "E4 the landing does not carry README.md"             "$(cd "$D" && git show --name-only --format= HEAD~1)" "README.md"
has  "E5 …it carries the PRD's record"                      "$(cd "$D" && git show --name-only --format= HEAD~1)" "prds/finished/prd.md"
lacks "E6 the record commit carries nothing foreign"        "$(cd "$D" && git show --name-only --format= HEAD)" "README.md"
eq   "E7 the sibling's hunk is still staged after collect"  "$(cd "$D" && git diff --cached --name-only)" "README.md"
eq   "E8 the PRD folder reads clean in the shared index"    "$(cd "$D" && git status --porcelain -- prds/finished)" ""
eq   "E9 the unstaged foreign edit is untouched"            "$(cd "$D" && git status --porcelain -- other.txt)" " M other.txt"
has  "E10 state: done in HEAD"                              "$(cd "$D" && git show HEAD:prds/finished/prd.md)" "state: done"
has  "E11 the line carries commit and record"               "$OUT" "· record "
( cd "$D" && git commit -q -m sibling )
eq   "E12 the sibling's next plain commit carries only its file" "$(cd "$D" && git show --name-only --format= HEAD)" "README.md"
has  "E13 …and does not revert the landing"                 "$(cd "$D" && git show HEAD:prds/finished/prd.md)" "state: done"
eq   "E14 no scratch index is left behind"                  "$(ls -d /tmp/pearde-index-* "${TMPDIR:-/tmp}"/pearde-index-* 2>/dev/null | wc -l | tr -d ' ')" "0"
# HEAD moved between read-tree and update-ref: refused, nothing written
D="$(fixture e2)"
OUT="$(cd "$D" && python3 - "$D" "$COLLECT" <<'PY' 2>&1
import sys, os, subprocess, importlib.util
root, path = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.dirname(path))
spec = importlib.util.spec_from_file_location("collect", path); c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
open(os.path.join(root, "mine.txt"), "w").write("mine\n")
with c.private_index([root]):
    c.git_out(root, "add", "--", "mine.txt")
    open(os.path.join(root, "theirs.txt"), "w").write("theirs\n")
    subprocess.run(["git", "-C", root, "add", "theirs.txt"], check=True)
    subprocess.run(["git", "-C", root, "commit", "-q", "-m", "sibling"], check=True)
    try:
        c.commit_private(root, "mine\n"); print("landed")
    except c.Stop as e:
        print("stop:", e)
PY
)"
has  "E15 a HEAD moved under the build is refused"          "$OUT" "stop: HEAD moved under collect"
eq   "E16 …the sibling's commit is HEAD, nothing on top"    "$(cd "$D" && git log -1 --format=%s)" "sibling"
eq   "E17 …mine.txt is not in HEAD"                         "$(cd "$D" && git ls-tree --name-only HEAD mine.txt)" ""

# ── F. the collect harnesses stop only the daemon they started ───────────────
echo "F. the collect harnesses stop only the daemon they started"
KEEPS="$ROOT/prds/the-tool-keeps-its-word/collect-keeps-its-word/probe/verify.sh"
ISA="$ROOT/prds/the-board-runs-itself/collect-is-a-command/probe/verify.sh"
for h in "$KEEPS" "$ISA"; do
  n="$(basename "$(dirname "$(dirname "$h")")")"
  eq "F1 $n: every serve.py stop names its port inline" "$(grep -c 'serve\.py" stop' "$h")" "$(grep -c 'PEARDE_PORT="\$SPARE" python3 "\$SRV/board/serve\.py" stop' "$h")"
  eq "F2 $n: 8443 is never written"                     "$(grep -c '8443' "$h")" "0"
done
# a sentinel daemon — a copy of the scripts, its own registry — on a spare
# port stands in for the live one; the harness runs; the sentinel survives
SRV="$SCRATCH/sentinel/resources"; mkdir -p "$SRV/board"
cp "$ROOT"/resources/*.py "$SRV/"; cp "$ROOT"/resources/board/*.py "$ROOT"/resources/board/*.css "$ROOT"/resources/board/*.js "$SRV/board/"
SENT="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')"
D="$(fixture f)"
( cd "$D" && PEARDE_PORT="$SENT" python3 "$SRV/board/serve.py" ensure "$D/prds" >/dev/null 2>&1 )
has  "F3 the sentinel daemon is up on its port"             "$(PEARDE_PORT="$SENT" python3 "$SRV/board/serve.py" status 2>&1)" "serve: up"
( env -u PEARDE_PORT PEARDE_AS=engineer bash "$ISA" </dev/null >"$SCRATCH/isa.out" 2>&1 )
has  "F4 collect-is-a-command ran its daemon section"       "$(cat "$SCRATCH/isa.out")" "R the daemon came up on the spare port"
has  "F5 …the sentinel is still up afterwards"              "$(PEARDE_PORT="$SENT" python3 "$SRV/board/serve.py" status 2>&1)" "serve: up"
PEARDE_PORT="$SENT" python3 "$SRV/board/serve.py" stop >/dev/null 2>&1
export PEARDE_PORT=1

# ── G. statusline.sh weights by complexity, the weight scan uses ─────────────
echo "G. statusline.sh weights by complexity"
D="$(fixture g)"; B="$D/prds"
sl() { ( cd "$1" && echo '{}' | bash "$STATUS" 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | sed -n 's/^▸pearde \([0-9]*\/[0-9]* [0-9]*%\).*/\1/p' ); }
sc() { python3 "$PLAN" scan "$1/prds" 2>/dev/null | sed -n 's/^progress: done \([0-9]*\/[0-9]*\) · \([0-9]*\)%.*/\1 \2%/p'; }
eq   "G1 the example: statusline and scan agree"           "$(sl "$D")" "$(sc "$D")"
sed -i '' 's/^complexity: .*/complexity: 40/' "$B/landed/prd.md"
eq   "G2 a done PRD re-weighted: both move, still agree"   "$(sl "$D")" "$(sc "$D")"
sed -i '' 's/^complexity: .*/est: 3h/' "$B/next/prd.md"
eq   "G3 est as the fallback of an unscored PRD: agree"    "$(sl "$D")" "$(sc "$D")"
for f in "$B"/*/prd.md "$B"/*/*/prd.md; do [ -f "$f" ] && sed -i '' '/^complexity: /d;/^est: /d' "$f"; done
rm -rf "$B"/*/specs
python3 - "$B/settings.md" <<'PY'
import sys; p=sys.argv[1]; t=open(p).read().replace("language: English", "language: English\nweight-default: 10", 1); open(p,"w").write(t)
PY
eq   "G4 nothing scored: weight-default is on the board"    "$(grep -c '^weight-default: 10' "$B/settings.md")" "1"
eq   "G5 …statusline and scan still agree"                 "$(sl "$D")" "$(sc "$D")"

echo
echo "verify: $((PASS+FAIL)) checks · $PASS pass · $FAIL fail"
[ "$FAIL" = 0 ]
