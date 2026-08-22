# Install

`prd` is a normal skill. Installing is putting this folder where skills are
discovered — no scripts, no repo wiring.

`<skill>` is the folder holding this file. It holds everything: the definition
(`README.md`), the templates, the status line.

## 1. The skill

Symlink the folder into a skills directory, named `prd`:

```
~/.claude/skills/prd -> <skill>          # every project
<repo>/.claude/skills/prd -> <skill>     # one project
```

A symlink, not a copy: one source of truth, so editing this folder updates
every install at once. `SKILL.md` carries the name and description. This is
what makes `prd` invocable as a command.

Already a real directory at that path? Stop and ask. Never replace it.

**Where instructions are read from a file instead** — append `SYSTEM.md` to
it, commonly `AGENTS.md` at the repo root; create it if absent. Replace
`<skill>` in the block with this folder's actual path. It carries
`prd-board:begin`/`:end` markers: marker present means installed, leave it
alone.

## 2. Status line

Optional. `statusline.sh` renders `<dir> <branch> · <model>`, plus
`▸prd <d>/<n> <p>% · open <o> <q>%` when a board is in scope. It walks up from
the cwd to the nearest board and stays quiet where there is none, so it is safe
globally.

It takes the status JSON on stdin, or in `$PRD_STATUS_JSON`, and prints one
line. Wire it wherever a status line can run a command — a config entry
pointing at `bash <skill>/statusline.sh`, or at a symlink to it.

**A status line already configured is composed with, never overwritten.** The
`$PRD_STATUS_JSON` fallback exists for exactly this: export the JSON once,
call both, join the output. How to join is a judgement call about that setup.
Only the board segment is prd's — drop the dir/branch/model part if the
existing line already shows it.

## Uninstall

Remove the symlink, delete the `prd-board` block, unset the status line.
`prds/` is your data: untouched by installing, and it survives uninstalling.
