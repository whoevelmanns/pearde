# Index

| write | means | resolves to |
|---|---|---|
| `@<path>` | **one file** — the real path from the repo root with `@` in front | itself. Nothing to look up |
| `@@<keyword>` | **one scope** — everything you must read to understand a feature | its row in [Keywords](#keywords) |

`@@` names a row in this index, not a path on disk. No keyword is a directory.

Board paths (`prds/…`) are neither. They address a board, not this skill.

**A scope is what a feature is made of, not a reading list.** Read the one
file that answers the question in front of you — the first anchor in a row is
that file, and the rest are what it sends you to. A round that opens a whole
scope pays for the manual again after every compaction, and pays for it in the
window it needs for the work.

**Where a file goes.** Markdown that someone reads lives under `references/`.
Anything executed — a script, a tool, its config and its data — lives under
`resources/`, whole. A tool's own README ships inside the tool.

**Every skill is one file under `skills/`** — frontmatter that decides when
it fires, and a body that points into `references/` and stops. The knowledge
is never in the skill. What a skill *runs* lives under `resources/`, one
folder per skill where there is one: @resources/board/ and @resources/scout/.

Installing turns each file into a folder of links elsewhere. Nothing in this
repo moves. @references/install.md is the whole of it, and it names no agent
— which directory to build in is the reader's to work out.

**When a file moves or is added**: update its row in [Files](#files), then
every [Keywords](#keywords) row whose scope it changed. Nothing else points at
it.

## Keywords

A file appears in every scope it belongs to. The first anchor in a row
explains the rest.

| keyword | is | read |
|---|---|---|
| `@@loop` | the round, start to finish | @references/parts/loop.md · @references/parts/round.md · @references/parts/states.md · @references/parts/commits.md · @references/parts/progress.md · @references/parts/order.md · @references/parts/roles.md |
| `@@board` | what the scan walks and what it parses | @references/parts/board.md · @references/parts/round.md · @resources/board/plan.py · @references/parts/contract.md · @references/parts/states.md · @references/templates/prd.md · @references/settings.md |
| `@@states` | the nine states and what moves a PRD between them | @references/parts/states.md · @references/parts/contract.md · @references/parts/commits.md |
| `@@order` | what runs next, and why no axis is a clock | @references/parts/order.md · @references/parts/derived.md · @resources/board/plan.py |
| `@@workers` | dispatching an analyst or an implementer | @references/parts/workers.md · @references/parts/roles.md · @references/parts/solo.md · @references/language.md |
| `@@specs` | one implementable unit, written and read | @references/templates/spec.md · @references/parts/workers.md · @references/parts/contract.md |
| `@@personas` | who works the **session**, and how one is chosen or made — the roster is @references/personas/INDEX.md, and a persona file is read only when it is worn | @references/parts/personas.md · @references/personas/INDEX.md · @references/parts/progress.md |
| `@@consult` | putting one problem to one persona, mid-round | @references/parts/consult.md · @references/parts/workers.md · @references/personas/INDEX.md |
| `@@derived` | work the board found, and its tripwire | @references/parts/derived.md · @references/parts/order.md · @references/templates/prd.md |
| `@@commits` | one PRD, one commit, on the transition that lands it | @references/parts/commits.md · @references/parts/states.md |
| `@@memos` | recording a decision and checking it | @skills/pearde-memo.md · @references/memo.md · @references/parts/memos.md · @references/templates/memo.md · @resources/memos.py |
| `@@report` | the board written for a person, one rolling state | @skills/pearde-report.md · @references/report.md · @references/templates/report.md · @references/parts/handles.md · @references/parts/loop.md |
| `@@drill` | asking until the request is a contract | @skills/pearde-drill.md · @references/drill.md · @references/templates/prd.md · @references/parts/handles.md |
| `@@handles` | every command the board answers to | @references/parts/handles.md · @references/parts/loop.md · @references/drill.md |
| `@@view` | the live view — service, plan, render, writers | @skills/pearde-view.md · @references/parts/view.md · @resources/board/serve.py · @resources/board/plan.py · @resources/board/render.py · @resources/board/view.css · @resources/board/view.js · @resources/board/lit-core.min.js · @resources/board/viewtest.js · @resources/board/edit.py |
| `@@round` | what one session holds, and what survives a compaction | @references/parts/round.md · @references/parts/loop.md · @references/parts/guard.md · @resources/board/plan.py |
| `@@guard` | the loop's rules, enforced rather than written | @references/parts/guard.md · @resources/guard.py · @references/parts/loop.md · @references/install.md |
| `@@progress` | the line printed on every state change | @references/parts/progress.md · @references/parts/states.md |
| `@@statusline` | the numbers rendered continuously in the terminal | @references/parts/statusline.md · @resources/statusline.sh · @references/install.md |
| `@@install` | putting every skill where this agent finds it | @references/install.md · @SKILL.md · @resources/install.sh · @resources/guard.py · @references/system.md · @references/parts/doctor.md · @resources/doctor.sh |
| `@@skills` | the entry points, what each is a door to, and how one is named | @SKILL.md · @skills/pearde.md · @skills/pearde-drill.md · @skills/pearde-memo.md · @skills/pearde-view.md · @skills/pearde-report.md · @skills/pearde-master.md · @skills/pearde-doctor.md · @skills/pearde-persona.md · @skills/pearde-persona-ask.md · @skills/pearde-persona-create.md · @skills/pearde-scout.md · @references/install.md |
| `@@doctor` | telling a broken install from an absent one | @skills/pearde-doctor.md · @references/parts/doctor.md · @resources/doctor.sh · @resources/guard.py · @resources/index.py · @references/install.md |
| `@@master` | one plan across several repos | @skills/pearde-master.md · @references/parts/master.md · @references/settings.md · @references/parts/board.md |
| `@@settings` | every board-wide knob | @references/settings.md · @references/parts/contract.md |
| `@@language` | how everything on the board is written | @references/language.md · @references/templates/prd.md · @references/templates/spec.md · @references/templates/memo.md |
| `@@templates` | the four files a handle writes from | @references/templates/prd.md · @references/templates/spec.md · @references/templates/memo.md · @references/templates/report.md |
| `@@index` | addressing itself — the syntaxes, the scopes, the check | @index.md · @resources/index.py · @README.md · @references/language.md |
| `@@scout` | the discovery tool, whole — stars, routes, findings | @skills/pearde-scout.md · @resources/scout/README.md · @resources/scout/scout.sh · @resources/scout/buckets.txt · @resources/scout/route.sh · @resources/scout/routes.md · @resources/scout/findings.md · @resources/scout/reading-list.md |

## Files

Every tracked file, one row — for @resources/index.py and for adding a file.
Nothing here answers a question about the work; [Keywords](#keywords) does.

### Entry points

| anchor | is |
|---|---|
| @SKILL.md | the installer — invocable before the skills are, retired once they exist |
| @README.md | the manual — board, states, loop, briefs, view |
| @index.md | this index — the `@` and `@@` syntaxes, the scopes, the files |
| @TODO.md | the open loop |
| @.gitignore | what git leaves alone |

### `references/` — read

| anchor | is |
|---|---|
| @references/language.md | how every document is written |
| @references/install.md | what the system is, and how to install it for any agent |
| @references/settings.md | board knobs |
| @references/memo.md | how a decision is recorded |
| @references/report.md | the board written for a person |
| @references/drill.md | how to ask |
| @references/system.md | drop-in instructions block for `AGENTS.md` |

#### `references/parts/` — the workflow, one part per step

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
| @references/parts/progress.md | the line printed on every state change |
| @references/parts/statusline.md | the same numbers, continuously, for a person |
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
| @references/templates/report.md | the one rolling state, for a person |

### `resources/` — run

| anchor | is |
|---|---|
| @resources/install.sh | build one skill folder of links per file in `skills/` |
| @resources/doctor.sh | install check + repair |
| @resources/guard.py | the PreToolUse/PostToolUse hook that enforces the loop |
| @resources/statusline.sh | continuous progress numbers |
| @resources/memos.py | read + check memos — the only reader of that format |
| @resources/index.py | read + check this index — the only reader of that format |
| @resources/board/serve.py | the live service |
| @resources/board/plan.py | read + order the board |
| @resources/board/render.py | the page — markup, and the arithmetic behind it |
| @resources/board/view.css | the page's stylesheet, inlined at render |
| @resources/board/view.js | the page's script, inlined at render |
| @resources/board/viewtest.js | the view's gate — a rendered page in a real browser |
| @resources/board/lit-core.min.js | Lit 3, vendored — the page's component base |
| @resources/board/edit.py | the writers — one line at a time |

### `skills/` — one file per skill

Frontmatter, and a body that points into `references/`. @references/install.md
turns each into a folder of links wherever this agent looks.

One per feature. The cut follows the scopes above: a scope a person or an
agent **invokes** gets a skill. A scope the loop **reads mid-task** stays a
reference, reached through `@@`.

**The file name is the command.** A skill's `name:` must equal its file name,
and an install builds the folder from it, so `skills/pearde-view.md` is
`/pearde-view` everywhere. The prefix is the namespace and `-` is the only
separator a skill name may hold — kebab-case is the whole of the allowed
character set, and a `:` belongs to plugin loaders, which are one agent's
feature and not portable. `pearde-persona-ask` is the namespace `pearde`, the
group `persona`, the verb `ask`, spelled the way every agent can read it.

| anchor | is | scope |
|---|---|---|
| @skills/pearde.md | the round, and every handle that moves a PRD | `@@loop` |
| @skills/pearde-drill.md | asking until the request is a contract | `@@drill` |
| @skills/pearde-memo.md | recording a decision, and checking the record | `@@memos` |
| @skills/pearde-view.md | the timeline, the order, and editing through it | `@@view` |
| @skills/pearde-report.md | the board written for a person, one rolling state | `@@report` |
| @skills/pearde-master.md | one plan across several repositories | `@@master` |
| @skills/pearde-doctor.md | a broken install against an absent one | `@@doctor` |
| @skills/pearde-persona.md | who is working, and switching for the round | `@@personas` |
| @skills/pearde-persona-ask.md | one problem, one colleague, nothing written | `@@consult` |
| @skills/pearde-persona-create.md | composing one for a field the roster misses | `@@personas` |
| @skills/pearde-scout.md | ranked discovery, the route index, and the quality gates | `@@scout` |

#### `resources/scout/` — a self-contained tool

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
| @resources/scout/snapshots/2026-08-25.tsv | one day's star counts |
| @resources/scout/templates/_typos.toml | typos gate config |
| @resources/scout/templates/deny.toml | cargo-deny gate config |
| @resources/scout/templates/dependabot.yml | dependency updates |
| @resources/scout/templates/quality.yml | the quality gate workflow |
| @resources/scout/templates/scout.yml | the sweep in CI |
