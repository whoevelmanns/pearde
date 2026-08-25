---
name: pearde
description: Install this repo's skills for whichever agent is reading, then work the PRD board at prds/. Materialises one skill folder per file in skills/ — pearde, pearde-drill, pearde-memo, pearde-view, pearde-master, pearde-doctor, pearde-persona, pearde-persona-ask, pearde-persona-create, pearde-scout — wherever this agent discovers skills, wires the status line, and hands off to the board. Use for "/pearde", "install pearde", "set up pearde", "wire up the skills", and everything the board answers to once it is installed.
---

# pearde

**Not installed yet?** Read @references/install.md and do it — one pass, then
carry on with the request. Installing is making links; nothing is compiled and
no file outside this repo is rewritten except the ones @references/install.md
names.

You are reading this file, so this repo is discoverable as one skill. That is
enough to work the board and nothing else. Installing splits it into the
skills in `skills/` — each invocable on its own, each triggering on its own
description — and wires the status line.

**Already installed?** Skip it. @resources/doctor.sh says which it is:

```bash
bash @resources/doctor.sh --fix
```

Then read @README.md and work the request.

---

- `skills/` — one file per skill. What an agent is pointed at.
- `references/` — read. The workflow, the personas, the templates, the rules.
- `resources/` — run. The board service, scout, the status line, doctor.
- @index.md is the map: `@<path>` is one file, `@@<keyword>` is a scope.
