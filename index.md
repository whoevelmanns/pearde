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

**Every tracked file has a row in @references/files.md** — the manifest, split
off so this map stays the size of the question it answers. When a file moves or
is added, write its row there, then every [Keywords](#keywords) row whose scope
it changed. Nothing else points at it.

@resources/index.py reads both and is the only reader of either format.

## Keywords

A file appears in every scope it belongs to. The first anchor in a row
explains the rest.

| keyword | is | read |
|---|---|---|
| `@@loop` | the round, start to finish | @references/parts/loop.md · @references/parts/round.md · @references/parts/states.md · @references/parts/commits.md · @references/parts/progress.md · @references/parts/order.md · @references/parts/roles.md |
| `@@board` | what the scan walks and what it parses | @references/parts/board.md · @references/parts/round.md · @resources/board/plan.py · @references/parts/contract.md · @references/parts/states.md · @references/templates/prd.md · @references/templates/vision.md · @references/settings.md |
| `@@states` | the nine states and what moves a PRD between them | @references/parts/states.md · @resources/board/transitions.py · @resources/board/specs.py · @references/parts/contract.md · @references/parts/commits.md |
| `@@order` | what runs next, and why no axis is a clock | @references/parts/order.md · @references/parts/derived.md · @resources/board/plan.py · @references/templates/vision.md |
| `@@workers` | dispatching an analyst or an implementer | @references/parts/workers.md · @references/parts/roles.md · @references/parts/solo.md · @references/language.md |
| `@@specs` | one implementable unit, written and read | @references/templates/spec.md · @references/parts/workers.md · @references/parts/contract.md |
| `@@personas` | who works the **session**, and how one is chosen or made — the roster is @references/personas/INDEX.md, and a persona file is read only when it is worn | @references/parts/personas.md · @references/personas/INDEX.md · @references/parts/progress.md |
| `@@consult` | putting one problem to one persona, mid-round | @references/parts/consult.md · @references/parts/workers.md · @references/personas/INDEX.md |
| `@@derived` | work the board found, and its tripwire | @references/parts/derived.md · @references/parts/order.md · @references/templates/prd.md |
| `@@commits` | one PRD, one commit, on the transition that lands it | @references/parts/commits.md · @references/parts/states.md |
| `@@memos` | recording a decision and checking it | @skills/pearde-memo.md · @references/memo.md · @references/parts/memos.md · @references/templates/memo.md · @resources/memos.py |
| `@@workflows` | how a kind of job is done, and improved on every run | @references/workflow.md · @references/parts/workflows.md · @references/templates/workflow.md · @references/templates/atomic.md · @resources/workflows.py |
| `@@report` | the board written for a person, one rolling state | @skills/pearde-report.md · @references/report.md · @references/templates/report.md · @references/parts/handles.md · @references/parts/loop.md |
| `@@drill` | asking until the request is a contract | @skills/pearde-drill.md · @references/drill.md · @references/templates/prd.md · @resources/questions.py · @references/parts/handles.md |
| `@@handles` | every command the board answers to | @references/parts/handles.md · @resources/pearde.py · @resources/board/transitions.py · @references/parts/loop.md · @references/drill.md |
| `@@view` | the live view — service, plan, render, writers | @skills/pearde-view.md · @references/parts/view.md · @resources/board/serve.py · @resources/board/plan.py · @resources/board/render.py · @resources/board/view.css · @resources/board/view.js · @resources/board/lit-core.min.js · @resources/board/viewtest.js · @resources/board/edit.py |
| `@@round` | what one session holds, and what survives a compaction | @references/parts/round.md · @references/parts/loop.md · @references/parts/guard.md · @resources/board/plan.py |
| `@@guard` | the loop's rules, enforced rather than written | @references/parts/guard.md · @resources/guard.py · @references/parts/loop.md · @references/install.md |
| `@@progress` | the line printed on every state change | @references/parts/progress.md · @references/parts/states.md |
| `@@statusline` | the numbers rendered continuously in the terminal | @references/parts/statusline.md · @resources/statusline.sh · @references/install.md |
| `@@install` | putting every skill where this agent finds it | @references/install.md · @SKILL.md · @resources/install.sh · @resources/pearde.py · @resources/guard.py · @references/system.md · @references/parts/doctor.md · @resources/doctor.sh |
| `@@skills` | the entry points, what each is a door to, and how one is named | @SKILL.md · @skills/pearde.md · @skills/pearde-drill.md · @skills/pearde-memo.md · @skills/pearde-view.md · @skills/pearde-report.md · @skills/pearde-master.md · @skills/pearde-doctor.md · @skills/pearde-persona.md · @skills/pearde-persona-ask.md · @skills/pearde-persona-create.md · @skills/pearde-scout.md · @references/install.md |
| `@@doctor` | telling a broken install from an absent one | @skills/pearde-doctor.md · @references/parts/doctor.md · @resources/doctor.sh · @resources/guard.py · @resources/index.py · @resources/questions.py · @references/install.md |
| `@@master` | one plan across several repos | @skills/pearde-master.md · @references/parts/master.md · @references/settings.md · @references/parts/board.md |
| `@@settings` | every board-wide knob | @references/settings.md · @references/parts/contract.md |
| `@@language` | how everything on the board is written | @references/language.md · @references/templates/prd.md · @references/templates/spec.md · @references/templates/memo.md |
| `@@templates` | the five files a handle writes from | @references/templates/prd.md · @references/templates/spec.md · @references/templates/memo.md · @references/templates/report.md · @references/templates/vision.md |
| `@@index` | addressing itself — the syntaxes, the scopes, the manifest, the check | @index.md · @references/files.md · @resources/index.py · @references/language.md |
| `@@scout` | the discovery tool, whole — stars, routes, findings | @skills/pearde-scout.md · @resources/scout/README.md · @resources/scout/scout.sh · @resources/scout/buckets.txt · @resources/scout/route.sh · @resources/scout/routes.md · @resources/scout/findings.md · @resources/scout/reading-list.md |

## Files

@references/files.md — every tracked file, one row. It is read when a file is
added or moved, and by @resources/index.py; never to answer a question about
the work.
