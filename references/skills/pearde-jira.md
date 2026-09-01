---
name: pearde-jira
description: Mirrors a PRD's `state` onto its Jira issue's status, walking the project's real workflow graph one live transition at a time, and reads back the other direction — drift between a PRD's state and its Jira status, and "Selected"+assigned tickets with no PRD yet. Five subcommands: `sync`, `discover`, `check`, `drift`, `import-new`. Use for "/pearde-jira sync", "/pearde-jira discover", "/pearde-jira check", "/pearde-jira drift", "/pearde-jira import-new", "mirror this PRD to Jira", "did this ticket's status drift from the board", "any new Jira tickets without a PRD", "(re)cache this project's workflow graph", "is Jira reachable".
---

Read @resources/jira/README.md.
