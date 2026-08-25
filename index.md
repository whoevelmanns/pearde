# Index

| write | means | resolves to |
|---|---|---|
| `@<path>` | **one file** — the real path from the repo root with `@` in front | itself. Nothing to look up |
| `@@<keyword>` | **one scope** — everything you must read to understand a feature | its row in [Keywords](#keywords) |

`@@` names a row in this index, not a path on disk. No keyword is a directory.

Board paths (`prds/…`) are neither. They address a board, not this skill.

**Where a file goes.** Markdown that someone reads lives under `references/`.
Anything executed — a script, a tool, its config and its data — lives under
`resources/`, whole. A tool's own README ships inside the tool.

**Every skill is a folder under `skills/`**, holding a `SKILL.md` and nothing
that points outside itself. A skill that shares this repo's documents carries
committed symlinks — `references`, `resources`, `README.md`, `index.md` —
relative to its real location, so `@<path>` resolves the same whether the
folder is read here or through a link in an agent's skills directory. A skill
that shares nothing, like `skills/scout/`, ships whole and links nowhere.
@references/targets.md is where the folders go, per agent.

**When a file moves or is added**: update its row in [Files](#files), then
every [Keywords](#keywords) row whose scope it changed. Nothing else points at
it.

## Keywords

A file appears in every scope it belongs to. The first anchor in a row
explains the rest.

| keyword | is | read |
|---|---|---|
| `@@loop` | the round, start to finish | @references/parts/loop.md · @references/parts/roles.md · @references/parts/order.md · @references/parts/states.md · @references/parts/commits.md · @references/parts/progress.md |
| `@@board` | what the scan walks and what it parses | @references/parts/board.md · @references/parts/contract.md · @references/parts/states.md · @references/templates/prd.md · @references/settings.md |
| `@@states` | the nine states and what moves a PRD between them | @references/parts/states.md · @references/parts/contract.md · @references/parts/commits.md |
| `@@order` | what runs next, and why no axis is a clock | @references/parts/order.md · @references/parts/derived.md · @resources/view/plan.py |
| `@@workers` | dispatching an analyst or an implementer | @references/parts/workers.md · @references/parts/roles.md · @references/parts/solo.md · @references/parts/personas.md · @references/language.md |
| `@@specs` | one implementable unit, written and read | @references/templates/spec.md · @references/parts/workers.md · @references/parts/contract.md |
| `@@personas` | who is working, how one is chosen, consulted or made | @references/parts/personas.md · @references/personas/INDEX.md · @references/personas/engineer.md · @references/personas/designer.md · @references/personas/mentor.md · @references/personas/skeptic.md · @references/parts/roles.md · @references/parts/workers.md · @references/parts/progress.md |
| `@@derived` | work the board found, and its tripwire | @references/parts/derived.md · @references/parts/order.md · @references/templates/prd.md |
| `@@commits` | one PRD, one commit, on the transition that lands it | @references/parts/commits.md · @references/parts/states.md |
| `@@memos` | recording a decision and checking it | @references/memo.md · @references/parts/memos.md · @references/templates/memo.md · @resources/memos.py |
| `@@drill` | asking until the request is a contract | @references/drill.md · @references/templates/prd.md · @references/parts/handles.md |
| `@@handles` | every command the board answers to | @references/parts/handles.md · @references/parts/loop.md · @references/drill.md |
| `@@view` | the live view — service, plan, render, writers | @references/parts/view.md · @resources/view/serve.py · @resources/view/plan.py · @resources/view/render.py · @resources/view/view.css · @resources/view/view.js · @resources/view/edit.py |
| `@@progress` | the line printed on every state change | @references/parts/progress.md · @resources/statusline.sh · @references/parts/states.md |
| `@@statusline` | the numbers rendered continuously in the terminal | @resources/statusline.sh · @references/targets.md · @references/parts/progress.md · @references/parts/personas.md · @references/install.md |
| `@@install` | putting every skill where each agent finds it | @references/install.md · @references/targets.md · @resources/install.sh · @references/system.md · @references/parts/doctor.md · @resources/doctor.sh |
| `@@targets` | the agents this repo knows how to wire, and the row that is all it knows | @references/targets.md · @resources/targets.py · @resources/install.sh · @references/system.md |
| `@@doctor` | telling a broken install from an absent one | @references/parts/doctor.md · @resources/doctor.sh · @resources/index.py · @resources/targets.py · @references/install.md |
| `@@master` | one plan across several repos | @references/parts/master.md · @references/settings.md · @references/parts/board.md |
| `@@settings` | every board-wide knob | @references/settings.md · @references/parts/contract.md |
| `@@language` | how everything on the board is written | @references/language.md · @references/templates/prd.md · @references/templates/spec.md · @references/templates/memo.md |
| `@@templates` | the three files a handle writes from | @references/templates/prd.md · @references/templates/spec.md · @references/templates/memo.md |
| `@@index` | addressing itself — the syntaxes, the scopes, the check | @index.md · @resources/index.py · @README.md · @references/language.md |
| `@@scout` | the star-discovery tool, whole | @skills/scout/README.md · @skills/scout/SKILL.md · @skills/scout/scout.sh · @skills/scout/buckets.txt · @skills/scout/reading-list.md |

## Files

Every tracked file, one row.

### Entry points

| anchor | is |
|---|---|
| @README.md | the manual — board, states, loop, briefs, view |
| @index.md | this index — the `@` and `@@` syntaxes, the scopes, the files |
| @TODO.md | the open loop |
| @.gitignore | what git leaves alone |

This repo runs its own board, so `@resources/install.sh` has written its block
into the instructions files here too. Each is the user's file with one block
in it, between markers — @references/targets.md says which agent reads which.

| anchor | is |
|---|---|
| @AGENTS.md | the block, for the agents that read `AGENTS.md` |
| @CLAUDE.md | the block, for the agent that reads `CLAUDE.md` |
| @GEMINI.md | the block, for the agent that reads `GEMINI.md` |

### `references/` — read

| anchor | is |
|---|---|
| @references/language.md | how every document is written |
| @references/install.md | what installed means |
| @references/targets.md | one row per agent — where its skills go, and what it reads |
| @references/settings.md | board knobs |
| @references/memo.md | how a decision is recorded |
| @references/drill.md | how to ask |
| @references/system.md | drop-in instructions block for `AGENTS.md` |

#### `references/parts/` — the workflow, one part per step

| anchor | is |
|---|---|
| @references/parts/loop.md | the seven steps, in order |
| @references/parts/board.md | the layout the scan walks |
| @references/parts/contract.md | the frontmatter keys, and their defaults |
| @references/parts/states.md | the nine states, and what a tenth means |
| @references/parts/order.md | the three axes that pick what runs next |
| @references/parts/derived.md | work the board found, and its tripwire |
| @references/parts/roles.md | orchestrator, analyst, implementer, consultant |
| @references/parts/workers.md | the exact brief handed to each |
| @references/parts/solo.md | the same loop without parallel workers |
| @references/parts/personas.md | how a persona is picked, switched and consulted |
| @references/parts/commits.md | one PRD, one commit |
| @references/parts/memos.md | what was decided, and what it beat |
| @references/parts/progress.md | the state-change line and the status line |
| @references/parts/handles.md | every command the board answers to |
| @references/parts/view.md | the live view at `127.0.0.1:8443` |
| @references/parts/doctor.md | broken install vs absent one |
| @references/parts/master.md | one plan across several repos |

#### `references/personas/` — who works

| anchor | is |
|---|---|
| @references/personas/INDEX.md | the roster, and how `persona create` builds a new one |
| @references/personas/engineer.md | Mara Vogt — the default, engineering generalist |
| @references/personas/designer.md | Ines Calder — product/design engineer |
| @references/personas/mentor.md | Tomas Berg — teaching engineer |
| @references/personas/skeptic.md | Nadia Ross — adversarial reviewer |

#### `references/templates/` — what a handle writes from

| anchor | is |
|---|---|
| @references/templates/prd.md | one PRD |
| @references/templates/spec.md | one implementable unit |
| @references/templates/memo.md | one decision record |

### `resources/` — run

| anchor | is |
|---|---|
| @resources/install.sh | the bootstrap — link every skill into every agent |
| @resources/doctor.sh | install check + repair |
| @resources/statusline.sh | continuous progress numbers |
| @resources/memos.py | read + check memos — the only reader of that format |
| @resources/index.py | read + check this index — the only reader of that format |
| @resources/targets.py | read @references/targets.md — the only reader of that format |
| @resources/view/serve.py | the live service |
| @resources/view/plan.py | read + order the board |
| @resources/view/render.py | the page — markup, and the arithmetic behind it |
| @resources/view/view.css | the page's stylesheet, inlined at render |
| @resources/view/view.js | the page's script, inlined at render |
| @resources/view/edit.py | the writers — one line at a time |

### `skills/` — one folder per skill

Each is what an agent is pointed at. @references/targets.md says where.

| anchor | is |
|---|---|
| @skills/pearde/SKILL.md | the entry point that makes `pearde` invocable |
| @skills/pearde/README.md | → `../../README.md` |
| @skills/pearde/index.md | → `../../index.md` |
| @skills/pearde/references | → `../../references` |
| @skills/pearde/resources | → `../../resources` |

#### `skills/scout/` — a self-contained skill

Nothing outside it links in past `@@scout`. Its docs ship with it.

| anchor | is |
|---|---|
| @skills/scout/README.md | the scout manual |
| @skills/scout/SKILL.md | scout's entry point |
| @skills/scout/scout.sh | sweep / delta / trending |
| @skills/scout/toolscout.sh | one-off dependency ranker |
| @skills/scout/buckets.txt | the taxonomy — the knob |
| @skills/scout/reading-list.md | the curated, mechanism-mapped list |
| @skills/scout/snapshots/2026-08-25.tsv | one day's star counts |
| @skills/scout/templates/_typos.toml | typos gate config |
| @skills/scout/templates/deny.toml | cargo-deny gate config |
| @skills/scout/templates/dependabot.yml | dependency updates |
| @skills/scout/templates/quality.yml | the quality gate workflow |
| @skills/scout/templates/scout.yml | the sweep in CI |
