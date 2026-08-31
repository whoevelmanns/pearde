#!/usr/bin/env bash
# an-unknown-flag-refuses — a state-moving command with a flag it does not
# know writes nothing, and `--dry` is real on every one of them.
#
# Every fixture is a copy of resources/board/example/prds under its own
# `mktemp -d` with its own git repo; every command carries `--board <copy>`
# and runs from a cwd with no prds/ above it; PEARDE_PORT=1 so nothing here
# can reach a live daemon. Nothing touches the real board.
set -u
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
PEARDE="$ROOT/resources/pearde.py"
export PEARDE_AS=engineer
export PEARDE_PORT=1
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
cd "$W"

pass=0; fail=0
ok()   { if [ "$2" = 0 ]; then pass=$((pass+1)); echo "  ok   $1"; else fail=$((fail+1)); echo "  FAIL $1"; [ -n "${3:-}" ] && echo "       $3"; fi; }
has()  { grep -qF -- "$3" <<<"$2"; ok "$1" $? "$2"; }
eq()   { [ "$2" = "$3" ]; ok "$1" $? "got: $2 · want: $3"; }
t()    { eval "$2"; ok "$1" $? "${3:-}"; }

fixture() {                       # a board copy in its own repo; echoes it
  local d; d="$(mktemp -d)"
  cp -R "$ROOT/resources/board/example/prds" "$d/prds"
  ( cd "$d" && git init -q -b main && git add -A \
    && git -c user.name=t -c user.email=t@t commit -qm base )
  echo "$d"
}
run()   { python3 "$PEARDE" "$@" --board "$D/prds" 2>"$W/err"; }
err()   { cat "$W/err"; }
clean() { ( cd "$D" && git status --porcelain ); }
fm()    { grep -m1 "^$2:" "$D/prds/$1/prd.md" | sed "s/^$2: *//"; }
rows()  { [ -f "$D/prds/.transitions.jsonl" ] && wc -l <"$D/prds/.transitions.jsonl" | tr -d ' ' || echo 0; }
commit(){ ( cd "$D" && git add -A && git -c user.name=t -c user.email=t@t commit -qm "$1" ); }

# ── A. the incident: deferred → open on a flag the verb does not know ───────
echo "A. the incident"
D="$(fixture)"
run defer big/second >/dev/null
eq  "A a real defer parks big/second" "$(fm big/second state)" "deferred"
commit parked
OUT="$(run release big/second open --dyr)"; RC=$?
eq  "A release --dyr exits 2" "$RC" "2"
has "A …names the flag and the list" "$(err)" "unknown flag --dyr — release takes: --as, --board, --dry"
eq  "A …state unchanged" "$(fm big/second state)" "deferred"
eq  "A …git status clean" "$(clean)" ""
eq  "A …no transition row" "$(rows)" "1"
OUT="$(run release big/second open --dry)"; RC=$?
eq  "A release --dry exits 0" "$RC" "0"
has "A …prints dry · and the line" "$OUT" "dry · ▸ big/second: deferred → open ·"
has "A …and the paths" "$OUT" "would write: prds/big/second/prd.md · prds/.transitions.jsonl"
eq  "A …state unchanged" "$(fm big/second state)" "deferred"
eq  "A …git status clean" "$(clean)" ""
DRY="$(sed -n 's/^dry · //p' <<<"$OUT")"
REAL="$(run release big/second open)"
eq  "A the real run prints the line the dry run said" "$REAL" "$DRY"
eq  "A …and moved it" "$(fm big/second state)" "open"
eq  "A …one row" "$(rows)" "2"

# ── B. the refusal is before any read of the board ──────────────────────────
echo "B. before any read"
OUT="$(python3 "$PEARDE" release big/second open --dyr --board "$W/no-such-board" 2>"$W/err")"; RC=$?
eq  "B a board that does not exist is never looked at: exit 2" "$RC" "2"
has "B …the message is the flag's" "$(err)" "unknown flag --dyr"
OUT="$(env -u PEARDE_AS python3 "$PEARDE" release big/second open --dyr --board "$D/prds" 2>"$W/err")"; RC=$?
eq  "B no persona either: the flag is refused first" "$RC" "2"
has "B …" "$(err)" "unknown flag --dyr"
OUT="$(run set big/second open --worker --board "$D/prds" 2>"$W/err")"; RC=$?
eq  "B a valued flag does not eat the next flag: exit 2" "$RC" "2"
has "B …says which" "$(err)" "--worker takes a value — set takes:"
OUT="$(run claim big/second --as 2>"$W/err")"; RC=$?
eq  "B --as with no value: exit 2" "$RC" "2"
has "B …" "$(err)" "--as takes a value"

# ── C. every verb: --dyr refuses with its list, --help prints the same ──────
echo "C. every verb"
D="$(fixture)"
check_verb() {                     # <cmd> <args…> — refusal list == help list
  local cmd="$1"; shift
  local out; out="$(run "$cmd" "$@" --dyr </dev/null)"; local rc=$?
  eq  "C $cmd --dyr exits 2" "$rc" "2"
  local said; said="$(sed -n 's/.*unknown flag --dyr — '"$cmd"' takes: //p' "$W/err")"
  t   "C …names the list" "[ -n \"$said\" ]" "$(err)"
  local help; help="$(python3 "$PEARDE" "$cmd" --help | sed -n 's/^  takes: //p')"
  eq  "C …--help lists the same flags" "$help" "$said"
  has "C …--dry is on the list" "$said" "--dry"
  eq  "C …git status clean" "$(clean)" ""
}
check_verb add "T"
check_verb claim next w1
check_verb release next open
check_verb answer asking Q1 "t"
check_verb defer next
check_verb retry next
check_verb unblock next
check_verb set next open
check_verb sweep
check_verb specced building
check_verb refine next
check_verb collect finished
check_verb settings workers=4
OUT="$(run brief next --dyr)"; RC=$?
eq  "C brief --dyr exits 2" "$RC" "2"
has "C …brief's list has no --dry: it writes nothing" "$(err)" "brief takes: --as, --board, --role, --consult, --question, --transcript, --force, --check"
OUT="$(python3 "$PEARDE" init "$W/newboard" --dyr 2>"$W/err")"; RC=$?
eq  "C init --dyr exits 2" "$RC" "2"
has "C …init's list" "$(err)" "init takes: --language, --name, --example, --dry"
t   "C …and made no board" "[ ! -e \"$W/newboard\" ]"
eq  "C no transition row on the copy" "$(rows)" "0"

# ── D. --dry on every writer: the line, the paths, nothing written; then the
#       real run makes the change the dry line said ────────────────────────
echo "D. dry, then real"
dry_then_real() {                  # <label> <prd> <cmd> <args…>
  local label="$1" prd="$2"; shift 2
  local out; out="$(run "$@" --dry)"; local rc=$?
  eq  "D $label --dry exits 0" "$rc" "0"
  has "D …prints dry ·" "$out" "dry · "
  has "D …names prd.md" "$out" "would write: "
  eq  "D …git status clean" "$(clean)" ""
  local dry; dry="$(sed -n 's/^dry · //p' <<<"$out" | tail -1)"
  local real; real="$(run "$@" | tail -1)"
  eq  "D …the real run prints the line the dry run said" "$real" "$dry"
  t   "D …and the real run wrote" "[ -n \"$(clean)\" ]"
  commit "$label"
}
S=big/second
dry_then_real "claim" $S claim $S w1
eq  "D …claim written" "$(fm $S claim | cut -d' ' -f1)" "w1"
dry_then_real "release" $S release $S open
eq  "D …state open" "$(fm $S state)" "open"
dry_then_real "defer" $S defer $S
eq  "D …state deferred" "$(fm $S state)" "deferred"
dry_then_real "release (the way back)" $S release $S open
OUT="$(run set $S failed --force --dry)"
has "D set --force --dry says forced" "$OUT" "dry · ▸ $S: open → failed · forced ·"
eq  "D …and wrote nothing" "$(fm $S state)" "open"
dry_then_real "set --force" $S set $S failed --force
eq  "D …state failed" "$(fm $S state)" "failed"
dry_then_real "retry" $S retry $S
eq  "D …state open" "$(fm $S state)" "open"
OUT="$(run claim $S w1 --dry)"
has "D claim --dry names the baseline dir" "$OUT" "prds/.claims/$S/"
eq  "D …and wrote nothing" "$(clean)" ""
# unblock: big/second needs landed (done), parked at blocked
python3 - "$D/prds/$S/prd.md" <<'PY2'
import sys; p=sys.argv[1]; s=open(p).read().replace("\nstate:", "\nneeds: landed\nstate:", 1); open(p,"w").write(s)
PY2
run set $S blocked --force >/dev/null
commit blocked
dry_then_real "unblock" $S unblock $S
eq  "D …state specced" "$(fm $S state)" "specced"
# answer: asking holds Q1 alone → the last answer moves it
OUT="$(run answer asking Q1 "in memory" --dry)"; RC=$?
eq  "D answer --dry exits 0" "$RC" "0"
has "D …the last answer's line is the transition" "$OUT" "dry · ▸ asking: question → open ·"
has "D …names prd.md, the riders file and the row" "$OUT" "would write: prds/asking/prd.md · prds/.claims/riders · prds/.transitions.jsonl"
eq  "D …wrote nothing" "$(clean)" ""
DRY="$(sed -n 's/^dry · //p' <<<"$OUT")"
REAL="$(run answer asking Q1 "in memory" | tail -1)"
eq  "D …the real answer prints the line the dry run said" "$REAL" "$DRY"
eq  "D …state open" "$(fm asking state)" "open"
commit answered
# add
OUT="$(run add "Dry test" --dry)"; RC=$?
eq  "D add --dry exits 0" "$RC" "0"
has "D …counts the new PRD on the line" "$OUT" "dry · ▸ dry-test: — → open ·"
has "D …names the new file" "$OUT" "would write: prds/dry-test/prd.md · prds/.transitions.jsonl"
t   "D …and made no directory" "[ ! -e \"$D/prds/dry-test\" ]"
DRY="$(sed -n 's/^dry · //p' <<<"$OUT")"
REAL="$(run add "Dry test" | tail -1)"
eq  "D …the real add prints the line the dry run said" "$REAL" "$DRY"
commit added
# specced: building carries a spec; analyzing is where specced is set from
run set building analyzing --force >/dev/null
commit analyzing
OUT="$(run specced building --blast mid --dry)"; RC=$?
eq  "D specced --dry exits 0" "$RC" "0"
has "D …the line" "$OUT" "dry · ▸ building: analyzing → specced ·"
has "D …the paths" "$OUT" "would write: prds/building/prd.md · prds/.transitions.jsonl"
eq  "D …complexity untouched" "$(fm building complexity)" "$(git -C "$D" show HEAD:prds/building/prd.md | grep -m1 '^complexity:' | sed 's/^complexity: *//')"
eq  "D …git status clean" "$(clean)" ""
DRY="$(sed -n 's/^dry · //p' <<<"$OUT")"
REAL="$(run specced building --blast mid | tail -1)"
eq  "D …the real specced prints the line the dry run said" "$REAL" "$DRY"
eq  "D …blast-radius written" "$(fm building blast-radius)" "mid"
commit specced
OUT="$(run specced building --check --dry)"; RC=$?
eq  "D specced --check --dry: the gate alone, nothing written, exit 0" "$RC" "0"
# refine: big/second → analyzing, then two children from a table
run set big/second analyzing --force >/dev/null
commit analyzing2
TABLE=$'## Split\n\n| child | contract | needs |\n|---|---|---|\n| alpha | the first half | — |\n| beta | the second half | alpha |\n'
OUT="$(run refine big/second --dry <<<"$TABLE")"; RC=$?
eq  "D refine --dry exits 0" "$RC" "0"
has "D …each child" "$OUT" "dry · big/second/beta: open · needs alpha"
has "D …the parent's line counts the children" "$OUT" "dry · ▸ big/second: analyzing → open ·"
has "D …the paths" "$OUT" "would write: prds/big/second/alpha/prd.md · prds/big/second/beta/prd.md · prds/big/second/prd.md · prds/.transitions.jsonl"
t   "D …no child on disk" "[ ! -e \"$D/prds/big/second/alpha\" ]"
eq  "D …git status clean" "$(clean)" ""
DRY="$(sed -n 's/^dry · ▸/▸/p' <<<"$OUT")"
REAL="$(run refine big/second <<<"$TABLE" | tail -1)"
eq  "D …the real refine prints the line the dry run said" "$REAL" "$DRY"
t   "D …children on disk" "[ -f \"$D/prds/big/second/beta/prd.md\" ]"
# sweep --apply: a claim silent past claim-ttl
D="$(fixture)"
run claim big/second w1 >/dev/null
eq  "D a claim to sweep" "$(fm big/second state)" "analyzing"
python3 - "$D/prds/big/second" <<'PY'
import os, sys, time
t = time.time() - 4 * 3600
for r, _, fs in os.walk(sys.argv[1]):
    for f in fs:
        os.utime(os.path.join(r, f), (t, t))
os.utime(sys.argv[1], (t, t))
PY
commit claimed
OUT="$(run sweep --apply --dry)"; RC=$?
eq  "D sweep --apply --dry exits 0" "$RC" "0"
has "D …lists the silent claim" "$OUT" "big/second · analyzing · claim w1"
has "D …and the line --apply would print" "$OUT" "dry · ▸ big/second: analyzing → open ·"
eq  "D …wrote nothing" "$(clean)" ""
DRY="$(sed -n 's/^dry · //p' <<<"$OUT")"
REAL="$(run sweep --apply | tail -1)"
eq  "D …the real sweep prints the line the dry run said" "$REAL" "$DRY"
# settings
D="$(fixture)"
OUT="$(run settings workers=4 --dry)"; RC=$?
eq  "D settings --dry exits 0" "$RC" "0"
has "D …the line" "$OUT" "dry · settings: workers 1 → 4"
has "D …the path" "$OUT" "would write: prds/settings.md"
eq  "D …workers untouched" "$(grep -m1 '^workers:' "$D/prds/settings.md")" "workers: 1"
REAL="$(run settings workers=4)"
eq  "D …the real run says the line" "$REAL" "settings: workers 1 → 4"
commit settings
# collect: the model — keeps its own dry lines and gains the dry · line
OUT="$(run collect finished --trust --dry)"; RC=$?
eq  "D collect --dry exits 0" "$RC" "0"
has "D …keeps 'dry — nothing written'" "$OUT" "finished: dry — nothing written"
has "D …and prints the dry · line" "$OUT" "dry · ▸ finished: claimed → done ·"
has "D …round file owed on it" "$OUT" "· round file owed · as engineer"
has "D …the paths" "$OUT" "would write: prds/finished/prd.md · prds/.transitions.jsonl"
eq  "D …git status clean" "$(clean)" ""
eq  "D …state claimed" "$(fm finished state)" "claimed"
# init
OUT="$(python3 "$PEARDE" init "$W/nb" --name nb --dry 2>"$W/err")"; RC=$?
eq  "D init --dry exits 0" "$RC" "0"
has "D …the first line" "$OUT" "dry · board nb · language English — pearde settings language=<l> changes it"
has "D …the paths" "$OUT" "would write: $W/nb/prds/settings.md · $W/nb/prds/vision.md"
t   "D …and no board" "[ ! -e \"$W/nb\" ]"
t   "D …no daemon line, no doctor" "! grep -q 'doctor\|http' <<<\"\$OUT\""

# ── E. the real board was never touched ─────────────────────────────────────
echo "E. the real board"
t   "E no fixture prd.md under prds/" "[ -z \"$(find "$ROOT/prds" -name prd.md -path '*dry-test*' -o -name prd.md -path '*/alpha/*')\" ]"

echo
echo "verify: $((pass+fail)) checks · $pass pass · $fail fail"
[ "$fail" = 0 ]
