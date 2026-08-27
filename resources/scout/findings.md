# The findings — what won, on which axis, and when

The second index. `routes.md` is where a number comes from; this is what the
numbers decided. One row per **job**, never per tool — "recursive search over a
source tree" is a job, "ripgrep" is an answer, and the job outlives the answer.

What a finding is:

- **A job phrased as a choice.** If nothing was rejected, nothing was decided.
- **At least two axes.** Attention, installs, stars, hygiene — a pick standing
  on one route is an opinion and is marked `weak`.
- **Numbers, with the route that produced them.** `route.sh <id> <query>`
  reproduces every cell in the evidence tables below.
- **A date.** Findings expire: six months, then re-measure or delete. A stale
  row reads as current.
- **What would overturn it.** A finding that nothing could reverse was never a
  measurement.

Anything that has no answer yet goes to [Open](#open) — a queue, not a gap.

## Index

| job | pick | axes | measured | strength |
|---|---|---|---|---|
| recursive search over a source tree | `ripgrep` | brew · arch · popcon · repology · scorecard | 2026-08-26 | strong |
| web search from a script, no API key | `marginalia`, own SearXNG for volume | route probes across 12 endpoints | 2026-08-26 | strong |
| star momentum for a repo we do not own | our own snapshots (`scout.sh delta`) | github api · ossinsight · star-history | 2026-08-26 | strong |
| a page as text an agent can hold | `r.jina.ai` | one route only | 2026-08-26 | weak |

## Findings

### recursive search over a source tree

**Pick** `ripgrep`. **Beats** `the_silver_searcher`, `ugrep`, `grep`.

| tool | brew 30d | arch % | popcon inst | distros | scorecard |
|---|---|---|---|---|---|
| ripgrep | 85,537 (#50) | 78.63 | 13,329 | 122 | 4.7 |
| fd | 13,376 (#300) | 47.09 | 5,486 | — | 6.8 |
| ugrep | 4,899 (#567) | 1.84 | 655 | 91 | — |
| the_silver_searcher | 752 (#1441) | 4.37 | 2,255 | 108 | 3.4 |

**Why** the four axes agree, which is the whole test — ripgrep leads on
installs (`brew`), on early-adopter machines (`arch`), on conservative ones
(`popcon`), and on packaging breadth (`repology`). `the_silver_searcher` holds
distro breadth from its 2014 peak and nothing else; the gap between its 108
distros and its 752 monthly installs is what an abandoned tool looks like from
outside. `fd` is in the table as the control — a different job (find files, not
search contents) and it ranks second everywhere, which is how you know the
axes are measuring adoption and not fashion.

**Overturned by** ripgrep's `scorecard` at 4.7 being the weakest cell here; a
`depsdev` gap of a year, or an `osv` advisory, moves this to `ugrep`, which is
the only entrant with comparable distro coverage and an active maintainer.

**Route gotcha** `repology fd` returns 0 — the project is `fd-find` there. A
zero from repology means the name is wrong far more often than it means the
tool is unpackaged.

### web search from a script, no API key

**Pick** `marginalia` for the non-commercial web, `ddg` as the mainstream
fallback, your own SearXNG when volume matters. **Beats** every public SearXNG
instance, Brave, Exa, Tavily, grep.app, Sourcegraph.

| endpoint | result |
|---|---|
| `api.marginalia.nu/public/search/<q>` | 200, JSON, no key, CC-BY-NC-SA |
| `lite.duckduckgo.com/lite/` | 200, HTML — 10 result links parsed |
| 8 public SearXNG instances from `searx.space` | `429`, or HTML in answer to `format=json` |
| Brave · Exa · Tavily | key and billing |
| `grep.app/api/search` | `429` on the first anonymous call |
| `sourcegraph.com/.api/search/stream` | 200, `matchCount: 0` — public code search needs a token |

**Why** the free tier of web search has closed almost completely; what is left
is one index that is deliberately non-commercial and one HTML endpoint that
tolerates a scraper. Both are fine at a handful of queries an hour and neither
survives a loop. Volume means running SearXNG yourself, which is a container
and a one-line settings change.

**Overturned by** a public instance answering `format=json` twice in a week —
re-run the `searx.space` filter before assuming it is still closed.

### star momentum for a repo we do not own

**Pick** our own snapshots — `scout.sh sweep` daily, `scout.sh delta` to read
them. **Beats** the stargazers API, star-history, OSS Insight.

| source | result |
|---|---|
| `api.github.com/repos/*/stargazers` | restricted since 2026-06-30 for repos you do not own |
| `api.star-history.com` | 200, but renders an SVG chart — a picture, not a series |
| `api.ossinsight.io/v1/trends/repos/` | 200, engagement score fusing stars, forks, PRs, pushes |
| `snapshots/*.tsv` + `scout.sh delta` | a real series, from the day we started taking one |

**Why** every hosted timeline for a repo we do not own is gone or is a
rendering. The only series that exists is the one we accumulate, which costs
one search call per bucket per day and answers immediately about anything in
`buckets.txt` — and nothing about what is not. OSS Insight fills exactly that
hole: it is a discovery channel for repos we never bucketed, and its tail is
30-star projects, so it is read as a candidate list and never as a ranking.

**Overturned by** GitHub restoring the stargazers timeline, which would make
the snapshot directory redundant for anything we did not already sample.

### a page as text an agent can hold

**Pick** `r.jina.ai`. **Beats** nothing yet — one axis, so this is `weak`.

| endpoint | result |
|---|---|
| `r.jina.ai/<url>` | 200, markdown with title and published date, no key at low volume |

**Why** it is the only extractor measured, and it worked on the first call
without a key. That is a reason to use it today and not a finding.

**Overturned by** the first head-to-head against a local extractor
(`trafilatura`, `readability`) on a page with a paywall, a cookie wall and a
JS-rendered body — recorded in [Open](#open) as the next measurement.

## Open

Jobs asked, not yet measured. A row leaves this table only as a finding above.

| job | axes to measure on | why it matters |
|---|---|---|
| local vs hosted markdown extraction | fidelity on paywall / cookie-wall / JS-rendered pages | the `read` route is a network dependency in every crawl |
| polite bulk fetching of a domain | crawl-delay compliance, resume, cache | `crawl` and `wayback` answer about the past, nothing fetches the present in bulk |
| embedding model for local retrieval | `models` downloads, licence, dimensions, RAM | `models` ranks by downloads, which is the weakest axis in this file |
| TUI framework, Rust | `gh` stars · `crates` recent downloads · `depsdev` cadence | picked once, lived with for years |
| MCP servers worth wiring in | `mcp` census · `gh` stars · `scorecard` | the registry is self-serve, so it is unfiltered by construction |

## Maintenance

- Write the finding when the measurement is made, not when the tool is
  adopted. The numbers are perishable and the reasoning is not.
- Re-run `route.sh check` before adding a row. A finding produced by a route
  that has since died is deleted with the route.
- Six months old is re-measured or deleted. There is no third option.
- A pick that changes gets its row rewritten in place, with the new date — the
  argument for the old pick lives in version control, never in this file.
