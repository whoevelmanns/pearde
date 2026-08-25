<!-- pearde:begin — from the pearde skill's system.md -->
## PRD board (pearde)

This repo has a PRD board at `prds/`.

On "pearde", "work the board", "run the prds", or "pearde status": read
`@README.md` and follow it exactly.

`@<path>` is one file in the skill. `@@<keyword>` is a scope, listed in
`@index.md`. Read the scope, not a guess at which file holds the rule.

- **The round** — `@@loop`: scan, answer, refine, spec ahead, implement,
  collect, stop. `@@board` is what the scan walks. `@@states` is what a state
  means and what may set it.
- **Settings** — `language`, `workers`, `pipeline` live in `prds/settings.md`.
  Read it before working the board. Write it when the user changes one.
  Missing means first run: create it per `@@settings`, then ask the user for
  the board language — stated by the user, never guessed.
- **Who works** — one persona per session, one id from `@@personas`, stored
  nowhere: `engineer` until switched, and the round's line carries it. A
  candidate that differs from the active persona and governs the round: ask
  once, recommend the candidate, wear the answer — never switch silently. The
  user naming one is not a question. A dispatched worker's persona comes from
  its own job and moves nothing.
- **Calling one** — the roster is colleagues you can reach mid-round, on your
  own judgment, without asking. Put one problem to a persona you are not
  wearing, talk to it — follow up, push back, answer its question — and relay
  what it said attributed. It writes nothing and your persona does not move.
  Call the `skeptic` before `done` on work you implemented. `ask <id>
  <question>` is the user doing the same thing. `@@personas`.
- **Writing** — PRDs, specs, and reports go in the board `language`, per
  `@@language`.
- **Asking** — per `@@drill`: one round, the whole frontier, each question
  with your recommended answer.
- **Deciding** — a call the code will not explain goes in
  `prds/memos/<slug>.md`, never in a PRD. `@@memos` is the format.
- **Dispatching** — `@@workers` is the brief for an analyst and an
  implementer, verbatim. It also holds the single-agent mode.
- **Not wired up?** `@@install` says what installed means. `@@doctor` tells a
  broken install from an absent one.

Handles: `status`, `once`, `add <title>`, `drill <prd>`, `retry <prd>`,
`unblock <prd>`, `run <prd>`, `memo <subject>`, `plan`, `view`,
`persona [<id>]`, `persona create <topic>`, `workers=N`, `pipeline=N` —
`@@handles` is all of them.
<!-- pearde:end -->
