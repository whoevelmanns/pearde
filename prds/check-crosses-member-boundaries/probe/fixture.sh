#!/usr/bin/env bash
# Builds the PRD's fixture in a run-time directory and prints what each reader
# says. No argument: a fresh mktemp dir, removed on exit. One argument: build
# it there and leave it. Never writes under prds/ — a dir holding prd.md
# anywhere under the board is a PRD.
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
if [ $# -ge 1 ]; then TMP="$1"; mkdir -p "$TMP"; else
  TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT; fi

wf () { # <dir> <slug> — a valid one-step workflow named <slug>
  mkdir -p "$1"
  cat > "$1/$2.md" <<WF
---
workflow: $2
subject: a fixture route
date: 2026-08-01
runs: 0
---

# Workflow $2

## Use when

- a fixture needs a slug that resolves

## Steps

| # | atomic | why | on failure |
|---|--------|-----|------------|
| 1 | \`step-one\` | the only step | \`stop\` |
WF
  cat > "$1/step-one.md" <<AT
---
atomic: step-one
subject: the only step
date: 2026-08-01
---

## Do

Nothing — this is a fixture.

## Done when

- [ ] nothing happened
AT
}

prd () { # <boarddir> <name> <workflow-value-line-or-empty>
  mkdir -p "$2"
  { echo '---'; echo 'state: specced'; echo 'priority: 10';
    [ -n "${3:-}" ] && echo "$3"; echo '---'; echo;
    echo "# $(basename "$2") — a fixture PRD"; } > "$2/prd.md"
}

# --- the master, and its members -------------------------------------------
mkdir -p "$TMP/master/prds" "$TMP/solo/prds" "$TMP/ownlib/prds"
wf "$TMP/master/prds/workflows" mw          # only the MASTER holds `mw`
wf "$TMP/ownlib/prds/workflows" ownroute    # only the MEMBER holds `ownroute`

cat > "$TMP/master/prds/settings.md" <<SM
---
members:
  - solo: ../../solo/prds
  - ownlib: ../../ownlib/prds
  - gone: ../../gone/prds
---

# fixture master
SM

prd "$TMP/master/prds" "$TMP/solo/prds/broken"    'workflow: no-such-route'
prd "$TMP/master/prds" "$TMP/solo/prds/b-master"  'workflow: mw'
prd "$TMP/master/prds" "$TMP/ownlib/prds/b-own"   'workflow: ownroute'
mkdir -p "$TMP/master/prds/listed"
printf -- '---\nstate: specced\npriority: 10\nworkflow:\n  - one-route\n  - two-route\n---\n\n# listed\n' \
  > "$TMP/master/prds/listed/prd.md"

run () { # <label> <board>
  out="$(python3 "$REPO/resources/workflows.py" check "$2" 2>&1)"; rc=$?
  echo "--- check on $1 — exit $rc"
  [ -n "$out" ] && echo "$out" | sed 's/^/    /'
  return 0
}

echo "fixture at $TMP"
echo
run "the master   ($TMP/master/prds)"  "$TMP/master/prds"
run "member solo  ($TMP/solo/prds)"    "$TMP/solo/prds"
run "member ownlib($TMP/ownlib/prds)"  "$TMP/ownlib/prds"
echo
echo "--- scan on the master (plan.py), for comparison"
python3 "$REPO/resources/board/plan.py" scan "$TMP/master/prds" 2>&1 \
  | grep -E "broken|b-master|b-own|listed|MISSING|gone" | sed 's/^/    /'
