<!-- pearde:begin — from the pearde skill's system.md -->
## PRD board (pearde)

This repo has a PRD board. On "pearde", "work the board", "run the prds", or
"pearde status": read `<skill>/README.md` and follow it exactly. It defines the
board under `prds/`, the PRD states, the loop, the analyst and implementer
briefs, and the docs and templates under `<skill>/references/`.

Board settings — `language`, `workers`, `pipeline` — live in
`prds/settings.md`. Read it before working the board; write it when the user
changes one. Missing means first run: create it per `references/settings.md`
and ask the user for the board language — stated by the user, never guessed.

Write everything — PRDs, specs, reports — in the board `language`, per
`references/language.md`: short, on the point, precise, no legacy. Ask per
`references/drill.md`: one round, the whole frontier, each question with your
recommended answer.

Not wired up yet? `references/install.md` says what installed means.
No parallel workers? Run the single-agent mode the README describes.

Handles: `status`, `once`, `add <title>`, `drill <prd>`, `retry <prd>`,
`run <prd>`, `memo <subject>`, `plan`, `plane`, `workers=N`, `pipeline=N`.

Decisions the code will not explain go in `prds/memos/<slug>.md`, not in a PRD:
closed frontmatter, an Alternatives section that is never empty, checked by
`doctor`. `references/memo.md` is the format.
<!-- pearde:end -->
