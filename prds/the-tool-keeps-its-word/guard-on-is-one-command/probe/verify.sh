#!/usr/bin/env bash
# guard-on-is-one-command — `pearde guard on|off|status` on temp repos only.
#
# Every fixture is a `mktemp -d` holding a copy of resources/board/example as
# its board and its own `git init`; the guard's state dir is a temp dir; the
# daemon port is dead (PEARDE_PORT=1) so nothing registers. This repo's own
# .claude/settings.json is never read for a write and never written.
set -u
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
P="python3 $ROOT/resources/pearde.py"
G="python3 $ROOT/resources/guard.py"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
export PEARDE_GUARD_STATE="$T/guardstate" PEARDE_PORT=1 PEARDE_AS=probe
SELF="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$ROOT/resources/guard.py")"
# this repo's own settings file, byte for byte, before any fixture runs — the
# guard may be wired here, so E compares bytes rather than asserting absence
OWN="$ROOT/.claude/settings.json"; SNAP="$T/settings.before"
{ cat "$OWN" 2>/dev/null || :; } > "$SNAP"

PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); }
bad() { FAIL=$((FAIL+1)); echo "FAIL: $1"; }
eq()  { [ "$2" = "$3" ] && ok || bad "$1 — got '$2', want '$3'"; }
has() { printf '%s' "$2" | grep -qF -- "$3" && ok || bad "$1 — missing '$3'"; }
not() { printf '%s' "$2" | grep -qF -- "$3" && bad "$1 — has '$3'" || ok; }
jq_() { python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(eval(sys.argv[2]))' "$1" "$2" 2>&1; }
repo() { local d="$T/$1"; mkdir -p "$d"; cp -R "$ROOT/resources/board/example/prds" "$d/prds"; ( cd "$d" && git init -q . ); echo "$d"; }
guardrow() { bash "$ROOT/resources/doctor.sh" "$1" 2>/dev/null | grep -E '^  guard ' ; }

# ── A. a repo with no .claude/ ───────────────────────────────────────────────
echo "── A. no .claude/: on, on again, status, off"
A="$(repo a)"; SA="$A/.claude/settings.json"
OUT="$($P guard on "$A" 2>&1)"; RC=$?
eq  "A on exits 0" "$RC" 0
eq  "A the file exists" "$( [ -f "$SA" ] && echo yes )" yes
has "A prints the file" "$OUT" "guard on: $SA"
eq  "A four + lines" "$(printf '%s\n' "$OUT" | grep -c '^  + ')" 4
has "A names the env key" "$OUT" '+ env.MAX_THINKING_TOKENS = "8000"'
has "A the one sentence" "$OUT" "read after /hooks or a restart"
eq  "A env key" "$(jq_ "$SA" 'd["env"]["MAX_THINKING_TOKENS"]')" 8000
eq  "A key order: env, hooks" "$(jq_ "$SA" '" ".join(d)')" "env hooks"
eq  "A PreToolUse matchers" "$(jq_ "$SA" '" ".join(e["matcher"] for e in d["hooks"]["PreToolUse"])')" "Bash|Read Edit|Write"
eq  "A PostToolUse matchers" "$(jq_ "$SA" '" ".join(e["matcher"] for e in d["hooks"]["PostToolUse"])')" "Edit|Write"
eq  "A the pre command names this guard.py" "$(jq_ "$SA" 'd["hooks"]["PreToolUse"][1]["hooks"][0]["command"]')" "python3 $SELF pre"
eq  "A the post command names this guard.py" "$(jq_ "$SA" 'd["hooks"]["PostToolUse"][0]["hooks"][0]["command"]')" "python3 $SELF post"
eq  "A hook type command" "$(jq_ "$SA" 'd["hooks"]["PreToolUse"][0]["hooks"][0]["type"]')" command
eq  "A indent 2, trailing newline" "$(python3 -c 'import json,sys; t=open(sys.argv[1]).read(); print(t==json.dumps(json.loads(t),indent=2,ensure_ascii=False)+"\n")' "$SA")" True
CMD="$(jq_ "$SA" 'd["hooks"]["PreToolUse"][0]["hooks"][0]["command"]')"
has "A the written command refuses a hand-walked board" "$(cd "$A" && echo '{"tool_name":"Bash","tool_input":{"command":"find prds -name prd.md"},"cwd":"'"$A"'"}' | sh -c "$CMD")" '"deny"'
ROW="$(guardrow "$A")"
has "A doctor reads guard ok" "$ROW" "  guard       ok      wired in $SA"
has "A ...with the cap" "$ROW" "MAX_THINKING_TOKENS=8000"
SUM="$(cksum < "$SA")"
OUT="$($P guard on "$A" 2>&1)"; RC=$?
eq  "A on again exits 0" "$RC" 0
has "A on again says so" "$OUT" "guard on: $SA — already wired, nothing changed"
eq  "A on again wrote nothing" "$(cksum < "$SA")" "$SUM"
OUT="$($P guard status "$A" 2>&1)"; RC=$?
eq  "A status exits 0" "$RC" 0
eq  "A status is doctor's row" "$OUT" "$ROW"
OUT="$($P guard off "$A" 2>&1)"; RC=$?
eq  "A off exits 0" "$RC" 0
has "A off prints the file" "$OUT" "guard off: $SA"
eq  "A three - lines" "$(printf '%s\n' "$OUT" | grep -c '^  - ')" 3
eq  "A off leaves an empty hooks block" "$(jq_ "$SA" 'd["hooks"]')" "{}"
eq  "A off leaves the env key" "$(jq_ "$SA" 'd["env"]["MAX_THINKING_TOKENS"]')" 8000
ROW="$(guardrow "$A")"
has "A doctor reads guard off" "$ROW" "  guard       off     not wired in $SA"
has "A doctor's fix line names the command" "$(bash "$ROOT/resources/doctor.sh" "$A" 2>/dev/null | grep -A1 '^  guard ' | tail -1)" "fix: pearde guard on"
OUT="$($P guard status "$A" 2>&1)"; RC=$?
eq  "A status exits 1 when off" "$RC" 1
eq  "A status is doctor's row when off" "$(printf '%s\n' "$OUT" | head -1)" "$ROW"
has "A status carries the fix line" "$OUT" "fix: pearde guard on"
OUT="$($P guard off "$A" 2>&1)"; RC=$?
eq  "A off again exits 0" "$RC" 0
has "A off again says so" "$OUT" "guard off: $SA — not wired, nothing changed"

# ── B. a settings file that already holds other hooks and keys ──────────────
echo "── B. other keys and hooks: on then off is byte-identical"
B="$(repo b)"; SB="$B/.claude/settings.json"; mkdir -p "$B/.claude"
python3 - "$SB" <<'PY'
import json, sys
d = {"permissions": {"allow": ["Bash(ls:*)"]},
     "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo mine"}]}],
               "PostToolUse": [{"matcher": "Edit|Write", "hooks": [{"type": "command", "command": "echo théirs"}]}]},
     "env": {"OTHER": "1"},
     "zzz": [1, 2]}
open(sys.argv[1], "w").write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
PY
SUM="$(cksum < "$SB")"
OUT="$($P guard on "$B" 2>&1)"; RC=$?
eq  "B on exits 0" "$RC" 0
eq  "B four + lines" "$(printf '%s\n' "$OUT" | grep -c '^  + ')" 4
eq  "B key order kept" "$(jq_ "$SB" '" ".join(d)')" "permissions hooks env zzz"
eq  "B the foreign PreToolUse entry stays first" "$(jq_ "$SB" '" ".join(e["matcher"] for e in d["hooks"]["PreToolUse"])')" "Bash Bash|Read Edit|Write"
eq  "B the foreign PostToolUse entry stays" "$(jq_ "$SB" '" ".join(e["matcher"] for e in d["hooks"]["PostToolUse"])')" "Edit|Write Edit|Write"
eq  "B the foreign hook is untouched" "$(jq_ "$SB" 'd["hooks"]["PostToolUse"][0]["hooks"][0]["command"]')" "echo théirs"
eq  "B env.OTHER stays, cap added" "$(jq_ "$SB" '" ".join(d["env"])')" "OTHER MAX_THINKING_TOKENS"
eq  "B zzz stays" "$(jq_ "$SB" 'd["zzz"]')" "[1, 2]"
has "B doctor reads guard ok" "$(guardrow "$B")" "ok      wired in $SB"
OUT="$($P guard off "$B" 2>&1)"; RC=$?
eq  "B off exits 0" "$RC" 0
eq  "B three - lines" "$(printf '%s\n' "$OUT" | grep -c '^  - ')" 3
not "B off never names the foreign hook" "$OUT" "echo"
eq  "B off leaves the cap" "$(jq_ "$SB" 'd["env"]["MAX_THINKING_TOKENS"]')" 8000
python3 - "$SB" <<'PY'
import json, sys
d = json.load(open(sys.argv[1])); del d["env"]["MAX_THINKING_TOKENS"]
open(sys.argv[1], "w").write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
PY
eq  "B on then off, cap dropped by hand: byte-identical" "$(cksum < "$SB")" "$SUM"

# ── C. a cap already set is not overwritten; a file that is not JSON is refused
echo "── C. a set cap stays; not-JSON is refused untouched"
C="$(repo c)"; SC="$C/.claude/settings.json"; mkdir -p "$C/.claude"
printf '{\n  "env": {\n    "MAX_THINKING_TOKENS": "4000"\n  }\n}\n' > "$SC"
OUT="$($P guard on "$C" 2>&1)"
eq  "C three + lines — the cap was set" "$(printf '%s\n' "$OUT" | grep -c '^  + ')" 3
eq  "C the cap is kept" "$(jq_ "$SC" 'd["env"]["MAX_THINKING_TOKENS"]')" 4000
has "C doctor reads the kept cap" "$(guardrow "$C")" "MAX_THINKING_TOKENS=4000"
printf '{ not json\n' > "$SC"; SUM="$(cksum < "$SC")"
ERR="$($P guard on "$C" 2>&1 >/dev/null)"; RC=$?
eq  "C not JSON: on exits 1" "$RC" 1
has "C not JSON: refused, named" "$ERR" "pearde guard on: refused — $SC is not JSON"
eq  "C not JSON: untouched" "$(cksum < "$SC")" "$SUM"
ERR="$($P guard off "$C" 2>&1 >/dev/null)"; RC=$?
eq  "C not JSON: off exits 1" "$RC" 1
eq  "C not JSON: still untouched" "$(cksum < "$SC")" "$SUM"

# ── D. the repo argument: default is the board above the cwd ────────────────
echo "── D. no <repo>: the board above the cwd, or a refusal"
D="$(repo d)"; SD="$(cd "$D" && pwd -P)/.claude/settings.json"   # os.getcwd() is the real path
IN="$(find "$D/prds" -mindepth 1 -maxdepth 1 -type d | head -1)"
OUT="$(cd "$IN" && $P guard on 2>&1)"; RC=$?
eq  "D from inside the board: exits 0" "$RC" 0
has "D ...writes the repo's file" "$OUT" "guard on: $SD"
OUT="$(cd "$IN" && $P guard 2>&1)"; RC=$?
has "D bare pearde guard is status" "$OUT" "  guard       ok      wired in $SD"
E="$T/nothing"; mkdir -p "$E"
ERR="$(cd "$E" && $P guard on 2>&1 >/dev/null)"; RC=$?
eq  "D outside every board: exits 1" "$RC" 1
has "D ...refused, naming the board" "$ERR" "pearde guard on: refused — no board above "
has "D ...and the fix" "$ERR" " — name the repo: pearde guard on <repo>"
eq  "D ...wrote nothing" "$( [ -e "$E/.claude" ] && echo yes || echo no )" no
ERR="$($P guard on "$T/absent" 2>&1 >/dev/null)"; RC=$?
eq  "D a path that is not a directory: exits 1" "$RC" 1
has "D ...says so" "$ERR" "is not a directory"

# ── E. the dispatcher, help, init's fourth line, the manual ─────────────────
echo "── E. help, init, the manual"
H="$($P help 2>&1)"
has "E help lists guard on" "$H" "pearde guard on [<repo>]"
has "E help lists guard off" "$H" "pearde guard off [<repo>]"
has "E help's bare guard line is status" "$(printf '%s\n' "$H" | grep -E '^  pearde guard +\[')" "doctor's guard row alone"
I="$T/i"; mkdir -p "$I"; ( cd "$I" && git init -q . )
OUT="$(python3 "$ROOT/resources/board/init.py" init "$I" 2>&1)"; RC=$?
eq  "E init exits 0" "$RC" 0
eq  "E init's fourth-from-last line is guard on" "$(printf '%s\n' "$OUT" | tail -4 | head -1)" "pearde guard on — optional, refuses the waste the loop's rules name"
eq  "E ...and the last three are unchanged" "$(printf '%s\n' "$OUT" | tail -2)" 'pearde add "<title>"
pearde'
has "E init's doctor row names the command" "$OUT" "fix: pearde guard on"
has "E guard.md names the command" "$(cat "$ROOT/references/parts/guard.md")" '`pearde guard on [<repo>]`'
has "E guard.md keeps the block" "$(cat "$ROOT/references/parts/guard.md")" '"matcher": "Edit|Write"'
has "E guard.md: off is the command" "$(cat "$ROOT/references/parts/guard.md")" '`pearde guard off`, or set `disableAllHooks`'
has "E install.md's guard bullet names the command" "$(cat "$ROOT/references/install.md")" '- `pearde guard on` in the repo the board lives in'
has "E doctor.sh's fix line names the command" "$(cat "$ROOT/resources/doctor.sh")" 'fix "pearde guard on — writes the block'
eq  "E this repo's settings file is byte for byte what it was before the probe" "$( { cat "$OWN" 2>/dev/null || :; } | cmp -s - "$SNAP" && echo same || echo changed)" same

echo
echo "$((PASS+FAIL)) checks · $PASS pass · $FAIL fail"
[ "$FAIL" = 0 ]
