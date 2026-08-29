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
| @TODO.md | the open loop |
| @.gitignore | what git leaves alone |

## `references/` — read

| anchor | is |
|---|---|
| @references/files.md | this manifest — every tracked file, one row |
| @references/language.md | how every document is written |
| @references/install.md | what the system is, and how to install it for any agent |
| @references/settings.md | board knobs |
| @references/memo.md | how a decision is recorded |
| @references/workflow.md | how a job is done — the two file shapes, the steps grammar, the report section |
| @references/report.md | the board written for a person |
| @references/drill.md | how to ask |
| @references/system.md | drop-in instructions block for `AGENTS.md` |

### `references/parts/` — the workflow, one part per step

| anchor | is |
|---|---|
| @references/parts/loop.md | the seven steps, in order |
| @references/parts/board.md | the layout the scan walks |
| @references/parts/round.md | `prds/.round.md` — what the session holds, across a compaction |
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
| @resources/board/serve.py | the live service |
| @resources/board/plan.py | read + order the board |
| @resources/board/render.py | the page — markup, and the arithmetic behind it |
| @resources/board/view.css | the page's stylesheet, inlined at render |
| @resources/board/view.js | the page's script, inlined at render |
| @resources/board/viewtest.js | the view's gate — a rendered page in a real browser |
| @resources/board/lit-core.min.js | Lit 3, vendored — the page's component base |
| @resources/board/edit.py | the writers — one line at a time |
| @resources/board/collect.py | `collect` — verify, commit the footprint, `done`, one call |
| @resources/board/brief.py | `brief` — a worker's or a consultant's brief, one command's output; the text is the marker blocks of workers.md, this fills them and holds no copy |
| @resources/board/specs.py | `specced` and `refine` — the two transitions a spec set decides |
| @resources/board/init.py | `init` and `settings` — a board after one command, no question; one key of settings.md |
| @resources/board/transitions.py | the eight transition commands — the one writer of `state:` |
| @resources/board/example/ | the example board — eight PRDs, one per band; copied by `plan.py example`, never run in place |

## `skills/` — one file per skill

Frontmatter, and a body that points into `references/`. One per feature: a
scope a person or an agent **invokes** gets a skill, a scope the loop **reads
mid-task** stays a reference reached through `@@`. The file name is the
command, and @references/install.md is the naming rule and the install.

| anchor | is | scope |
|---|---|---|
| @skills/pearde.md | the round, and every handle that moves a PRD | `@@loop` |
| @skills/pearde-drill.md | asking until the request is a contract | `@@drill` |
| @skills/pearde-memo.md | recording a decision, and checking the record | `@@memos` |
| @skills/pearde-view.md | the timeline, the order, and editing through it | `@@view` |
| @skills/pearde-workflow.md | how a kind of job is done, and improved on every run | `@@workflows` |
| @skills/pearde-report.md | the board written for a person, one rolling state | `@@report` |
| @skills/pearde-master.md | one plan across several repositories | `@@master` |
| @skills/pearde-doctor.md | a broken install against an absent one | `@@doctor` |
| @skills/pearde-persona.md | who is working, and switching for the round | `@@personas` |
| @skills/pearde-persona-ask.md | one problem, one colleague, nothing written | `@@consult` |
| @skills/pearde-persona-create.md | composing one for a field the roster misses | `@@personas` |
| @skills/pearde-scout.md | ranked discovery, the route index, and the quality gates | `@@scout` |

### `resources/scout/` — a self-contained tool

Nothing outside it links in past `@@scout`. Its docs ship with it.

| anchor | is |
|---|---|
| @resources/scout/README.md | the scout manual — what @skills/pearde-scout.md is a door to |
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
