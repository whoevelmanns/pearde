---
complexity: 12
workflow: implement-a-spec
footprint:
  - references/parts/handles.md
  - skills
---

# spec05 — the command line is the handle: `handles.md` gains the column, every skill names the one line

`references/parts/handles.md` gets a third column, `Command` — the exact
`pearde` line for each handle, `—` where the handle is the orchestrator's own
act, `pending · <child>` for every name a later child delivers. Every skill
file that runs a script names `python3 @resources/pearde.py <cmd>` and
nothing else. The chat spelling in `Say` does not change. Needs spec02: the
`--help` check below runs the landed file.

## What already stands

The dispatcher's `RESERVED` table in `resources/pearde.py` (from
`@prds/the-board-runs-itself/one-command/probe/pearde.py`) is the
name → child map the `pending` marks copy:

| child | names |
|---|---|
| `transitions-are-commands` | `add` `claim` `release` `answer` `defer` `retry` `unblock` `set` |
| `specced-is-a-command` | `specced` `refine` |
| `collect-is-a-command` | `collect` |
| `brief-is-printed` | `brief` |
| `the-loop-is-commands` | `sweep` |
| `init-asks-nothing` | `init` `settings` |
| `vision-is-first-class` | `vision` |

`settings` is named as a command by no child's contract; the parent's
`init-asks-nothing` is the child that writes `settings.md`, so it carries
the mark until a child claims the name.

## What is left

### `references/parts/handles.md`

1. The table header becomes `| Want | Say | Command |`, the separator gains a
   cell, and every existing row gains a third cell:

   | Say (unchanged) | Command |
   |---|---|
   | `status` | `pearde status` |
   | `scan` | `pearde scan` |
   | `once` | — |
   | `workers=5` | — |
   | `pipeline=5` | — |
   | `add <title>` | `pearde add` · pending · transitions-are-commands |
   | `defer <prd>` | `pearde defer` · pending · transitions-are-commands |
   | `drill <prd>` | — |
   | `retry <prd>` | `pearde retry` · pending · transitions-are-commands |
   | `unblock <prd>` | `pearde unblock` · pending · transitions-are-commands |
   | `collect` | `pearde collect` · pending · collect-is-a-command |
   | `run <prd>` | — |
   | `report` | — |
   | `memo <subject>` | `pearde memo add <subject>` |
   | `persona` | — |
   | `ask <id> <question>` | — |
   | `persona create <topic>` | — |
   | `plan` | `pearde plan` |
   | `gantt` | `pearde gantt --open` |
   | `calibrate` | `pearde calibrate` |
   | `view` | `pearde view` |
   | `master <path> …` | — |
   | `master` with no path | `pearde members` |
   | `reconcile` | `pearde reconcile` |
   | `doctor` | `pearde doctor --fix` |

2. New rows, appended to the table, one per reserved name with no row yet;
   `Want` is the phrase from the parent's children table, `Say` is the bare
   name, `Command` is `pearde <name>` · pending · `<child>`:
   `claim` `release` `answer` `set` (transitions-are-commands), `specced`
   `refine` (specced-is-a-command), `brief` (brief-is-printed), `sweep`
   (the-loop-is-commands), `init` `settings` (init-asks-nothing), `vision`
   (vision-is-first-class). A pending row carries the bare name and no
   arguments — the child that clears the mark writes the shape.
3. One sentence under the table, before the bullets: `The Command column is
   the line @resources/pearde.py answers; a row marked pending answers
   `not yet — <child>` until that child lands, and `the-loop-is-commands`
   clears every mark in one edit.`
4. No other prose in the file moves — the bullets and the `run <prd>` block
   stay as they are.

### `skills/`

5. Each command block or inline script call becomes the `pearde` line, the
   `@` path kept so the install resolves it:

   | file | today | becomes |
   |---|---|---|
   | `pearde.md` | `python3 @resources/board/plan.py scan` | `python3 @resources/pearde.py scan` |
   | `pearde-doctor.md` | `bash @resources/doctor.sh [board]` · `--fix [board]` | `python3 @resources/pearde.py doctor [board]` · `doctor --fix [board]`, comments kept |
   | `pearde-view.md` | six `serve.py` / `plan.py` lines | `python3 @resources/pearde.py view` · `view status` · `view stop` · `plan` · `gantt --open` · `reconcile`, comments kept |
   | `pearde-memo.md` | `` `python3 @resources/memos.py check <board>` reads them — the only reader of that format. `list` and `show` are the other two verbs. `` | `` `python3 @resources/pearde.py memo check [board]` reads them — @resources/memos.py is the only reader of that format. `memo list` and `memo add <subject>` are the other two verbs. `` |
   | `pearde-master.md` | `` `python3 @resources/board/plan.py members <board>` `` | `` `python3 @resources/pearde.py members [board]` `` |

   `show` was never a verb of `memos.py` — the memo skill's claim is
   corrected, not carried over. `pearde-scout.md` runs no board script and
   does not change. Frontmatter is untouched in every file.

## Acceptance

- [x] the handles table's header line is `| Want | Say | Command |` (cell text; padding is free) and every table row has three cells
- [x] for every row whose `Command` cell starts with `pearde `, `python3 resources/pearde.py <the words after pearde> --help` exits 0 — 26 rows: the 10 with a command today (`status` `scan` `memo add` `plan` `gantt` `calibrate` `view` `members` `reconcile` `doctor`) and the 16 pending; the check prints `26 ok`
- [x] every one of the 16 reserved names has exactly one row whose `Command` cell carries `pending` and the child from the table above
- [x] `grep -l "resources/board/plan.py\|resources/board/serve.py\|resources/memos.py\|resources/doctor.sh" skills/*.md` prints nothing, and `grep -l "resources/pearde.py" skills/*.md` lists exactly `pearde.md` `pearde-doctor.md` `pearde-view.md` `pearde-memo.md` `pearde-master.md`
- [x] `grep -c '`show`' skills/pearde-memo.md` prints 0
- [x] `bash resources/doctor.sh | grep "^  skills"` says `ok` — no frontmatter moved
- [x] `python3 resources/index.py check` prints no line naming `handles.md` or a file under `skills/`

## Verify and Proof

```sh
grep -n '^| *Want *| *Say *| *Command *|' references/parts/handles.md
awk -F'|' '/^\|/ && !/^\|[- |]*$/ { if (NF != 5) bad++ } END { print (bad+0) " rows without three cells" }' references/parts/handles.md
awk -F'|' '/^\|/ { c=$4; sub(/^ *`?/, "", c); if (c ~ /^pearde /) { sub(/`.*/, "", c); print c } }' references/parts/handles.md | sed 's/^pearde //' | while read -r cmd; do python3 resources/pearde.py $cmd --help >/dev/null 2>&1 && echo "ok $cmd" || echo "FAIL $cmd"; done | sort | uniq -c
for n in add claim release answer defer retry unblock set specced refine collect brief sweep init vision settings; do printf '%s %s\n' "$n" "$(grep -c "\`pearde $n\`.*pending" references/parts/handles.md)"; done
grep -l "resources/board/plan.py\|resources/board/serve.py\|resources/memos.py\|resources/doctor.sh" skills/*.md; grep -l "resources/pearde.py" skills/*.md
grep -c '`show`' skills/pearde-memo.md
bash resources/doctor.sh | grep "^  skills"
python3 resources/index.py check | grep -c "handles.md\|skills/"
```
