# Files

Every tracked file, one row. @resources/index.py reads this and @index.md
together: a file on disk with no row here is a map that is incomplete, and a
row naming nothing is a map that points at nothing.

Nothing here answers a question about the work — @index.md's Keywords table
does. Read this when you add a file, move one, or are told the index drifted.

**Adding a file**: write its row here, then every Keywords row in @index.md
whose scope it changed. Nothing else points at it.

## Entry points

| anchor | is |
|---|---|
| @SKILL.md | the installer — invocable before the skills are, retired once they exist |
| @README.md | the manual — board, states, loop, briefs, view |
| @index.md | the map — the `@` and `@@` syntaxes, and every scope |
| @.gitignore | what git leaves alone |

## `references/agents/` — dispatch

| file | what it is |
|------|------------|
| @references/agents/pearde-analyst.md | the analyst worker type — model and return contract |
| @references/agents/pearde-implementer.md | the implementer worker type — model and return contract |

## `references/` — read

| anchor | is |
|---|---|
| @references/archive.md | how a finished PRD leaves `.pearde/prds/` — the flat `.pearde/prds/archive/` shape, and why `scan` already ignores it |
| @references/files.md | this manifest — every tracked file, one row |
| @references/language.md | how every document is written |
| @references/install.md | what the system is, and how to install it for any agent |
| @references/settings.md | board knobs |
| @references/memo.md | how a decision is recorded |
| @references/workflow.md | how a job is done — the two file shapes, the steps grammar, the report section |
| @references/report.md | the board written for a person |
| @references/drill.md | how to ask |
| @references/graph.md | the knowledge-graph feature — graphify rounds, the ollama backend, the Obsidian vault |
| @references/knowledge.md | the research layer — sources, conclusions, the ask→capture→conclude loop, the tool behind it |
| @references/system.md | drop-in instructions block for `AGENTS.md` |
| @references/plugins.md | the curated plugin list — what to install alongside pearde, what not to, and why |
| @references/obsidian.md | the vault and its native access — REST + MCP from the same port, the two required plugins, how a round uses them |

### `references/parts/` — the workflow, one part per step

| anchor | is |
|---|---|
| @references/parts/loop.md | the seven steps, in order |
| @references/parts/board.md | the layout the scan walks |
| @references/parts/round.md | `.pearde/.state/round.md` — what the session holds, across a compaction |
| @references/parts/guard.md | the loop's rules as a hook that refuses the waste |
| @references/parts/contract.md | the frontmatter keys, and their defaults |
| @references/parts/states.md | the nine states, and what a tenth means |
| @references/parts/order.md | the three axes that pick what runs next |
| @references/parts/derived.md | work the board found, and its tripwire |
| @references/parts/roles.md | orchestrator, analyst, implementer, consultant |
| @references/parts/workers.md | the exact brief handed to each |
| @references/parts/solo.md | the same loop without parallel workers |
| @references/parts/personas.md | who works the session, and how one is picked |
| @references/parts/consult.md | putting one problem to one persona, mid-round |
| @references/parts/commits.md | one PRD, one commit |
| @references/parts/memos.md | what was decided, and what it beat |
| @references/parts/workflows.md | the how, accumulated — the folder on one page |
| @references/parts/progress.md | the line printed on every state change |
| @references/parts/statusline.md | the same numbers, continuously, for a person |
| @references/parts/handles.md | every command the board answers to |
| @references/parts/view.md | the live view at `127.0.0.1:8443` |
| @references/parts/doctor.md | broken install vs absent one |
| @references/parts/master.md | one plan across several repos |

### `references/personas/` — who works

| anchor | is |
|---|---|
| @references/personas/INDEX.md | the roster, and how `persona create` builds a new one |
| @references/personas/engineer.md | Mara Vogt — the default, engineering generalist |
| @references/personas/designer.md | Ines Calder — product/design engineer |
| @references/personas/mentor.md | Tomas Berg — teaching engineer |
| @references/personas/skeptic.md | Nadia Ross — adversarial reviewer |

### `references/templates/` — what a handle writes from

| anchor | is |
|---|---|
| @references/templates/prd.md | one PRD |
| @references/templates/spec.md | one implementable unit |
| @references/templates/memo.md | one decision record |
| @references/templates/atomic.md | one unit of work |
| @references/templates/workflow.md | one ordered route over atomics |
| @references/templates/report.md | the one rolling state, for a person |
| @references/templates/vision.md | one board's destination — the vision, its terminals, its edges |

## `resources/` — run

| anchor | is |
|---|---|
| @resources/pearde.py | the one command — a dispatcher over every script; discovers `COMMANDS` in `resources/board/*.py`; `help` from docstrings |
| @resources/install.sh | build one skill folder of links per file in `skills/` |
| @resources/doctor.sh | install check + repair |
| @resources/guard.py | the PreToolUse/PostToolUse hook that enforces the loop |
| @resources/statusline.sh | continuous progress numbers |
| @resources/memos.py | read + check memos — the only reader of that format |
| @resources/workflows.py | read + check the workflow library, and brief one — the only reader of that format |
| @resources/index.py | read + check the map — the only reader of that format |
| @resources/questions.py | read + check a PRD's question round — the only reader of that format |
| @resources/graph/graph.sh | graphify rounds — extract, update, query, path, explain, god-nodes, vault open |
| @resources/knowledge.py | the research loop — query, enqueue, remember, conclude, relink, wiki, dashboard, doctor — over `.pearde/wiki/` |
| @resources/board/serve.py | the live service |
| @resources/board/plan.py | read + order the board |
| @resources/board/render.py | the page — markup, and the arithmetic behind it |
| @resources/board/view.css | the page's stylesheet, inlined at render |
| @resources/board/view.js | the page's script, inlined at render |
| @resources/board/viewtest.js | the view's gate — a rendered page in a real browser |
| @resources/board/hotreload-test.js | the view's hot-reload gate — one live page, a view source moved under it (`node hotreload-test.js <served-board-url>`) |
| @resources/board/adapters/claude.json | the Start button's default launch target — one JSON per adapter (`{"name","command","prompt"}`, optional `"plugins"` list of suggestions), read live by serve.py; doctor reports missing ones |
| @resources/board/lit-core.min.js | Lit 3, vendored — the page's component base |
| @resources/board/edit.py | the writers — one line at a time |
| @resources/board/collect.py | `collect` — verify, commit the footprint, `done`, one call |
| @resources/board/orphans.py | `orphans` — every done PRD whose footprint never reached the branch that holds it; per-branch, never `git log --all`, reads only |
| @resources/board/brief.py | `brief` — a worker's or a consultant's brief, one command's output; the text is the marker blocks of workers.md, this fills them and holds no copy |
| @resources/board/transitions.py | the eight transition commands — the one writer of `state:` |
| @resources/board/specs.py | `specced` and `refine` — the two transitions a spec set decides |
| @resources/board/init.py | `init` and `settings` — a board after one command, no question; one key of settings.md; seeds the Obsidian vault (`.obsidian/` — dataview + local-rest-api copied from the preset the install fetched, a bundle the install never fetched named rather than skipped, fresh REST key minted at `.pearde/wiki/.obsidian-api-key`) |
| @resources/board/example/ | the example board — eight PRDs, one per band; copied by `plan.py example`, never run in place |
| @resources/board/obsidian/ | the vault preset — `.obsidian` root files (app, graph colors, community/core plugin lists, appearance) and the two required plugins' settings; copied by `init` to any new board, an existing install wins. The plugin bundles (`main.js`, `manifest.json`, `styles.css`) are **not** in the repo: `install.sh` fetches them at pinned versions and `.gitignore` holds them out |

## `references/skills/` — one file per skill

Frontmatter, and a body that points into `references/`. One per feature: a
scope a person or an agent **invokes** gets a skill, a scope the loop **reads
mid-task** stays a reference reached through `@@`. The file name is the
command, and @references/install.md is the naming rule and the install.

| anchor | is | scope |
|---|---|---|
| @references/skills/pearde.md | the round, and every handle that moves a PRD | `@@loop` |
| @references/skills/pearde-drill.md | asking until the request is a contract | `@@drill` |
| @references/skills/pearde-memo.md | recording a decision, and checking the record | `@@memos` |
| @references/skills/pearde-view.md | the timeline, the order, and editing through it | `@@view` |
| @references/skills/pearde-report.md | the board written for a person, one rolling state | `@@report` |
| @references/skills/pearde-master.md | one plan across several repositories | `@@master` |
| @references/skills/pearde-doctor.md | a broken install against an absent one | `@@doctor` |
| @references/skills/pearde-persona.md | who is working, and switching for the round | `@@personas` |
| @references/skills/pearde-persona-ask.md | one problem, one colleague, nothing written | `@@consult` |
| @references/skills/pearde-persona-create.md | composing one for a field the roster misses | `@@personas` |
| @references/skills/pearde-scout.md | ranked discovery, the route index, and the quality gates | `@@scout` |
| @references/skills/pearde-workflow.md | how a kind of job is done, and improved on every run | `@@workflows` |
| @references/skills/pearde-graph.md | knowledge-graph rounds over any folder, Obsidian vault out | `@@graph` |
| @references/skills/pearde-knowledge.md | the research layer — query, capture, conclude, link | `@@knowledge` |

### `resources/board/knowledge/` — the layer's seed template, not yet wired to `init`

Not the same thing as @resources/board/obsidian/: that preset is the
`.obsidian` app config (dataview + local-rest-api), copied by `init.py`'s
`write_obsidian` into `<dir>/.obsidian` on every fresh board. This folder is
the knowledge-layer's *content* seed — dashboard, workflow config, empty
indexes — meant for a new board's `.pearde/wiki/`. As of this writing
`init.py` never references `resources/board/knowledge/` at all: no
`write_knowledge` step exists, and `resources/knowledge.py`'s `Store` reads
and writes `.pearde/wiki/` directly without ever copying this preset into
it. So today a fresh `.pearde/wiki/` starts from whatever `knowledge.py`
creates on first use, not from this template — these files are a seed
nothing plants. Keep them (a future `init` step is the obvious fix, not
deletion), but don't read the row below as describing current `init`
behavior.

| anchor | is |
|---|---|
| @resources/board/knowledge/ | template for a new board's `.pearde/wiki/` — dashboard, workflow, indexes, the empty pending/graphs/absorbed scaffolds; not currently copied by any command (see note above) |
| @resources/board/knowledge/Dashboard.md | the dashboard template — Dataview views, vault-relative |
| @resources/board/knowledge/WORKFLOW.md | the configuration template — focus, rules, routing |
| @resources/board/knowledge/_index.md | the conclusions index template |
| @resources/board/knowledge/conclusions/_index.md | the conclusions index, under conclusions/ |
| @resources/board/knowledge/sources/_index.md | the sources index template |
| @resources/board/knowledge/sources/.absorbed/_index.md | the absorbed-sources marker |
| @resources/board/knowledge/.graphifyignore | the extract-scope template |

### `.pearde/wiki/` — data, not source

One folder, gitignored, the layer's whole: notes, graph, wiki, and its own
Obsidian vault. No rows — the folder is machine-local output of
@resources/knowledge.py, the row above is its intended contract (see the
note there — not yet how a fresh board actually gets it).

### `resources/scout/` — a self-contained tool

Nothing outside it links in past `@@scout`. Its docs ship with it.

| anchor | is |
|---|---|
| @resources/scout/README.md | the scout manual — what @references/skills/pearde-scout.md is a door to |
| @resources/scout/scout.sh | sweep / delta / trending |
| @resources/scout/toolscout.sh | one-off dependency ranker |
| @resources/scout/route.sh | call one ranking page by id — reader of the route index |
| @resources/scout/routes.md | index one — every page a ranking comes from |
| @resources/scout/findings.md | index two — what won, on which axis, when |
| @resources/scout/buckets.txt | the taxonomy — the knob |
| @resources/scout/reading-list.md | the curated, mechanism-mapped list |
| @resources/scout/snapshots/ | the sweep's dated star counts, one row for the directory |
| @resources/scout/templates/_typos.toml | typos gate config |
| @resources/scout/templates/deny.toml | cargo-deny gate config |
| @resources/scout/templates/dependabot.yml | dependency updates |
| @resources/scout/templates/quality.yml | the quality gate workflow |
| @resources/scout/templates/scout.yml | the sweep in CI |
