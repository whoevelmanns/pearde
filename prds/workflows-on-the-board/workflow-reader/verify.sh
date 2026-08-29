#!/bin/bash
# Verify @resources/workflows.py against a scratch library holding one clean
# workflow with two atomics and one file per failure shape in
# @references/workflow.md's `## The check`.
#
#   bash prds/workflows-on-the-board/workflow-reader/verify.sh
#
# Exit 0 and a `verify: N/N` line when every shape reports exactly its own
# line, the clean files report nothing, and `brief` inlines both atomics in
# step order. The fixture is built in a temp dir and removed on exit — the
# real library is never touched.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
WF="$ROOT/resources/workflows.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
B="$TMP/prds"; L="$B/workflows"
mkdir -p "$L" "$B/a-prd"
printf -- '---\nlanguage: English\n---\n' > "$B/settings.md"

PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); }
no()  { FAIL=$((FAIL+1)); printf 'FAIL  %s\n' "$1"; }

# ── the clean pair, plus the workflow over them ──────────────────────────────
cat > "$L/read-the-contract.md" <<'EOF'
---
atomic: read-the-contract
subject: read the format before touching the file
date: 2026-08-28
runs: 2
---

# read-the-contract — read the format before touching the file

## Do

1. `cat references/workflow.md` and read `## The check`.

## Done when

- The closed key set can be named without reopening the file.

## Fails when

| seen | means | do |
|------|-------|----|
EOF
cat > "$L/reproduce-the-failure.md" <<'EOF'
---
atomic: reproduce-the-failure
subject: turn a report into a command that fails on this tree
date: 2026-08-28
updated: 2026-09-02
runs: 4
---

# reproduce-the-failure — a report becomes a failing command

## Do

1. Run `python3 resources/workflows.py check` and read the lines.

## Done when

- One command fails on this tree and its output is quoted.

## Fails when

| seen | means | do |
|------|-------|----|
| exit 0 | the tree is already clean | ask for the tree it failed on |
EOF
cat > "$L/fix-a-reported-break.md" <<'EOF'
---
workflow: fix-a-reported-break
subject: a reported break, from the report to the verified fix
date: 2026-08-28
runs: 0
---

# fix-a-reported-break — a report becomes a verified fix

## Use when

- A break is reported against a file this repo owns.
- Not a new feature — that is a PRD, not a workflow.

## Steps

| # | atomic | why | on failure |
|---|--------|-----|------------|
| 1 | `read-the-contract` | the fix is judged against the format, not taste | `stop` |
| 2 | `reproduce-the-failure` | a fix with no failing command is a guess | `→ 1` |
EOF

# ── one file per failure shape ───────────────────────────────────────────────
printf '# no-fence — a file that never opened a fence\n' > "$L/no-fence.md"
printf -- '---\natomic: unterminated\nsubject: a fence that never closes\ndate: 2026-08-28\n' > "$L/unterminated.md"

mk_atomic() { # slug, extra-frontmatter, body-override
  cat > "$L/$1.md" <<EOF
---
atomic: $1
subject: a fixture for one failure shape
date: 2026-08-28
$2---

# $1 — a fixture

## Do

1. Nothing.

## Done when

- Nothing.
EOF
}
mk_atomic no-slug-key ""
python3 - "$L/no-slug-key.md" <<'EOF'
import sys
p = sys.argv[1]
s = open(p).read().replace("atomic: no-slug-key\n", "")
open(p, "w").write(s)
EOF
mk_atomic both-keys "workflow: both-keys
"
mk_atomic slug-mismatch ""
python3 - "$L/slug-mismatch.md" <<'EOF'
import sys
p = sys.argv[1]
s = open(p).read().replace("atomic: slug-mismatch", "atomic: something-else")
open(p, "w").write(s)
EOF
mk_atomic missing-subject ""
python3 - "$L/missing-subject.md" <<'EOF'
import sys
p = sys.argv[1]
s = open(p).read().replace("subject: a fixture for one failure shape\n", "")
open(p, "w").write(s)
EOF
mk_atomic stray-key "owner: nobody
"
mk_atomic bad-date ""
python3 - "$L/bad-date.md" <<'EOF'
import sys
p = sys.argv[1]
s = open(p).read().replace("date: 2026-08-28", "date: 28.08.2026")
open(p, "w").write(s)
EOF
mk_atomic early-updated "updated: 2026-08-01
"
mk_atomic bad-runs "runs: many
"
cat > "$L/no-do.md" <<'EOF'
---
atomic: no-do
subject: an atomic with no Do
date: 2026-08-28
---

# no-do — an atomic with no Do

## Done when

- Nothing.
EOF
cat > "$L/no-done-when.md" <<'EOF'
---
atomic: no-done-when
subject: an atomic with no Done when
date: 2026-08-28
---

# no-done-when — an atomic with no Done when

## Do

1. Nothing.
EOF
cat > "$L/no-steps.md" <<'EOF'
---
workflow: no-steps
subject: a workflow with no Steps table
date: 2026-08-28
---

# no-steps — a workflow with no Steps table

## Use when

- Never.
EOF
mk_workflow() { # slug, rows
  cat > "$L/$1.md" <<EOF
---
workflow: $1
subject: a fixture for one failure shape
date: 2026-08-28
---

# $1 — a fixture

## Use when

- Never.

## Steps

| # | atomic | why | on failure |
|---|--------|-----|------------|
$2
EOF
}
mk_workflow noncontiguous '| 1 | `read-the-contract` | a clause | `stop` |
| 3 | `reproduce-the-failure` | a clause | `→ 1` |'
mk_workflow dangling-step '| 1 | `no-such-atomic` | a clause | `stop` |'
mk_workflow bad-onfailure '| 1 | `read-the-contract` | a clause | `→ 2` |'

# ── the board half ───────────────────────────────────────────────────────────
cat > "$B/a-prd/prd.md" <<'EOF'
---
state: backlog
origin: requested
priority: 50
workflow: not-a-workflow
---

# a-prd — routed to a workflow nobody wrote
EOF

# A `workflow:` naming an atomic is the same failure with the file present:
# a route was asked for and a single step was found. Once from a `prd.md`,
# once from a spec — @resources/workflows.py reads both halves of the board.
mkdir -p "$B/routed-to-atomic/specs"
cat > "$B/routed-to-atomic/prd.md" <<'EOF'
---
state: backlog
origin: requested
priority: 50
workflow: read-the-contract
---

# routed-to-atomic — a prd.md routed to an atomic instead of a workflow
EOF
cat > "$B/routed-to-atomic/specs/spec01.md" <<'EOF'
---
complexity: 3
workflow: reproduce-the-failure
---

# spec01 — a spec routed to an atomic instead of a workflow
EOF

OUT="$(python3 "$WF" check "$B")"
RC=$?
if [ "$RC" = 1 ]; then ok; else no "check exit $RC, expected 1"; fi

expect() { # file, substring
  n=$(printf '%s\n' "$OUT" | grep -cF "$1: " )
  m=$(printf '%s\n' "$OUT" | grep -F "$1: " | grep -cF "$2")
  if [ "$n" = 1 ] && [ "$m" = 1 ]; then ok
  else no "$1 — $n line(s), $m matching \"$2\""; fi
}
expect "no-fence.md"      "no closed \`---\` frontmatter fence"
expect "unterminated.md"  "no closed \`---\` frontmatter fence"
expect "no-slug-key.md"   "neither \`atomic:\` nor \`workflow:\`"
expect "both-keys.md"     "both \`atomic:\` and \`workflow:\`"
expect "slug-mismatch.md" "disagrees with the filename"
expect "missing-subject.md" "missing \`subject:\`"
expect "stray-key.md"     "is not a workflow key"
expect "bad-date.md"      "is not ISO 8601"
expect "early-updated.md" "precedes date"
expect "bad-runs.md"      "is not an integer >= 0"
expect "no-do.md"         "no \`## Do\`"
expect "no-done-when.md"  "no \`## Done when\`"
expect "no-steps.md"      "no \`## Steps\` table"
expect "noncontiguous.md" "contiguous"
expect "dangling-step.md" "no file in the library"
expect "bad-onfailure.md" "neither \`stop\` nor"
expect "a-prd/prd.md"     "names no workflow in the library"
expect "routed-to-atomic/prd.md" "names \`read-the-contract.md\`, not a workflow"
expect "routed-to-atomic/specs/spec01.md" "names \`reproduce-the-failure.md\`, not a workflow"

for clean in read-the-contract reproduce-the-failure fix-a-reported-break; do
  if printf '%s\n' "$OUT" | grep -qF "$clean.md: "; then
    no "$clean.md — clean file reported"
  else ok; fi
done

# ── the clean library alone is silent ────────────────────────────────────────
C="$TMP/clean/prds"; mkdir -p "$C/workflows"
printf -- '---\nlanguage: English\n---\n' > "$C/settings.md"
for f in read-the-contract reproduce-the-failure fix-a-reported-break; do
  cp "$L/$f.md" "$C/workflows/"
done
CO="$(python3 "$WF" check "$C")"; CRC=$?
if [ -z "$CO" ] && [ "$CRC" = 0 ]; then ok
else no "a clean library is not silent (exit $CRC): $CO"; fi

# ── brief inlines both atomics, in step order ────────────────────────────────
BR="$(python3 "$WF" brief fix-a-reported-break "$C")"; BRC=$?
[ "$BRC" = 0 ] && ok || no "brief exit $BRC"
printf '%s\n' "$BR" | grep -q '^## Use when' && ok || no "brief has no ## Use when"
printf '%s\n' "$BR" | grep -q '^### 1 — read-the-contract' && ok || no "brief has no step 1 heading"
printf '%s\n' "$BR" | grep -q '^### 2 — reproduce-the-failure' && ok || no "brief has no step 2 heading"
printf '%s\n' "$BR" | grep -qF 'cat references/workflow.md' && ok || no "brief omits atomic 1 body"
printf '%s\n' "$BR" | grep -qF 'python3 resources/workflows.py check' && ok || no "brief omits atomic 2 body"
STRAY=$(printf '%s\n' "$BR" | grep -c '^## ' )
[ "$STRAY" = 1 ] && ok || no "brief leaves $STRAY level-2 headings — an inlined atomic must sit under its step"
o1=$(printf '%s\n' "$BR" | grep -n '^### 1' | cut -d: -f1)
o2=$(printf '%s\n' "$BR" | grep -n '^### 2' | cut -d: -f1)
[ "$o1" -lt "$o2" ] && ok || no "brief steps out of order"

# ── brief on an atomic exits 1 ───────────────────────────────────────────────
python3 "$WF" brief read-the-contract "$C" >/dev/null 2>&1
[ "$?" = 1 ] && ok || no "brief on an atomic did not exit 1"

# ── list: workflows first, then atomics ──────────────────────────────────────
LI="$(python3 "$WF" list "$C")"
[ "$(printf '%s\n' "$LI" | wc -l | tr -d ' ')" = 3 ] && ok || no "list printed $(printf '%s\n' "$LI" | wc -l) rows, expected 3"
printf '%s\n' "$LI" | head -1 | grep -q '^fix-a-reported-break .*workflow' && ok || no "list does not put the workflow first"
printf '%s\n' "$LI" | grep -q 'reproduce-the-failure .*atomic .*4 *2026-09-02 ' && ok || no "list row is missing runs/updated"

# ── show prints the file verbatim ────────────────────────────────────────────
python3 "$WF" show read-the-contract "$C" | diff -q - "$C/workflows/read-the-contract.md" >/dev/null \
  && ok || no "show does not print the file verbatim"

# ── an external library gets the whole check ─────────────────────────────────
E="$TMP/ext/prds"; mkdir -p "$E" "$TMP/ext/shared"
printf -- '---\nlanguage: English\nworkflows: ../shared\n---\n' > "$E/settings.md"
cp "$L/bad-runs.md" "$TMP/ext/shared/"
EO="$(python3 "$WF" check "$E")"
printf '%s\n' "$EO" | grep -qF 'bad-runs.md: runs' && ok || no "an external library is not checked: $EO"
printf -- '---\nlanguage: English\nworkflows: ../gone\n---\n' > "$E/settings.md"
MO="$(python3 "$WF" check "$E")"
printf '%s\n' "$MO" | grep -qF 'which does not exist' && ok || no "a missing external library is not reported: $MO"

# The line above reports checks *executed*, not checks *expected*: drop one to
# a stray `continue` or a quoting slip and it prints `38/38 checks pass` and
# exits 0, which is indistinguishable from success. Pin the denominator.
[ "$((PASS+FAIL))" = 39 ] || no "expected 39 checks, ran $((PASS+FAIL))"
echo "verify: $PASS/$((PASS+FAIL)) checks pass"
[ "$FAIL" = 0 ] || exit 1
