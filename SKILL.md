---
name: pearde
description: Install this repo's skills for whichever agent is reading, then work the PRD board at prds/. One pass: materialise a folder per file in skills/ — pearde, pearde-drill, pearde-memo, pearde-view, pearde-report, pearde-master, pearde-doctor, pearde-persona, pearde-persona-ask, pearde-persona-create, pearde-scout, pearde-workflow — wherever this agent discovers skills, then hand off to the board and carry on with the request. Use for "/pearde", "install pearde", "set up pearde", "wire up the skills", and everything the board answers to.
---

# pearde — install, then work

You are reading the installer. It exists because this repo has to be
invocable before any of its skills are, and it stops existing the moment they
are.

## 1. Install

Read @references/install.md and do it. One pass, no questions unless a step
genuinely cannot be decided from what is on the machine.

```bash
bash @resources/install.sh --apply <skills-dir>
```

Working out `<skills-dir>` is step one of @references/install.md, and it is
the only part this repo cannot do for you. Report which of its four cases you
hit and where you installed — that sentence is the only record the install
has.

## 2. This file retires itself

`skills/pearde.md` is the real board skill. While this installer exists they
are two things answering to `pearde`, so `--apply` replaces this file with a
link to that one as its last act — the installer gone, the skill it stood in
for live. Nothing is lost: `git checkout SKILL.md` brings it back to
re-install or to install somewhere else.

If you install by hand rather than through `@resources/install.sh`, do that
last step by hand too:

```bash
ln -sfn skills/pearde.md SKILL.md
```

Only when this repo sits *inside* the skills directory under the name
`pearde` — that is the case where the installer shadows the skill. Cloned
anywhere else, this file is discovered by nobody and there is nothing to
retire.

## 3. Then work the request

Read @README.md and carry on with what was actually asked. Installing is not
the answer to the question; it is what had to happen first.

---

- `skills/` — one file per skill. The file name is the command.
- `references/` — read. The workflow, the personas, the templates, the rules.
- `resources/` — run. The board service, scout, the status line, doctor.
- @index.md is the map: `@<path>` is one file, `@@<keyword>` is a scope.
  @references/files.md is the manifest behind it, one row per file.
