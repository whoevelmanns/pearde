# Language

Governs this definition, PRDs, specs, memos, and worker reports. Written in the
board `language` from `.pearde/settings.md`. Every rule holds in any language.

Reader: an agent, cold, without the conversation that produced the document.

## Rules

- **Structure over prose.** A fact set is a table. A sequence is a numbered
  list. A rule set is bullets. Write a paragraph only when the content is an
  argument.
- **One idea per sentence.** A comma joining two thoughts is two sentences.
- **Imperative.** `Set specced`, not "the state should then be set to specced".
- **Name the thing.** The file, state, command, field. Never "the relevant
  config" for `@references/templates/prd.md`.
- **Address, do not describe a path.** One file is `@<path>` — the real path
  from the repo root with `@` in front. A whole feature is `@@<keyword>`, the
  scope defined in `@index.md`. Write `@@statusline`, not "the status line
  script and the progress part".
- **Reach for `@@` when the reader needs the scope, `@` when they need the
  file.** A brief, a handle, an install step says `@@view`; a rule that cites
  one table says `@references/parts/progress.md`.
- **No hedging.** No `might`, `probably`, `consider`. A real choice names who
  chooses and when.
- **No meta.** No "this section explains", no "as mentioned above".
- **No legacy.** Present tense only. No former names, no migration notes, no
  deprecated aliases. History lives in version control.
- **Rationale only where it changes a decision**, as a trailing clause after
  `—`. "One writer — nothing to race, so no locking" earns its clause. "This is
  important for correctness" does not.
- **Delete, do not deprecate.** A stale line reads as current.

## Where prose stays

A memo's `## Why` and `## Alternatives considered` are arguments, not facts —
the one place paragraphs are correct. Compress them. Everything else in a memo
is a table or a list.

## Shape per document

| document      | reader              | shape               |
|---------------|---------------------|---------------------|
| PRD body      | an analyst, cold    | a contract          |
| spec body     | an implementer      | a checklist         |
| atomic        | a worker, mid-step  | a checklist         |
| workflow      | a worker, cold      | a route             |
| memo          | a reader months out | decision + argument |
| worker report | the orchestrator    | verdict + evidence  |
| README        | a person, first time | quickstart, then rings |

The README is the one document with a human reader — a sentence there may
carry two ideas. Every other document keeps the rules above.
