---
name: pearde-report
description: Write the board's state for a person — one file, rewritten whole, saying what is planned, what is being worked on now, and what is undecided or failing. Prose and lists, no PRD names, no states, no weights. Use for "/pearde-report", "report", "write the report", "where do things stand", "status for a human", "what should I tell the team", "summarise the board in plain words", "update the report", "what is waiting on me". One state, never a log — git holds every earlier one.
---

Read @references/report.md for the format,
@references/templates/report.md for the file. The scope is `@@report`.

- **One file, rewritten whole.** `prds/report.md`. Never appended, never a
  section per round, never a date-stamped entry — the file says what is true
  today, and git holds every state before it.
- **Written for whoever the work is for, not for an agent.** No PRD directory
  names, no board states, no weights or percentages. The mapping table in
  @references/report.md says what each state reads as in plain words.
- **Four parts** — a lead, `## Planned`, `## In work`, `## Undecided or
  failing`. Every PRD on the board lands in exactly one of them.
- **The last section is the one that is read.** Each entry names the single
  thing that would move it, and a question is written as the fork itself so
  the reader can answer it where they sit.

Scan the board first — @references/parts/loop.md step 1 — so the report is the
board as it is, not as the conversation remembers it. A round that moved
anything rewrites this file before it stops.

No board in scope: write the text into the reply and say it belongs at
`prds/report.md`.
