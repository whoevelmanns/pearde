---
name: pearde-report
description: Write the board's state for a person — one file, rewritten whole, saying what is planned, what is being worked on now, and what is undecided or failing. Prose and lists, no PRD names, no states, no weights. Use for "/pearde-report", "report", "write the report", "where do things stand", "status for a human", "what should I tell the team", "summarise the board in plain words", "update the report", "what is waiting on me". One state, never a log — git holds every earlier one.
---

Read @references/report.md — one state and not a log, human and not agent, the
four parts, and the table saying what each board state reads as in plain
words. @references/templates/report.md is the file. The scope is `@@report`.

Scan the board first — @references/parts/loop.md step 1 — so the report is the
board as it is, not as the conversation remembers it. A round that moved
anything rewrites `prds/report.md` before it stops.

No board in scope: write the text into the reply and say it belongs at
`prds/report.md`.
