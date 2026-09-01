#!/usr/bin/env bash
# Sweep GitHub for things worth reusing — not just libraries, but the reference
# lists, starters and written-down practice that get cloned across every field.
#
# Two axes, because they answer different questions:
#   stars  — what the field already settled on. Safe, but you are late.
#   delta  — what it is settling on right now. Early, but half of it is hype.
#
# The stargazers API is restricted as of 2026-06-30, so there is no per-repo
# star timeline for a repo you do not own. Delta is computed the one way still
# open: snapshot star counts on every sweep, diff our own history. `delta`
# reports nothing until the second sweep and sharpens with every one after —
# and it measures the buckets in buckets.txt, not GitHub's global firehose.
#
#   scout.sh sweep              take a snapshot of every bucket
#   scout.sh delta [days]       what gained the most stars since ~N days ago
#   scout.sh trending [window]  GitHub's own trending, as a discovery channel
#                               for buckets you never thought to define
#                               (window: daily | weekly | monthly)
set -euo pipefail

# Repo descriptions are full of emoji and CJK; byte-wise collation keeps sort
# and awk from erroring out on sequences that are not valid in the user locale.
export LC_ALL=C

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scout="$root/scout"
snaps="$scout/snapshots"
buckets="$scout/buckets.txt"
per_bucket="${SCOUT_PER_BUCKET:-30}"
# One snapshot/day; keep enough to serve any `delta <days>` window callers
# actually use (README documents up to ~90) plus slack for gaps in the cron.
snap_keep="${SCOUT_SNAP_KEEP:-90}"

die() { echo "scout: $*" >&2; exit 1; }

cmd_sweep() {
	[ -f "$buckets" ] || die "no bucket file at $buckets"
	mkdir -p "$snaps"
	local out="$snaps/$(date -u +%Y-%m-%d).tsv"
	: > "$out"

	local n=0
	while IFS=$'\t' read -r name query; do
		case "$name" in ''|\#*) continue ;; esac
		[ -n "${query:-}" ] || continue
		printf '  %-14s %s\n' "$name" "$query" >&2

		# One search call per bucket. Authenticated search allows 30/min, so
		# even a large bucket file stays inside the limit without throttling.
		gh api -X GET search/repositories \
			-f q="$query" -f sort=stars -f order=desc -F per_page="$per_bucket" \
			--jq '.items[] | [
				.full_name, (.stargazers_count|tostring), .pushed_at,
				(.archived|tostring), (.license.spdx_id // "NONE"),
				(.language // "-"), ((.description // "") | gsub("\t";" "))
			] | @tsv' |
			sed "s/^/$name\t/" >> "$out" || die "search failed for bucket '$name'"
		n=$((n + 1))
	done < "$buckets"

	echo >&2
	echo "snapshot: $out  ($n buckets, $(wc -l < "$out" | tr -d ' ') rows)" >&2

	# Cap: keep only the snap_keep most recent snapshots so snapshots/ does
	# not grow unbounded — one ~700-line TSV per sweep, forever, otherwise.
	local all total over extra
	all=$(ls -1 "$snaps"/*.tsv 2>/dev/null | sort)
	total=$(echo "$all" | grep -c .)
	over=$((total - snap_keep))
	extra=""
	[ "$over" -gt 0 ] && extra=$(echo "$all" | head -n "$over")
	if [ -n "$extra" ]; then
		echo "$extra" | while IFS= read -r f; do rm -f "$f"; done
		echo "pruned $(echo "$extra" | wc -l | tr -d ' ') snapshot(s) older than the $snap_keep kept" >&2
	fi

	cmd_delta 0 2>/dev/null || echo "run again tomorrow for a delta" >&2
}

# Diff the newest snapshot against the most recent one at least N days older.
cmd_delta() {
	local want_days="${1:-7}"
	local files
	files=$(ls -1 "$snaps"/*.tsv 2>/dev/null | sort) || true
	[ -n "$files" ] || die "no snapshots yet — run 'scout.sh sweep' first"

	local newest base
	newest=$(echo "$files" | tail -1)
	base=$(echo "$files" | sed '$d' | tail -1)   # BSD head has no `-n -1`
	[ -n "${base:-}" ] || { echo "only one snapshot so far — nothing to diff" >&2; return 1; }

	# Prefer the oldest snapshot still inside the requested window, so `delta 30`
	# measures a month of movement rather than yesterday's noise.
	if [ "$want_days" -gt 0 ]; then
		local cutoff f
		cutoff=$(date -u -v-"${want_days}"d +%Y-%m-%d 2>/dev/null || date -u -d "$want_days days ago" +%Y-%m-%d)
		for f in $files; do
			[ "$(basename "$f" .tsv)" \< "$cutoff" ] && continue
			base="$f"; break
		done
	fi

	echo "# $(basename "$base" .tsv) -> $(basename "$newest" .tsv)" >&2
	awk -F'\t' -v OFS='\t' '
		NR==FNR { old[$2] = $3; next }
		{
			if (!($2 in old)) { gain = "NEW"; pct = "-" }
			else {
				d = $3 - old[$2]
				if (d <= 0) next
				gain = "+" d
				pct = old[$2] > 0 ? sprintf("%.1f%%", d * 100 / old[$2]) : "-"
			}
			key = ($2 in old) ? $3 - old[$2] : 999999999
			print key, $1, $2, $3, gain, pct, substr($8, 1, 60)
		}
	' "$base" "$newest" |
		sort -t$'\t' -k1,1nr | cut -f2- |
		{ printf 'BUCKET\tREPO\tSTARS\tGAIN\tRATE\tWHAT\n'; cat; } |
		head -40 | column -t -s $'\t'
}

cmd_trending() {
	local window="${1:-weekly}"
	local html
	html=$(curl -sfL -A "Mozilla/5.0" "https://github.com/trending?since=$window") \
		|| die "could not reach github.com/trending"

	# Repo names and star gains appear once per row in document order, so the
	# two extractions line up by position. A scraped page with no API behind
	# it — a mismatch is a layout change, and dies loudly.
	local names gains
	names=$(echo "$html" | grep -oE 'href="/[^"/]+/[^"/]+" data-view-component="true" class="Link"' \
		| sed -E 's|href="/||; s|" data.*||')
	gains=$(echo "$html" | grep -oE '[0-9,]+ stars (today|this week|this month)' | sed -E 's/ stars.*//')

	[ "$(echo "$names" | wc -l)" -eq "$(echo "$gains" | wc -l)" ] \
		|| die "trending layout changed — name/gain rows no longer align"

	{ printf 'REPO\tGAIN (%s)\n' "$window"; paste <(echo "$names") <(echo "$gains"); } \
		| column -t -s $'\t'
}

case "${1:-}" in
	sweep)    shift; cmd_sweep "$@" ;;
	delta)    shift; cmd_delta "$@" ;;
	trending) shift; cmd_trending "$@" ;;
	*)        awk 'NR>1 && /^#/ {sub(/^# ?/,""); print; next} NR>1 {exit}' \
	              "${BASH_SOURCE[0]}" >&2; exit 2 ;;
esac
