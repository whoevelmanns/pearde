#!/usr/bin/env bash
# Rank candidate dependencies for a project by GitHub popularity *and* the
# signals that stars alone hide: whether anyone still pushes to it, whether it
# is archived, whether it carries a license you can actually ship.
#
# Stars are a lagging popularity vote, not a fitness test — a 40k-star repo
# untouched for two years is a worse dependency than a 3k-star one shipping
# monthly. Both columns print, so the choice is made on both.
#
# Usage:
#   toolscout.sh 'topic:rust language:rust'      # a GitHub search query
#   toolscout.sh 'pdf parsing' --limit 40
#
# Query syntax is GitHub's own: topic:, language:, stars:>N, pushed:>DATE.
set -euo pipefail

limit=25
args=()
while [ $# -gt 0 ]; do
	case "$1" in
		--limit) limit="$2"; shift 2 ;;
		*) args+=("$1"); shift ;;
	esac
done

if [ ${#args[@]} -eq 0 ]; then
	sed -n '2,14p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//' >&2
	exit 2
fi

query="${args[*]}"
now="$(date -u +%s)"

# GitHub caps search results at 100/page; sort=stars gives the popularity axis,
# every other axis is computed below from the same payload.
gh api -X GET search/repositories \
	-f q="$query" -f sort=stars -f order=desc -F per_page="$limit" \
	--jq '.items[] | {
		name: .full_name,
		stars: .stargazers_count,
		pushed: .pushed_at,
		issues: .open_issues_count,
		license: (.license.spdx_id // "NONE"),
		archived: .archived,
		lang: (.language // "-"),
		desc: (.description // "")
	}' |
jq -rs --argjson now "$now" '
	def days(t): (($now - (t | fromdateiso8601)) / 86400) | floor;
	def flag(r):
		if r.archived then "ARCHIVED"
		elif days(r.pushed) > 365 then "stale"
		elif days(r.pushed) > 90 then "slow"
		else "active" end;
	["REPO","STARS","LAST PUSH","STATE","ISSUES","LICENSE","LANG"],
	(.[] | [
		.name,
		(.stars | tostring),
		"\(days(.pushed))d ago",
		flag(.),
		(.issues | tostring),
		.license,
		.lang
	])
	| @tsv
' | column -t -s "$(printf '\t')"

echo
echo "query: $query   (stars rank; 'STATE' is what stars do not tell you)"
