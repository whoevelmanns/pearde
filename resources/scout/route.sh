#!/usr/bin/env bash
# Call one route from routes.md — the pages a ranking comes from, one shell
# block each, addressed by id.
#
# routes.md is the knob and this file is only its reader: the block printed
# under `### <id>` is what runs, with $Q bound to the query and $N to the row
# count. Adding a route is editing that file, never this one.
#
#   route.sh list [group]      every route, or one group's
#   route.sh <id> [query...]   run it — query defaults to the route's example
#   route.sh check [id ...]    run every route against its example, green or dead
#
# Env: SCOUT_N rows (default 10), SCOUT_MAILTO contact for the polite pools,
# and whatever a route documents for itself (ECO, REG, CC, SEARX).
set -euo pipefail
export LC_ALL=C

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
routes="$here/routes.md"
export N="${SCOUT_N:-10}"
export MAILTO="${SCOUT_MAILTO:-scout@localhost}"
export UA="pearde-scout (mailto:$MAILTO)"
export HERE="$here"

die() { echo "route: $*" >&2; exit 1; }
[ -f "$routes" ] || die "no route index at $routes"

# The block under `### <id>` — everything between the first ```sh fence and its
# close. Stops at the next heading, so an id that owns no block prints nothing.
block() {
	awk -v id="$1" '
		$0 ~ "^### " id " " { inr = 1; next }
		inr && insh && /^```$/ { exit }
		inr && insh { print; next }
		inr && /^```sh$/ { insh = 1; next }
		inr && /^#/ { exit }
	' "$routes"
}

# One `- **key** value` bullet from a route, backticks stripped.
field() {
	awk -v id="$1" -v k="$2" '
		$0 ~ "^### " id " " { inr = 1; next }
		inr && /^#/ { exit }
		inr && $0 ~ "^- \\*\\*" k "\\*\\* " {
			sub("^- \\*\\*" k "\\*\\* ", ""); gsub(/`/, ""); print; exit
		}
	' "$routes"
}

ids() { sed -n 's/^### \([a-z0-9-]*\) .*/\1/p' "$routes"; }

cmd_list() {
	local want="${1:-}"
	awk -v want="$want" '
		/^## / { group = $0; sub(/^## /, "", group); sub(/ —.*/, "", group) }
		/^### / {
			line = $0; sub(/^### /, "", line)
			id = line; sub(/ .*/, "", id)
			head = line; sub(/^[^ ]* — /, "", head)
			if (want == "" || group == want) printf "%-14s %-22s %s\n", id, group, head
		}
	' "$routes"
}

run() {
	local id="$1"; shift
	local b; b="$(block "$id")"
	[ -n "$b" ] || die "no route '$id' — try 'route.sh list'"
	local q="$*"
	[ -n "$q" ] || q="$(field "$id" example)"
	Q="$q" bash -c "$b"
}

cmd_check() {
	local list; list="${*:-$(ids)}"
	# macOS ships neither timeout nor gtimeout by default — a route that hangs
	# then hangs the check, which is loud enough to fix by hand.
	local tmo=""
	command -v timeout >/dev/null 2>&1 && tmo="timeout 40"
	[ -n "$tmo" ] || { command -v gtimeout >/dev/null 2>&1 && tmo="gtimeout 40"; }
	local id b out rc flag bad=0
	for id in $list; do
		b="$(block "$id")" || true
		if [ -z "$b" ]; then printf '%-14s %-6s %s\n' "$id" "DEAD" "no block"; bad=1; continue; fi
		case "$(field "$id" auth)" in
			yours*) printf '%-14s %-6s %s\n' "$id" "skip" "runs against your own instance"; continue ;;
		esac
		set +e
		out="$(Q="$(field "$id" example)" N=3 $tmo bash -c "$b" 2>&1)"
		rc=$?
		set -e
		# One failure is a rate limit — 43 calls back to back trip pypistats and
		# the wayback CDX. Two failures is a dead route.
		if [ "$rc" -ne 0 ] || [ -z "$out" ]; then
			sleep 5
			set +e
			out="$(Q="$(field "$id" example)" N=3 $tmo bash -c "$b" 2>&1)"
			rc=$?
			set -e
			flag="flaky"
		else
			flag="ok"
		fi
		if [ "$rc" -eq 0 ] && [ -n "$out" ]; then
			printf '%-14s %-6s %s\n' "$id" "$flag" "$(printf '%s' "$out" | head -1 | cut -c1-72)"
		else
			printf '%-14s %-6s rc=%s %s\n' "$id" "DEAD" "$rc" "$(printf '%s' "$out" | head -1 | cut -c1-64)"
			bad=1
		fi
	done
	return "$bad"
}

case "${1:-}" in
	''|-h|--help) awk 'NR>1 && /^#/ {sub(/^# ?/,""); print; next} NR>1 {exit}' "${BASH_SOURCE[0]}" >&2; exit 2 ;;
	list)  shift; cmd_list "$@" ;;
	check) shift; cmd_check "$@" ;;
	*)     run "$@" ;;
esac
