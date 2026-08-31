#!/usr/bin/env bash
# the-skill-tree-is-guarded — a round on another board cannot write the skill
# through the install. Every call is hook JSON on stdin; PEARDE_GUARD_STATE
# points at a temp dir, so nothing under resources/board/state/ is touched.
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd -P)"
GUARD="$ROOT/resources/guard.py"
D="$(mktemp -d)"; S="$(mktemp -d)"           # fixtures; scratch, outside them
trap 'rm -rf "$D" "$S"' EXIT
export PEARDE_GUARD_STATE="$S/state"
pass=0; fail=0
ok()  { if [ "$2" -eq 0 ]; then pass=$((pass+1)); echo "  ok   $1"; else fail=$((fail+1)); echo "  FAIL $1${3:+ — $3}"; fi; }
has() { case "$2" in *"$3"*) ok "$1" 0 ;; *) ok "$1" 1 "missing: $3" ;; esac; }
lacks() { case "$2" in *"$3"*) ok "$1" 1 "found: $3" ;; *) ok "$1" 0 ;; esac; }

# a project with its own board — the example's prds/, not the example root
mkdir -p "$D/proj"; cp -R "$ROOT/resources/board/example/prds" "$D/proj/prds"
# an install: the five links of references/install.md, built here
mkdir -p "$D/skills/pearde"
ln -s "$ROOT/skills/pearde.md" "$D/skills/pearde/SKILL.md"
ln -s "$ROOT/README.md"        "$D/skills/pearde/README.md"
ln -s "$ROOT/index.md"         "$D/skills/pearde/index.md"
ln -s "$ROOT/references"       "$D/skills/pearde/references"
ln -s "$ROOT/resources"        "$D/skills/pearde/resources"
mkdir -p "$D/nowhere"
LINK="$D/skills/pearde/README.md"
MEMO="prds/memos/the-install-is-live-symlinks.md"
SESS="skilltree$$"                            # a session id no other harness uses

hook() { # tool cwd file [session] → guard's stdout
  local tool="$1" cwd="$2" file="$3" sess="${4:-$SESS}" inp
  case "$tool" in
    Write) inp='{"file_path":"'"$file"'","content":"x"}' ;;
    Bash)  inp='{"command":"'"$file"'"}' ;;
    *)     inp='{"file_path":"'"$file"'","old_string":"zzz-absent","new_string":"b"}' ;;
  esac
  printf '{"tool_name":"%s","session_id":"%s","cwd":"%s","tool_input":%s}' \
    "$tool" "$sess" "$cwd" "$inp" | python3 "$GUARD" pre 2>"$S/err"
}

echo "— the refusal"
out=$(hook Edit "$D/proj" "$LINK")
has  "A1 an Edit through the link from another board is denied" "$out" '"permissionDecision": "deny"'
has  "A2 the deny names the real path the link resolves to" "$out" "$ROOT/README.md"
has  "A3 the deny names the path as given, resolving" "$out" "$LINK resolves to"
has  "A4 the deny names the memo" "$out" "$MEMO"
has  "A5 the deny names the session's board" "$out" "$D/proj/prds"
has  "A6 way out one: file a PRD on the skill's own board" "$out" 'file a PRD on the skill'
reason=$(printf '%s' "$out" | python3 -c 'import json,sys;print(json.load(sys.stdin)["hookSpecificOutput"]["permissionDecisionReason"])')
has  "A7 way out one is a command, run from the skill root" "$reason" "\`pearde add \"<title>\"\` from $ROOT)"
has  "A8 way out two: hand the edit to a session working it" "$out" 'hand the edit to a session working it'
printf '%s' "$out" | python3 -c 'import json,sys; d=json.load(sys.stdin)["hookSpecificOutput"]; assert d["hookEventName"]=="PreToolUse"' 2>/dev/null
ok   "A9 the deny is one PreToolUse JSON object" $?
out=$(hook Write "$D/proj" "$LINK")
has  "A10 a Write through the link is denied the same way" "$out" '"permissionDecision": "deny"'
out=$(hook Write "$D/proj" "$D/skills/pearde/references/parts/new-file.md")
has  "A11 a Write of a new file through the references link is denied — realpath resolves the link above it" "$out" "$ROOT/references/parts/new-file.md"
out=$(hook Edit "$D/proj" "$ROOT/references/parts/guard.md")
has  "A12 the real path by name, no link, is denied too — the leak is the write, not the link" "$out" '"permissionDecision": "deny"'
lacks "A13 a real path is named once, not 'resolves to' itself" "$out" 'resolves to'
out=$(hook Edit "$D/proj" "$D/skills/pearde/resources/guard.py")
has  "A14 resources/ through the link is skill tree" "$out" "$ROOT/resources/guard.py"
out=$(hook Edit "$D/proj" "$D/skills/pearde/SKILL.md")
has  "A15 skills/ through the SKILL.md link is skill tree" "$out" "$ROOT/skills/pearde.md"
out=$(hook Edit "$(cd "$D/proj" && pwd -P)" "$LINK")
has  "A16 the cwd given as its real path (/private/var on darwin) is still another board" "$out" '"permissionDecision": "deny"'
n=$(python3 -c "import json;d=json.load(open('$S/state/$SESS.json'))['boards'];print(sum(b['refused'] for b in d.values()))")
[ "$n" -ge 6 ]; ok "A17 each refusal is counted on the session's block (refused=$n)" $?
[ ! -e "$ROOT/resources/board/state/guard/$SESS.json" ]; ok "A18 nothing written under resources/board/state/ — PEARDE_GUARD_STATE moved it" $?

echo "— what passes"
out=$(hook Edit "$D/proj" "$D/proj/prds/asking/specs/spec01.md")
[ -z "$out" ]; ok "P1 an Edit under the project's own prds/ passes" $?
out=$(hook Write "$D/proj" "$D/proj/prds/asking/specs/spec09.md")
[ -z "$out" ]; ok "P2 a Write under the project's own prds/ passes" $?
out=$(hook Edit "$ROOT" "$LINK")
[ -z "$out" ]; ok "P3 the same Edit from a working directory in this repo passes" $?
out=$(hook Edit "$ROOT/prds/memos" "$LINK")
[ -z "$out" ]; ok "P4 a working directory inside this repo's board passes" $?
out=$(hook Edit "$D/nowhere" "$LINK")
[ -z "$out" ]; ok "P5 no board in scope passes — the guard refuses only a round provably another board's" $?
out=$(hook Edit "$D/nowhere" "$ROOT/references/parts/guard.md")
[ -z "$out" ]; ok "P6 no board in scope, the real path by name, passes" $?
out=$(hook Write "$D/proj" "$ROOT/prds/memos/from-elsewhere.md")
[ -z "$out" ]; ok "P7 a write under this repo's own prds/ from another board passes — filing here is the way in" $?
out=$(hook Read "$D/proj" "$LINK")
[ -z "$out" ]; ok "P8 a Read through the link is not this rule's business" $?
out=$(hook Edit "$D/proj" "$D/proj/prds/asking/prd.md")
[ -z "$out" ]; ok "P9 a body edit of the project's prd.md still passes (state_by_hand untouched)" $?
out=$(hook Bash "$D/proj" "echo x > $LINK")
lacks "B1 the Bash hook does not match a shell write through the link — the caveat guard.md states" "$out" '"deny"'

echo "— status and doctor"
# status is read on a copy the probe wires itself — a worktree of HEAD has no
# settings file, and the words are the rule's, not this checkout's
WIRED=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$D/proj")
python3 "$GUARD" on "$WIRED" >/dev/null 2>&1
out=$(python3 "$GUARD" status "$WIRED" 2>&1); rc=$?
has  "S1 guard status ok says skill tree guarded" "$out" 'skill tree guarded'
[ $rc -eq 0 ]; ok "S2 guard status exits 0" $?
has  "S3 guard status still names the settings file" "$out" "wired in $WIRED/.claude/settings.json"
grep -q 'does not refuse a write into the skill tree' "$GUARD"; ok "S4 status has a broken row for the second rule — the words are earned by a probe" $?
grep -q 'skill tree guarded' "$ROOT/resources/doctor.sh"; ok "S5 doctor.sh's ok row carries the two words" $?
[ "$(grep -c 'skill tree guarded' "$ROOT/resources/doctor.sh")" -eq 1 ]; ok "S6 doctor.sh moved one line" $?

echo "— the text"
G="$ROOT/references/parts/guard.md"; I="$ROOT/references/install.md"
grep -q '^| an `Edit` or `Write` whose `file_path` resolves — through any install link, or by name — to a file under this skill' "$G"; ok "T1 guard.md refusals table has the row" $?
grep -q 'file a PRD on the skill'"'"'s own board, or hand the edit to a session working it' "$G"; ok "T2 the row names the two ways out" $?
grep -q 'the-install-is-live-symlinks' "$G"; ok "T3 the row names the memo" $?
grep -q 'The skill-tree refusal matches `Edit` and `Write` only' "$G"; ok "T4 guard.md says the Bash hook does not match a shell write" $?
grep -q 'The links run the other way too' "$I"; ok "T5 install.md's link bullet says the guard refuses a write through them from another board" $?
grep -q 'the-install-is-live-symlinks' "$I"; ok "T6 install.md names the memo" $?
grep -q 'the skill written from another board' "$GUARD"; ok "T7 guard.py's docstring lists the rule beside the other four" $?

echo
echo "$((pass+fail)) checks · $pass pass · $fail fail"
[ "$fail" -eq 0 ]
