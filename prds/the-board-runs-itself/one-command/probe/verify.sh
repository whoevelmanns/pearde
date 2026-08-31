#!/bin/bash
# one-command probe — the dispatcher against a fixture root in a temp dir.
#
#   bash prds/the-board-runs-itself/one-command/probe/verify.sh
#
# The fixture root mirrors the install: resources/*.py and *.sh are links to
# the real scripts, resources/board/ links the committed board scripts, and
# the probe's pearde.py is copied to resources/pearde.py — the path it lands
# on. Two fixture modules under resources/board/ exercise discovery and the
# clash. The board is one PRD. Nothing here touches the live daemon: `view`
# is only asked for --help.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
D="$(mktemp -d)"; D="$(cd "$D" && pwd -P)"; trap 'rm -rf "$D"' EXIT
R="$D/root"
PASS=0; FAIL=0
ok()   { PASS=$((PASS + 1)); echo "ok   $PASS — $1"; }
fail() { FAIL=$((FAIL + 1)); echo "FAIL — $1"; }
check() { if eval "$2"; then ok "$1"; else fail "$1"; fi; }

# ── fixture ───────────────────────────────────────────────────────────────────
mkdir -p "$R/resources/board" "$R/references/templates" "$R/prds/memos" "$R/prds/alpha"
for f in "$REPO"/resources/*.py "$REPO"/resources/*.sh; do ln -s "$f" "$R/resources/"; done
for f in plan.py serve.py render.py edit.py; do ln -s "$REPO/resources/board/$f" "$R/resources/board/$f"; done
ln -s "$REPO/references/templates/memo.md" "$R/references/templates/memo.md"
rm -f "$R/resources/pearde.py"; cp "$REPO/resources/pearde.py" "$R/resources/pearde.py"  # the link loop above already made a link; the copy is the point
P="python3 $R/resources/pearde.py"
cat > "$R/prds/settings.md" <<'EOF'
---
language: English
---
EOF
cat > "$R/prds/alpha/prd.md" <<'EOF'
---
state: open
origin: requested
priority: 50
complexity: 0
---

# alpha — the one PRD on the fixture board
EOF
cat > "$R/prds/memos/bad.md" <<'EOF'
---
memo: bad
kind: decision
status: decided
date: 2026-08-28
---

# bad — a memo missing its subject
EOF
cat > "$R/resources/board/hello.py" <<'EOF'
"""hello — a fixture module a child would add."""
def cmd_hello(args):
    """say hello — the fixture command"""
    print("hello", *args)
    return 7 if args == ["--rc"] else 0
COMMANDS = {"hello": cmd_hello, "collect": cmd_hello}
EOF

# ── help ──────────────────────────────────────────────────────────────────────
cd "$R"
H="$($P help)"; RC=$?
check "help exits 0" '[ "$RC" = 0 ]'
check "help lists every name once" '[ "$(printf "%s\n" "$H" | grep -c "^  pearde")" = "$(printf "%s\n" "$H" | grep "^  pearde" | sort -u | wc -l | tr -d " ")" ]'
check "help: no line over 80 characters" 'python3 -c "import sys; sys.exit(max(len(l) for l in sys.stdin.read().splitlines()) > 80)" <<< "$H"'
check "help reads plan.py's docstring for reconcile" 'grep -q "pearde reconcile \[board\] *re-order the schedule, keep the anchor" <<< "$H"'
check "help reads doctor.sh's comment block" 'grep -q "pearde doctor --fix \[board\] *report, then repair" <<< "$H"'
check "help reads install.sh's three modes" '[ "$(grep -c "^  pearde install" <<< "$H")" = 3 ]'
check "help reads a discovered module's docstring" 'grep -q "pearde hello *say hello — the fixture command" <<< "$H"'
check "RESERVED is empty — every name a child was to deliver has landed" 'python3 -c "import sys; sys.path.insert(0, \"$R/resources\"); import pearde; sys.exit(pearde.RESERVED != {})"'
check "help: a claimed reserved name is no longer pending" '! grep -q "pearde collect *not yet" <<< "$H"'
for c in scan plan reconcile gantt calibrate status members view memo workflow questions index doctor install hello; do
  check "$c --help exits 0" "$P $c --help >/dev/null 2>&1"
done
check "--help never runs the command (doctor --help prints one line per mode, no report)" '[ "$($P doctor --help | wc -l | tr -d " ")" = "$(grep -cE "^#   doctor\.sh " "$R/resources/doctor.sh")" ]'

# ── the default and the board ─────────────────────────────────────────────────
$P > "$D/a.txt" 2>&1; RA=$?
$P scan > "$D/b.txt" 2>&1; RB=$?
check "pearde and pearde scan exit 0" '[ "$RA" = 0 ] && [ "$RB" = 0 ]'
check "pearde and pearde scan are byte-identical" 'cmp -s "$D/a.txt" "$D/b.txt"'
(cd "$R/prds/alpha" && $P scan > "$D/c.txt" 2>&1)
check "the board is found walking up from a subdirectory" 'cmp -s "$D/a.txt" "$D/c.txt"'
$P scan "$R" > "$D/d.txt" 2>&1
check "the board is found from the path given" 'cmp -s "$D/a.txt" "$D/d.txt"'
E="$(cd "$D" && $P 2>&1)"; RC=$?
check "no board: exit 2 and the script's own message" '[ "$RC" = 2 ] && grep -q "no prds/ board found" <<< "$E"'
check "status forwards with its verb in front" '$P status | grep -q "^board: .* · 1 PRDs"'
check "questions defaults to check: silent, exit 0" '[ -z "$($P questions 2>&1)" ]'
check "questions list is forwarded as its own verb" '$P questions list >/dev/null 2>&1'

# ── discovery ─────────────────────────────────────────────────────────────────
check "a discovered command runs with its arguments" '[ "$($P hello a b)" = "hello a b" ]'
check "a discovered command's exit code passes through" '$P hello --rc >/dev/null; [ $? = 7 ]'
check "a module claims a reserved name and it routes there" '[ "$($P collect)" = "hello" ]'
check "help prints no not yet line — RESERVED is empty" '! grep -q "not yet" <<< "$H"'
E="$($P colect 2>&1)"; RC=$?
check "an unknown name exits 2 and names the near miss" '[ "$RC" = 2 ] && grep -q "did you mean collect" <<< "$E"'

# ── memo ──────────────────────────────────────────────────────────────────────
E="$($P memo check 2>&1)"; RC=$?
check "memo check forwards and its exit code passes through" '[ "$RC" = 1 ] && grep -q "bad.md: missing .subject:." <<< "$E"'
OUT="$($P memo add "Dates Are Written, not stamped")"; RC=$?
check "memo add prints the path and exits 0" '[ "$RC" = 0 ] && [ "$OUT" = "$R/prds/memos/dates-are-written-not-stamped.md" ]'
check "memo add: the slug is the memo: key" 'grep -q "^memo: dates-are-written-not-stamped$" "$OUT"'
check "memo add: the subject is kept as written" 'grep -q "^subject: Dates Are Written, not stamped$" "$OUT"'
check "memo add: the date is today, ISO" 'grep -q "^date: $(date +%Y-%m-%d)$" "$OUT"'
check "memo add: the new memo passes memo check (only bad.md is reported)" '[ "$($P memo check 2>&1 | wc -l | tr -d " ")" = 1 ]'
check "memo add refuses to overwrite" '! $P memo add "dates are written not stamped" >/dev/null 2>&1'
mkdir -p "$D/ext/prds" "$D/ext/records"
printf -- "---\nlanguage: English\nmemos: ../records\n---\n" > "$D/ext/prds/settings.md"
check "memo add refuses an external memos: dir" '(cd "$D/ext" && ! $P memo add "x" >/dev/null 2>&1 && [ -z "$(ls "$D/ext/records")" ])'

# ── clash ─────────────────────────────────────────────────────────────────────
cat > "$R/resources/board/other.py" <<'EOF'
def cmd(args):
    """other"""
    return 0
COMMANDS = {"hello": cmd, "scan": cmd}
EOF
E="$($P help 2>&1)"; RC=$?
check "two modules on one name: help exits 1" '[ "$RC" = 1 ]'
check "two modules on one name: help names both" 'grep -q "\`hello\` is claimed by both hello.py and other.py" <<< "$E"'
check "a module on a forwarded name is refused" 'grep -q "\`scan\` is forwarded by pearde.py and claimed by other.py" <<< "$E"'
check "the first claimant still runs" '[ "$($P hello 2>/dev/null)" = "hello" ]'
echo "def (" > "$R/resources/board/broken.py"; echo "COMMANDS = {}" >> "$R/resources/board/broken.py"
E="$($P help 2>&1)"
check "a module that fails to import is reported, not fatal" 'grep -q "broken.py failed to import" <<< "$E" && [ "$($P hello 2>/dev/null)" = "hello" ]'
rm "$R/resources/board/other.py" "$R/resources/board/broken.py"
check "clash gone: help exits 0 again" '$P help >/dev/null 2>&1'

# ── the real tree ─────────────────────────────────────────────────────────────
cd "$REPO"
check "on this repo: pearde help exits 0 or names a real clash" 'python3 "$REPO/resources/pearde.py" help >/dev/null 2>&1 || python3 "$REPO/resources/pearde.py" help 2>&1 | grep -q "claimed by"'
check "on this repo: pearde and pearde scan are byte-identical" 'python3 "$REPO/resources/pearde.py" > "$D/e.txt" 2>&1; python3 "$REPO/resources/pearde.py" scan > "$D/f.txt" 2>&1; cmp -s "$D/e.txt" "$D/f.txt"'

echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" = 0 ]
