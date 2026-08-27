# The routes — every page a ranking comes from

One route answers one question. The heading is the question; the block under
the id is how it is asked. `route.sh <id> [query]` runs that block with `$Q`
bound to the query and `$N` to the row count — this file is the knob,
`route.sh` is only its reader, the same split as `buckets.txt` and `scout.sh`.

**The axis is the finding.** `hn` ranks by attention, `brew` by installs, `gh`
by stars, `scorecard` by hygiene. Four verdicts on one tool, and they
disagree. A row in `findings.md` names which axis it was measured on, because
a claim measured on stars is a different claim from one measured on installs.

**One question, at least two axes.** A pick backed by a single route is an
opinion. `ripgrep` is top-30 on `brew` *and* 78% on `arch` *and* green on
`scorecard` — that is a finding.

Every block here ran green under `route.sh check` on **2026-08-26**. Re-run it
before trusting a row; a route that dies is deleted or moved to
[Dead ends](#dead-ends), never left in place.

Conventions:

- `$Q` — the query. `route.sh <id>` with no query uses the route's `example`.
- `$N` — rows, from `SCOUT_N` (default 10).
- `$UA` — a polite user agent carrying `SCOUT_MAILTO`. Registries rate-limit
  the default agent hard; ecosyste.ms answers `402 Payment Required` to it.
- `ECO`, `REG`, `CC`, `SEARX` — per-route env, documented on the route.
- `jq` and `curl` are assumed. `gh` only for the GitHub routes.

## Attention — what the field is talking about now

### hn — Hacker News stories, ranked by points
- **ranks** attention at posting time
- **auth** none
- **example** `ripgrep`
- **gotcha** a score dates the post, not the tool — a 2019 launch outranks this year's better fork

```sh
curl -sG 'https://hn.algolia.com/api/v1/search' \
	--data-urlencode "query=$Q" -d tags=story -d hitsPerPage="$N" |
jq -r '.hits[] | [.points, .num_comments, .title,
	(.url // ("https://news.ycombinator.com/item?id=" + .objectID))] | @tsv'
```

### hn-now — the HN front page as it stands
- **ranks** what is on the front page this minute
- **auth** none
- **example** `-`
- **gotcha** no query — the whole point is what you did not search for

```sh
curl -sG 'https://hn.algolia.com/api/v1/search' -d tags=front_page -d hitsPerPage="$N" |
jq -r '.hits[] | [.points, .num_comments, .title] | @tsv'
```

### lobsters — one tag's hottest, ranked by score
- **ranks** attention inside a tag, from a smaller and more technical crowd
- **auth** none
- **example** `rust`
- **gotcha** the tag must exist — `lobste.rs/t/<tag>` in a browser is the check

```sh
curl -s -A "$UA" "https://lobste.rs/t/$Q.json" |
jq -r ".[:$N][] | [.score, .comment_count, .title, .url] | @tsv"
```

### papers — Hugging Face daily papers, ranked by upvotes
- **ranks** what ML practitioners are reading today
- **auth** none
- **example** `-`
- **gotcha** upvotes are a community signal on a hosting site, not citations — see `openalex` for those

```sh
curl -s 'https://huggingface.co/api/daily_papers' |
jq -r ".[:$N][] | [.paper.upvotes, .paper.id, .paper.title] | @tsv"
```

### smallweb — Kagi's small-web feed
- **ranks** nothing — it is a sample of pages with no SEO behind them
- **auth** none
- **example** `-`
- **gotcha** an Atom feed, so the shape is layout-coupled; a format change shows up as empty output

```sh
curl -s 'https://kagi.com/api/v1/smallweb/feed/' |
grep -oE '<title[^>]*>[^<]+' | sed -E 's/<title[^>]*>//' | tail -n +2 | head -n "$N"
```

### wiki — Wikipedia's most-read articles for one day
- **ranks** public attention, by pageviews
- **auth** none
- **example** `2026/08/01`
- **gotcha** query is `YYYY/MM/DD`; the tail is dominated by the main page and search-portal entries

```sh
curl -s "https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/$Q" |
jq -r ".items[0].articles[:$N][] | [.rank, .views, .article] | @tsv"
```

## Installs — what people actually run

### brew — Homebrew installs, last 30 days
- **ranks** real installs on real Macs — the strongest anti-star axis for CLI tools
- **auth** none
- **example** `^rip|^fd$|silver_searcher`
- **gotcha** query is a regex over formula names; macOS only, so server-side tools read low

```sh
curl -s 'https://formulae.brew.sh/api/analytics/install/30d.json' |
jq -r --arg q "$Q" '.items[] | select(.formula | test($q)) |
	[.count, .number, .formula] | @tsv' | head -n "$N"
```

### npm — npm search, weighted by popularity
- **ranks** weekly downloads against a text query
- **auth** none
- **example** `http client`
- **gotcha** downloads count CI robots as heavily as people

```sh
curl -sG 'https://registry.npmjs.org/-/v1/search' \
	--data-urlencode "text=$Q" -d size="$N" -d popularity=1.0 |
jq -r '.objects[] | [.downloads.weekly, .package.name, .package.description] | @tsv'
```

### npm-dl — one npm package, last week
- **ranks** a single package's download count
- **auth** none
- **example** `express`
- **gotcha** a dependency of a popular package inherits its number; high downloads prove reach, not choice

```sh
curl -s "https://api.npmjs.org/downloads/point/last-week/$Q" |
jq -r '[.package, .downloads] | @tsv'
```

### crates — crates.io, ranked by recent downloads
- **ranks** Rust package pull, recent over total
- **auth** none
- **example** `regex`
- **gotcha** crates.io requires a contact user agent; `recent_downloads` is 90 days

```sh
curl -sG 'https://crates.io/api/v1/crates' -A "$UA" \
	--data-urlencode "q=$Q" -d sort=recent-downloads -d per_page="$N" |
jq -r '.crates[] | [.recent_downloads, .downloads, .name, .description] | @tsv'
```

### pypi — one PyPI package, recent downloads
- **ranks** a single package's week and month
- **auth** none
- **example** `requests`
- **gotcha** mirrors and CI inflate this more than any other registry, and the host rate-limits to roughly one call a second — hence the retries

```sh
curl -s --retry 3 --retry-delay 5 "https://pypistats.org/api/packages/$Q/recent" |
jq -r '[.package, .data.last_week, .data.last_month] | @tsv'
```

### popcon — Debian popularity contest
- **ranks** installs on machines whose owners opted in to being counted
- **auth** none
- **example** `ripgrep|fd-find|silversearcher`
- **gotcha** the sample skews to long-lived servers, so it lags new tools by years — that lag is the signal

```sh
curl -s 'https://popcon.debian.org/by_inst' |
awk -v q="$Q" '$2 ~ q { print $1, $2, $3 }' | head -n "$N"
```

### arch — Arch Linux pkgstats
- **ranks** percentage of reporting Arch machines with the package
- **auth** none
- **example** `ripgrep`
- **gotcha** the opposite skew to popcon — Arch users adopt early, so this leads

```sh
curl -sG 'https://pkgstats.archlinux.de/api/packages' \
	--data-urlencode "query=$Q" -d limit="$N" |
jq -r '.packagePopularities[] | [.popularity, .count, .name] | @tsv'
```

### aur — the AUR, ranked by votes
- **ranks** what Arch users package by hand — the pre-official tier
- **auth** none
- **example** `ripgrep`
- **gotcha** votes accumulate forever and are never decayed

```sh
curl -s "https://aur.archlinux.org/rpc/v5/search/$Q" |
jq -r ".results | sort_by(-.NumVotes) | .[:$N][] | [.NumVotes, .Popularity, .Name] | @tsv"
```

### repology — how many distros ship it
- **ranks** packaging breadth, which is a proxy for "someone else already vetted this"
- **auth** none
- **example** `ripgrep`
- **gotcha** the query is repology's project name, not the binary's

```sh
curl -s -A "$UA" "https://repology.org/api/v1/project/$Q" |
jq -r --arg p "$Q" '[.[].repo] | unique | [$p, length] | @tsv'
```

### docker — Docker Hub, ranked by pulls
- **ranks** image pulls, the deployment axis
- **auth** none
- **example** `nginx`
- **gotcha** pull counts are lifetime and never reset; an old image cannot be caught

```sh
curl -sG 'https://hub.docker.com/v2/search/repositories/' \
	--data-urlencode "query=$Q" -d page_size="$N" |
jq -r '.results[] | [.pull_count, .star_count, .repo_name] | @tsv'
```

### models — Hugging Face models, ranked by downloads
- **ranks** which weights people actually pull
- **auth** none
- **example** `embedding`
- **gotcha** downloads are 30-day and count every `from_pretrained` in CI

```sh
curl -sG 'https://huggingface.co/api/models' \
	--data-urlencode "search=$Q" -d sort=downloads -d limit="$N" |
jq -r '.[] | [.downloads, .likes, .id] | @tsv'
```

### ecosystems — one package across every registry
- **ranks** dependents — how many packages and repos actually depend on it
- **auth** none, but the polite pool needs `SCOUT_MAILTO`
- **example** `ripgrep`
- **gotcha** `REG` picks the registry (default `crates.io`: `npmjs.org`, `pypi.org`, …). The default curl agent gets `402 Payment Required`; `$UA` gets 200

```sh
curl -s -A "$UA" \
	"https://packages.ecosyste.ms/api/v1/registries/${REG:-crates.io}/packages/$Q" |
jq -r '[.name, .downloads, .dependent_packages_count, .dependent_repos_count,
	.latest_release_published_at] | @tsv'
```

## Stars — what a forge already settled on

### gh — GitHub search, ranked by stars, with what stars hide
- **ranks** stars, next to last-push, archived, issues and license
- **auth** `gh` CLI, logged in
- **example** `topic:tui language:rust stars:>1000`
- **gotcha** this is `toolscout.sh` — the one route that is already a tool of its own

```sh
"$HERE/toolscout.sh" "$Q" --limit "$N"
```

### trending — GitHub's own trending page
- **ranks** star gain over a window, computed by GitHub
- **auth** none
- **example** `weekly`
- **gotcha** this is `scout.sh trending` — scraped HTML, and it dies loudly when the layout moves

```sh
"$HERE/scout.sh" trending "$Q" | head -n "$N"
```

### ossinsight — trending repos by engagement score
- **ranks** stars, forks, PRs and pushes fused into one score, server-side
- **auth** none
- **example** `past_week`
- **gotcha** query is the period (`past_24_hours`, `past_week`, `past_month`, `past_3_months`); the score favours small fast-moving repos, so the tail is 30-star projects

```sh
curl -sG 'https://api.ossinsight.io/v1/trends/repos/' -d "period=$Q" |
jq -r ".data.rows[:$N][] | [.stars, .total_score, .repo_name, .primary_language] | @tsv"
```

### codeberg — the forge with no star economy
- **ranks** stars on Codeberg
- **auth** none
- **example** `git`
- **gotcha** absolute counts are two orders below GitHub — read the ordering, never the number

```sh
curl -sG 'https://codeberg.org/api/v1/repos/search' \
	--data-urlencode "q=$Q" -d sort=stars -d order=desc -d limit="$N" |
jq -r '.data[] | [.stars_count, .full_name, .description] | @tsv'
```

### gitlab — GitLab projects by star count
- **ranks** stars on gitlab.com
- **auth** none for public projects
- **example** `terraform`
- **gotcha** search matches path and name only, so a well-named fork outranks the original

```sh
curl -sG 'https://gitlab.com/api/v4/projects' \
	--data-urlencode "search=$Q" -d order_by=star_count -d per_page="$N" |
jq -r '.[] | [.star_count, .path_with_namespace, .description] | @tsv'
```

## Verdict — whether it is safe to depend on

### scorecard — OpenSSF Scorecard for one repo
- **ranks** supply-chain hygiene out of 10, per check
- **auth** none
- **example** `BurntSushi/ripgrep`
- **gotcha** scores the *process*, not the code — a perfect score on an abandoned repo is still abandoned

```sh
curl -s "https://api.scorecard.dev/projects/github.com/$Q" |
jq -r '(["SCORE", (.score|tostring), .repo.name] | @tsv),
	(.checks[] | [.name, (.score|tostring)] | @tsv)'
```

### osv — every known advisory against one package
- **ranks** nothing — it answers yes or no
- **auth** none
- **example** `smallvec`
- **gotcha** `ECO` picks the ecosystem (default `crates.io`: `npm`, `PyPI`, `Go`, …), and the name must be the registry's

```sh
curl -s -X POST 'https://api.osv.dev/v1/query' \
	-d "{\"package\":{\"name\":\"$Q\",\"ecosystem\":\"${ECO:-crates.io}\"}}" |
jq -r '(.vulns // []) | if length == 0 then "clean" else .[] | [.id, .summary] | @tsv end'
```

### depsdev — release cadence and default version
- **ranks** publish dates — the cheapest read on whether a package is alive
- **auth** none
- **example** `ripgrep`
- **gotcha** `ECO` picks the system (default `cargo`: `npm`, `pypi`, `go`, `maven`, `nuget`)

```sh
curl -s "https://api.deps.dev/v3alpha/systems/${ECO:-cargo}/packages/$Q" |
jq -r ".versions[-$N:][] | [.versionKey.version, .publishedAt, (.isDefault|tostring)] | @tsv"
```

### advisories — GitHub's advisory database
- **ranks** severity of what is filed against a package
- **auth** none
- **example** `lodash`
- **gotcha** unauthenticated calls share the 60/hour anonymous pool

```sh
curl -sG 'https://api.github.com/advisories' \
	--data-urlencode "affects=$Q" -d per_page="$N" |
jq -r '.[] | [.severity, .ghsa_id, .summary] | @tsv'
```

### eol — is this version still supported
- **ranks** release cycles by end-of-life date
- **auth** none
- **example** `nodejs`
- **gotcha** the query is endoflife.date's product slug, not a package name

```sh
curl -s "https://endoflife.date/api/$Q.json" |
jq -r ".[:$N][] | [.cycle, .releaseDate, (.eol|tostring)] | @tsv"
```

## Recipes — how to use the thing you picked

### cht — cheat.sh, one answer per topic
- **ranks** nothing — it is the answer, not the shortlist
- **auth** none
- **example** `rust/regex`
- **gotcha** `?T` strips the terminal colours; `:list` on any path enumerates what it holds

```sh
curl -s "https://cht.sh/$Q?T&style=bw"
```

### tldr — the common invocations of one command
- **ranks** nothing — the five flags people actually type
- **auth** none
- **example** `rg`
- **gotcha** pages live per-platform; this tries `common` then `linux`

```sh
curl -sf "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/$Q.md" ||
curl -sf "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/linux/$Q.md"
```

## Search — reaching what no index here holds

### marginalia — the non-commercial web, searched
- **ranks** pages by an index that deliberately demotes SEO
- **auth** none
- **example** `ripgrep`
- **gotcha** the corpus is small — it finds the personal write-up, never the vendor page. Calls hang outright often enough that the route retries twice before it counts as dead

```sh
curl -s -m 20 --retry 2 --retry-all-errors "https://api.marginalia.nu/public/search/$Q" |
jq -r ".results[:$N][] | [.url, .title] | @tsv"
```

### ddg — DuckDuckGo's HTML-only endpoint
- **ranks** a mainstream index, without a key
- **auth** none
- **example** `ripgrep alternatives`
- **gotcha** scraped markup — a layout change shows up as zero rows, so the count is the check

```sh
curl -s -A 'Mozilla/5.0' 'https://lite.duckduckgo.com/lite/' --data-urlencode "q=$Q" |
grep -oE "href=\"https?://[^\"]+\" class='result-link'" |
sed -E "s/href=\"//; s/\" class.*//" | head -n "$N"
```

### stack — Stack Overflow, ranked by votes
- **ranks** questions by score, which is where a tool's sharp edges are written down
- **auth** none
- **example** `ripgrep`
- **gotcha** always gzipped, hence `--compressed`; 300 calls/day anonymous

```sh
curl -s --compressed -G 'https://api.stackexchange.com/2.3/search/advanced' \
	-d site=stackoverflow --data-urlencode "q=$Q" \
	-d order=desc -d sort=votes -d pagesize="$N" |
jq -r '.items[] | [.score, (.is_answered|tostring), .title] | @tsv'
```

### searx — your own SearXNG, in JSON
- **ranks** whatever engines you enable, merged
- **auth** yours to run — set `SEARX` to the base URL
- **example** `ripgrep`
- **gotcha** every public instance answers `429` or HTML to `format=json`; the route exists because running one is the only version that works — `docker run -d -p 8888:8080 searxng/searxng`, then set `search.formats: [html, json]` in its settings

```sh
curl -sG "${SEARX:?set SEARX to your own SearXNG base URL}/search" \
	--data-urlencode "q=$Q" -d format=json |
jq -r ".results[:$N][] | [.url, .title] | @tsv"
```

## Crawl — reading a page, and what it used to say

### read — any URL as markdown
- **ranks** nothing — it turns a page into text an agent can hold
- **auth** none at low volume
- **example** `https://example.com`
- **gotcha** the query is a full URL including scheme; heavy use wants a Jina key

```sh
curl -s "https://r.jina.ai/$Q"
```

### wayback — every capture of one URL
- **ranks** by time — what a page said before it changed
- **auth** none
- **example** `rust-lang.org`
- **gotcha** `collapse=timestamp:6` keeps one capture per month, or the output is thousands of rows; the CDX server throttles hard, hence the retries

```sh
curl -s --retry 2 --retry-delay 5 -G 'https://web.archive.org/cdx/search/cdx' \
	--data-urlencode "url=$Q" -d output=json -d limit="$N" -d collapse=timestamp:6 |
jq -r '.[1:][] | [.[1], .[4], .[2]] | @tsv'
```

### crawl — Common Crawl's index for a domain
- **ranks** nothing — it answers what a real crawler saw, at petabyte scale, for free
- **auth** none
- **example** `rust-lang.org/*`
- **gotcha** `CC` picks the crawl (default `CC-MAIN-2026-34`); the current list is `index.commoncrawl.org/collinfo.json`

```sh
curl -sG "https://index.commoncrawl.org/${CC:-CC-MAIN-2026-34}-index" \
	--data-urlencode "url=$Q" -d output=json |
head -n "$N" | jq -r '[.timestamp, .status, .url] | @tsv'
```

### tranco — a domain's rank, and its drift
- **ranks** domains by a research-grade list built to resist manipulation
- **auth** none
- **example** `github.com`
- **gotcha** ranks a *domain*, so it says nothing about a project on a shared host

```sh
curl -s "https://tranco-list.eu/api/ranks/domain/$Q" |
jq -r ".ranks[:$N][] | [.date, .rank] | @tsv"
```

## Registries — the new categories, enumerated

### mcp — the Model Context Protocol registry
- **ranks** nothing yet — it is the census of what an agent can be handed
- **auth** none
- **example** `github`
- **gotcha** publication is self-serve, so the list is unfiltered

```sh
curl -sG 'https://registry.modelcontextprotocol.io/v0/servers' \
	--data-urlencode "search=$Q" -d limit="$N" |
jq -r '.servers[] | [.server.name, .server.description] | @tsv'
```

### llms — every model one gateway serves, with prices
- **ranks** by nothing, but carries context length and price per token
- **auth** none
- **example** `claude`
- **gotcha** prices are that gateway's, not the vendor's list price

```sh
curl -s 'https://openrouter.ai/api/v1/models' |
jq -r --arg q "$Q" '.data[] | select(.id | test($q)) |
	[.id, (.context_length|tostring), .pricing.prompt] | @tsv' | head -n "$N"
```

### selfhosted — one entry from awesome-selfhosted, structured
- **ranks** nothing — it is an `awesome-*` list that ships YAML instead of bullet points
- **auth** none
- **example** `gitea`
- **gotcha** the query is the entry's file name; browse `software/` in that repo for the set

```sh
curl -sf "https://raw.githubusercontent.com/awesome-selfhosted/awesome-selfhosted-data/master/software/$Q.yml"
```

### openalex — papers, ranked by citations
- **ranks** citation count — the slowest and least fakeable signal here
- **auth** none, polite pool via `SCOUT_MAILTO`
- **example** `property-based testing`
- **gotcha** citations lag by years, so this is the opposite instrument to `papers`

```sh
curl -sG 'https://api.openalex.org/works' \
	--data-urlencode "search=$Q" -d 'sort=cited_by_count:desc' -d "per-page=$N" \
	--data-urlencode "mailto=$MAILTO" |
jq -r '.results[] | [.cited_by_count, .publication_year, .title] | @tsv'
```

### arxiv — the newest preprints on a topic
- **ranks** by submission date — unreviewed, which is the point
- **auth** none
- **example** `agent memory`
- **gotcha** `http` answers `301`, so the scheme is `https`; Atom XML parsed by line pairing, and a schema change shows as misaligned rows

```sh
curl -sG 'https://export.arxiv.org/api/query' \
	--data-urlencode "search_query=all:$Q" \
	-d sortBy=submittedDate -d sortOrder=descending -d max_results="$N" |
grep -E '<(title|published)>' | sed -E 's/ *<[^>]*>//g' | tail -n +2 | paste - -
```

## Dead ends

Tried, and rejected with a reason. A route here is not retried without new
evidence — the failure is recorded so the next sweep does not spend the call.

| route | tried | verdict |
|---|---|---|
| stargazers timeline | `api.github.com/repos/*/stargazers` | restricted since 2026-06-30 for repos you do not own. `scout.sh delta` exists because of this |
| libraries.io | `libraries.io/api/search` | `401` — API key required. `ecosystems` and `depsdev` answer the same question without one |
| grep.app | `grep.app/api/search` | `429` on the first anonymous call |
| sourcegraph | `.api/search/stream` | answers, but `matchCount: 0` — public code search needs a token |
| terminaltrove | `terminaltrove.com/new/` | Cloudflare interstitial, `403` |
| openhub | `openhub.net/p/*.json` | Cloudflare interstitial, `403` |
| reddit json | `reddit.com/r/*/top.json` | `403` without OAuth |
| software heritage | `archive.softwareheritage.org/api/1` | bot wall |
| public SearXNG | 8 instances from `searx.space` | every one `429`s or ignores `format=json` — see the `searx` route |
| product hunt | `api.producthunt.com/v2` | GraphQL, token required |
| brave / exa / tavily | their search APIs | keys and billing. `marginalia`, `ddg` and a self-hosted `searx` cover the need |

## Maintenance

- Add a route by adding a `### id` block here. `route.sh` reads this file and
  holds no list of its own.
- `route.sh check` runs every route against its `example` and prints `ok` or
  `DEAD`. Run it before writing a finding; a dead route invalidates the row it
  produced.
- `check` retries a failing route once after five seconds and reports it
  `flaky`. `DEAD` therefore means it failed twice — `pypi`, `marginalia` and
  `wayback` throttle under 43 back-to-back calls and read `flaky` when they do.
- A route that dies twice moves to [Dead ends](#dead-ends) with the observed
  status. Nothing is left in place "in case it comes back".
- Registries throttle by user agent. `SCOUT_MAILTO=you@example.com` puts every
  polite-pool route (ecosyste.ms, OpenAlex, crates.io, repology) in the fast
  tier.
