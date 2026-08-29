#!/bin/bash
# Verify that `workflows.py check` reads a master board's members, resolves
# each slug the way @references/parts/workers.md orders it, and reports a
# `workflow:` whose shape is not a slug.
#
#   bash prds/check-crosses-member-boundaries/probe/verify.sh
#   bash prds/check-crosses-member-boundaries/probe/verify.sh --vs-head
#
# `--vs-head` re-runs this same harness against `git show HEAD:` copies of
# the two readers and prints how many checks FAIL there. A box that passes
# against the build proves nothing on its own; a box that fails against HEAD
# is a box that can fail. Ten of the eighteen do.
#
# Exit 0 and a `verify: N/N` line when every case holds. The fixture is built
# in a temp dir and removed on exit — no board on this machine is touched.
#
# NOT tested, because it was measured impossible: a member board run on its
# own resolving its master's library. A member has no `settings.md` naming a
# master and carries no back-reference, so nothing can find a master from
# below. `scan` fails there identically to `check` — see the PRD's F2. The
# fix is the master direction only, and that is what these boxes cover.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
WF="$ROOT/resources/workflows.py"
PLAN="$ROOT/resources/board/plan.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

EXPECTED=18   # pinned: a dropped check must fail loudly, not print a smaller total

# `--vs-head` — run this harness against HEAD's readers instead of the tree's.
if [ "${1:-}" = "--vs-head" ]; then
  command -v git >/dev/null 2>&1 || { echo "vs-head: no git"; exit 2; }
  H="$TMP/head"; mkdir -p "$H/resources/board" "$H/prds/x/probe"
  for f in $(git -C "$ROOT" ls-tree --name-only HEAD resources/ | grep '\.py$'); do
    git -C "$ROOT" show "HEAD:$f" > "$H/$f" 2>/dev/null
  done
  for f in $(git -C "$ROOT" ls-tree --name-only HEAD resources/board/ | grep '\.py$'); do
    git -C "$ROOT" show "HEAD:$f" > "$H/$f" 2>/dev/null
  done
  cp "${BASH_SOURCE[0]}" "$H/prds/x/probe/verify.sh"
  OUT="$(bash "$H/prds/x/probe/verify.sh" 2>&1)"
  LINE="$(printf '%s\n' "$OUT" | tail -1)"
  P="${LINE#verify: }"; P="${P%%/*}"; T="${LINE#*/}"; T="${T%% *}"
  printf '%s\n' "$OUT" | grep '^FAIL' || true
  printf 'vs HEAD: %s of %s checks FAIL against the unpatched readers\n' \
    "$((T - P))" "$T"
  [ "$((T - P))" -gt 0 ] || { echo "vs-head: NO check fails against HEAD — \
these boxes cannot fail and prove nothing"; exit 1; }
  exit 0
fi

PASS=0; FAIL=0
ok() { PASS=$((PASS+1)); }
no() { FAIL=$((FAIL+1)); printf 'FAIL  %s\n' "$1"; }

has()  { case "$2" in *"$1"*) ok ;; *) no "$3" ;; esac; }
hasnt() { case "$2" in *"$1"*) no "$3" ;; *) ok ;; esac; }
code() { [ "$1" = "$2" ] && ok || no "$3 — exit $1, wanted $2"; }

route () { # <libdir> <slug>
  mkdir -p "$1"
  { echo '---'; echo "workflow: $2"; echo 'subject: a fixture route'
    echo 'date: 2026-08-01'; echo '---'; echo
    echo "# $2"; echo; echo '## Use when'; echo
    echo '- a fixture needs a slug that resolves'; echo
    echo '## Steps'; echo
    echo '| # | atomic | why | on failure |'
    echo '|---|--------|-----|------------|'
    echo '| 1 | `step-one` | the only step | `stop` |'; } > "$1/$2.md"
  { echo '---'; echo 'atomic: step-one'; echo 'subject: the only step'
    echo 'date: 2026-08-01'; echo '---'; echo
    echo '## Do'; echo; echo 'Nothing — this is a fixture.'; echo
    echo '## Done when'; echo; echo '- nothing happened'; } > "$1/step-one.md"
}

prd () { # <dir> [workflow line]
  mkdir -p "$1"
  { echo '---'; echo 'state: specced'; echo 'priority: 10'
    [ $# -gt 1 ] && printf '%s\n' "$2"
    echo '---'; echo; echo "# $(basename "$1")"; } > "$1/prd.md"
}

# ── the master and its members ───────────────────────────────────────────────
mkdir -p "$TMP/master/prds" "$TMP/solo/prds" "$TMP/ownlib/prds"
route "$TMP/master/prds/workflows" mw          # the MASTER holds `mw`
route "$TMP/ownlib/prds/workflows" ownroute    # the MEMBER holds `ownroute`
{ echo '---'; echo 'members:'; echo '  - solo: ../../solo/prds'
  echo '  - ownlib: ../../ownlib/prds'; echo '---'; echo
  echo '# fixture master'; } > "$TMP/master/prds/settings.md"

prd "$TMP/solo/prds/broken"   'workflow: no-such-route'
prd "$TMP/solo/prds/b-master" 'workflow: mw'
prd "$TMP/ownlib/prds/b-own"  'workflow: ownroute'

M="$TMP/master/prds"
OUT="$(python3 "$WF" check "$M" 2>&1)"; RC=$?

# 1 — the blindness: a master sees a dangling route inside a member
has 'broken/prd.md' "$OUT" "a master's check does not report a member's dangling slug"
code "$RC" 1 "a master with one broken member exits 0"

# 2 — the address is the one `plan.py scan` prints
has '@solo/broken/prd.md' "$OUT" "a member's PRD is not addressed @<member>/<rel>"

# 3 — resolution order, master half: `mw` is the master's, and resolves
hasnt 'b-master' "$OUT" "a slug resolving in the master's library is reported (false positive)"

# 4 — resolution order, own half: `ownroute` is the member's, and resolves
hasnt 'b-own' "$OUT" "a slug resolving in the member's own library is reported"

# 5 — a clean master is silent and exits 0
rm -rf "$TMP/solo/prds/broken"
OUT="$(python3 "$WF" check "$M" 2>&1)"; RC=$?
[ -z "$OUT" ] && ok || no "a master whose members are clean is not silent: $OUT"
code "$RC" 0 "a clean master does not exit 0"

# 6 — a member named in members: and missing from disk is reported, not skipped
{ echo '---'; echo 'members:'; echo '  - solo: ../../solo/prds'
  echo '  - ownlib: ../../ownlib/prds'; echo '  - gone: ../../gone/prds'
  echo '---'; echo; echo '# fixture master'; } > "$M/settings.md"
OUT="$(python3 "$WF" check "$M" 2>&1)"; RC=$?
has 'gone' "$OUT" "a member missing from disk is skipped silently"
code "$RC" 1 "a master with a missing member exits 0"
{ echo '---'; echo 'members:'; echo '  - solo: ../../solo/prds'
  echo '  - ownlib: ../../ownlib/prds'; echo '---'; } > "$M/settings.md"

# 7 — a `workflow:` that is not a slug is a break in BOTH readers
mkdir -p "$M/listed"
{ echo '---'; echo 'state: specced'; echo 'priority: 10'; echo 'workflow:'
  echo '  - one-route'; echo '  - two-route'; echo '---'; echo
  echo '# listed'; } > "$M/listed/prd.md"
OUT="$(python3 "$WF" check "$M" 2>&1)"; RC=$?
has 'listed/prd.md' "$OUT" "check passes a list-valued workflow: in silence"
has 'one slug' "$OUT" "check does not say the key holds one slug"
code "$RC" 1 "a list-valued workflow: does not exit 1"
SOUT="$(python3 "$PLAN" scan "$M" 2>&1)"
has 'listed' "$SOUT" "scan does not print the listed PRD at all"
case "$SOUT" in *listed*wf*\?*) ok ;; *) no "scan does not mark a list-valued workflow: as a break" ;; esac

# 8 — a plain board with no members: unchanged behaviour, still reports its own
mkdir -p "$TMP/plain/prds"
route "$TMP/plain/prds/workflows" pr
prd "$TMP/plain/prds/dangle" 'workflow: nope'
OUT="$(python3 "$WF" check "$TMP/plain/prds" 2>&1)"; RC=$?
has 'dangle/prd.md' "$OUT" "a plain board stopped reporting its own dangling slug"
has 'in the library' "$OUT" "a plain board's wording changed from 'in the library'"
code "$RC" 1 "a plain board with a dangling slug does not exit 1"

# 9 — `brief` keeps a blank line inside `## Use when`
L="$TMP/plain/prds/workflows"
{ echo '---'; echo 'workflow: para'; echo 'subject: a trailing paragraph'
  echo 'date: 2026-08-01'; echo '---'; echo; echo '# para'; echo
  echo '## Use when'; echo; echo '- the first bullet'; echo
  echo 'Not every job is this one.'; echo
  echo '## Steps'; echo
  echo '| # | atomic | why | on failure |'
  echo '|---|--------|-----|------------|'
  echo '| 1 | `step-one` | the only step | `stop` |'; } > "$L/para.md"
BOUT="$(python3 "$WF" brief para "$TMP/plain/prds" 2>&1)"
case "$BOUT" in *"- the first bullet"$'\n\n'"Not every job"*) ok ;;
  *) no "brief glues the paragraph onto the last bullet of ## Use when" ;; esac

[ "$((PASS+FAIL))" = "$EXPECTED" ] || no "expected $EXPECTED checks, ran $((PASS+FAIL))"
printf 'verify: %d/%d checks pass\n' "$PASS" "$((PASS+FAIL))"
[ "$FAIL" -eq 0 ]
