<!-- pearde:begin — from the pearde skill's system.md -->
## PRD board (pearde)

This repo has a PRD board at `prds/`.

On "pearde", "work the board", "run the prds", or "pearde status": read
`<skill>/README.md` and follow it exactly. It defines the board, the PRD
states, the loop, the analyst and implementer briefs, and the docs and
templates under `<skill>/references/`.

- **Settings** — `language`, `workers`, `pipeline` live in `prds/settings.md`.
  Read it before working the board; write it when the user changes one. Missing
  means first run: create it per `references/settings.md` and ask the user for
  the board language, stated by the user, never guessed.
- **Writing** — PRDs, specs, and reports go in the board `language`, per
  `references/language.md`: structure over prose, one idea per sentence,
  imperative, no hedging, no legacy.
- **Asking** — per `references/drill.md`: one round, the whole frontier, each
  question with your recommended answer.
- **Deciding** — a call the code will not explain goes in
  `prds/memos/<slug>.md`, never in a PRD: closed frontmatter, an Alternatives
  section that is never empty, checked by `doctor`. `references/memo.md` is the
  format.
- **Not wired up?** `references/install.md` says what installed means.
- **No parallel workers?** Run the single-agent mode the README describes.

Handles: `status`, `once`, `add <title>`, `drill <prd>`, `retry <prd>`,
`unblock <prd>`, `run <prd>`, `memo <subject>`, `plan`, `view`, `workers=N`,
`pipeline=N`.
<!-- pearde:end -->
