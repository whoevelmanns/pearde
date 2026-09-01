# scout — find what is worth studying, ranking, or wiring in

Four layers, each answering a different question:

1. **discover** — what is out there, ranked (`scout.sh sweep|delta|trending`,
   `toolscout.sh`)
2. **ask** — one job, answered off many ranking pages and written down
   (`route.sh` + `routes.md` → `findings.md`)
3. **curate** — what is worth *reading*, mapped to what it teaches a specific
   tree (`reading-list.md`)
4. **wire** — the passive quality gates that keep the trees honest
   (`quality.yml` + the configs, sccache)

Stars are the discovery layer, never the verdict. The whole point of the
curated layer is that a 74k-star case-study corpus beats a 243k-star hype
repo for *improving the product* — and that a 10k-star archived TUI library
is a worse dependency than a 3k-star active one.

## Layout

| path | what |
|---|---|
| `scout.sh` | sweep/delta/trending — the daily measurement loop |
| `toolscout.sh` | one-off dependency ranker: stars + what stars hide |
| `route.sh` | call one ranking page by id — reader of `routes.md`, holds no list |
| `routes.md` | **index one** — every page a ranking comes from, one shell block each |
| `findings.md` | **index two** — what won, on which axis, when |
| `buckets.txt` | the taxonomy — `name<TAB>query` per line; **the knob** |
| `snapshots/` | star counts, one TSV per day, capped at the 90 most recent (`SCOUT_SNAP_KEEP`) |
| `reading-list.md` | the curated, mechanism-mapped list |
| `templates/` | quality-gate configs + workflow for wiring a new tree |
| `SKILL.md` | this skill's entry |
| `README.md` | this file |

## Commands

### `scout.sh sweep`
Snapshot every bucket in `buckets.txt` into `snapshots/<date>.tsv` (one GitHub
search call per bucket, sort=stars, top N). The **first** sweep is a baseline;
every sweep after it is a measurement. Run it daily on a local cron and the
delta accumulates while nobody looks — no cloud needed. A GH Actions template
(`templates/scout.yml`) exists for a repo that chooses to run the sweep in CI.
Each sweep also prunes `snapshots/` down to the 90 most recent TSVs (override
with `SCOUT_SNAP_KEEP`) — enough daily history for any `delta [days]` window
this doc mentions, plus slack for gaps in the cron, without growing forever.

### `scout.sh delta [days]`
What gained the most stars since ~N days ago, computed by **diffing our own
snapshots** — the stargazers API is restricted as of 2026-06-30, so this is
the only way left. `NEW` marks a repo
that entered a bucket's top-N, which is the useful signal (it displaced
established work).

### `scout.sh trending [daily|weekly|monthly]`
Scrapes GitHub's own trending as a discovery channel for buckets you never
thought to define. The response is layout-coupled HTML; a row misalignment
fails loudly, not silently.

### `toolscout.sh '<query>'`
One-off ranker for a specific choice: `topic:tui language:rust stars:>1000`.
Stars ranked, plus `STATE` — days since push, ARCHIVED, issue load, license —
so the dead-3-years 10k-star repo reads as what it is.

### `route.sh list | <id> [query] | check`
Forty-three ranking pages beyond GitHub, one shell block each in `routes.md`,
addressed by id: `hn`, `brew`, `arch`, `popcon`, `crates`, `scorecard`, `osv`,
`cht`, `marginalia`, `wayback`, `crawl`, `mcp`, `openalex`. `route.sh check`
runs every one against its own example and prints `ok` or `DEAD` — the file
cannot claim a route works without the claim being runnable.

Adding a route is editing `routes.md`; `route.sh` parses it and holds no list.

## The research loop — one job, two indices

`routes.md` is where numbers come from. `findings.md` is what the numbers
decided. The loop between them:

1. **Phrase the job as a choice.** "Recursive search over a source tree", not
   "is ripgrep good". If nothing can be rejected, there is nothing to measure.
2. **Pick routes by axis, at least two.** Attention (`hn`, `lobsters`),
   installs (`brew`, `arch`, `popcon`, `crates`, `npm`), stars (`gh`,
   `codeberg`), hygiene (`scorecard`, `osv`, `depsdev`). Axes that disagree are
   the finding — a tool with distro breadth and no installs is abandoned, and
   only two axes together say so.
3. **Run them.** `route.sh <id> <query>`, every candidate through every axis.
4. **Write the row.** Pick, what it beat, the numbers with their routes, the
   date, and what would overturn it. A pick on one axis is marked `weak`.
5. **Anything unanswered goes to `## Open`** in `findings.md` — a queue, so the
   next sweep knows what was already asked.

Six months is the expiry. A finding older than that is re-measured or deleted;
there is no third option.

## The reading list discipline

A repo earns a row in `reading-list.md` only by answering, in writing, *which
file in which tree changes because we read this*. That file carries the
genres, the entries and the anti-list.

## The quality layer — "accelerate quality by just using it"

Every quality gate below is verified green on the family's trees as of
2026-08-25, then wired into CI so it runs itself. The weekly schedule is the
point: a new CVE against a locked dep turns the tab red on Monday with no
human action.

- **typos** (`_typos.toml`) — 2,000+ md files where the prose IS the spec. A
  typo in a frontmatter key is a silent behaviour change. The config is the
  record of deliberate spellings, not an ad-hoc suppression.
- **gitleaks** (`.gitleaks.toml`) — full-history secret scan. The allowlist is
  fixtures asserting on fake keys, each with a recorded reason.
- **cargo-deny** (`deny.toml`) — RustSec advisories hard-gated. The ignore
  list is the audited unmaintained-transitive set, by ID, with reasoning. A
  NEW advisory fails the job. 0.20.x has no `unmaintained` severity key —
  ignore by ID with `unused-ignored-advisory = "allow"`.
- **cargo-machete** — unused deps caught as they appear.
- **sccache** — one shared compile cache across the workspaces. The
  precondition (identical toolchain pins) is met in this family; install and
  add `rustc-wrapper = "sccache"` to `~/.cargo/config.toml`.

Wire a new tree by copying `templates/` — `quality.yml`, `dependabot.yml`,
and the three config files — then adjust the deny.toml ignore list to that
tree's actual advisories.

## Maintenance

- Edit `buckets.txt` and `routes.md`, not the scripts. A bucket is
  `name<TAB>query`; a route is a `### id` heading, four bullets and one `sh`
  block.
- `SCOUT_MAILTO=you@example.com` puts every polite-pool route in the fast tier.
  Without it ecosyste.ms answers `402 Payment Required` and the registries
  throttle.
- `route.sh check` before writing a finding. A route that dies twice moves to
  the dead-ends table in `routes.md` with its observed status, and every
  finding that stood on it goes with it.
- `pushed:` filters in queries compose with `stars:>`; keep a stars floor or
  the tail is noise.
- The `delta` output rewards hype by construction — a repo gaining 10k
  stars/week is being *talked about*, orthogonal to whether it's good. Treat
  it as a reading list, never a shortlist.
- The scout's activity heuristic flags long-quiet but *finished* tools
  (hyperfine, tokei) as "slow". Right to flag, wrong about what the flag
  means.
