# Install

`pearde` is a normal skill. Installing is putting this folder where skills are
discovered — no scripts, no repo wiring.

`<skill>` is the skill folder, the one holding `README.md`. It holds
everything: the definition (`README.md`), the docs and templates in
`references/`, the status line, `memos.py`, `view/`.

`bash <skill>/doctor.sh --fix` answers whether installing worked, for all three
steps below plus the board itself, and repairs what it can. Run it after
installing, and whenever a part is silent when it should not be — an install
that is present and broken does nothing, exactly like one that is absent.

## 1. The skill

Symlink the folder into a skills directory, named `pearde`:

```
~/.claude/skills/pearde -> <skill>          # every project
<repo>/.claude/skills/pearde -> <skill>     # one project
```

- A symlink, not a copy — one source of truth, so editing this folder updates
  every install at once.
- `SKILL.md` carries the name and description. That is what makes `pearde`
  invocable as a command.
- Already a real directory at that path? Stop and ask. Never replace it.

**Where instructions are read from a file instead**: append
`references/system.md` to it, commonly `AGENTS.md` at the repo root, creating
it if absent. Replace `<skill>` in the block with the skill folder's actual
path. The block carries `pearde:begin` / `:end` markers — marker present means
installed, so leave it alone.

Nothing else to fill in. The first run creates `prds/settings.md` and asks the
user for the board language, per `references/settings.md`.

## 2. Status line

Optional. `statusline.sh` renders `<dir> <branch> · <model>`, plus
`▸pearde <d>/<n> <p>% · open <o> <q>%` when a board is in scope. It walks up
from the cwd to the nearest board and stays quiet where there is none, so it is
safe globally.

Input: the status JSON on stdin, or `$PRD_STATUS_JSON`. Output: one line. Wire
it wherever a status line can run a command — a config entry pointing at
`bash <skill>/statusline.sh`, or at a symlink to it.

- **Wire it in the config that is in force.** `$CLAUDE_CONFIG_DIR` moves the
  whole config elsewhere, so a machine can hold several profiles, each with its
  own `settings.json` and status line. An entry in the wrong one is correct and
  inert — the file loads for a different profile. `doctor.sh` prints the config
  directory it read.
- **A symlink is what rots.** The config still names a command, the command
  still names a path, and the path resolves to nothing, so the line renders
  empty and reads as "no status line configured". `doctor.sh` reports that as
  `broken` and `--fix` repoints it.
- **An existing status line is composed with, never overwritten.** The
  `$PRD_STATUS_JSON` fallback exists for this: export the JSON once, call both,
  join the output. How to join is a judgement call about that setup. Only the
  board segment is pearde's — drop the dir/branch/model part if the existing
  line already shows it.

## 3. The view

Optional, and one command. The board reads and plans without it; the view is
how a person looks at it and edits it. Requires Python 3 and nothing else — no
Docker, no account, no port but one on loopback.

```sh
python3 <skill>/view/serve.py ensure     # start the service, register this board
```

It prints the URL: `http://127.0.0.1:8443/board/<name>`. Every board registered
on this machine is listed at `/`.

- **One daemon per machine**, singleton by port bind — a second `ensure` on
  another board registers that board with the same service. `PLANE_SERVE_PORT`
  moves it.
- **Nothing leaves the machine.** It binds `127.0.0.1`, reads the board's
  files, and writes the same files back when you edit in the view.
- `serve.py status` says what it watches; `serve.py stop` ends it; `doctor.sh`
  reports a board the service is up for but is not watching, and `--fix`
  registers it.
- `view/state/` holds the registry and the log — machine-local and gitignored.
- No service at all? `python3 <skill>/view/plan.py gantt --open` writes the
  same render to `prds/.view.html` as one self-contained file.

## 4. A master board

Optional, and nothing to install: a board becomes the parent of several others
by naming them.

```yaml
# <parent-repo>/prds/settings.md
members:
  - ../mitosys/prds
  - ../model/prds
```

- The members stay where they are, boards in their own right. The parent gets
  the merged scan, the merged plan, and one timeline over all of them.
- Run the round in the parent from then on. `doctor.sh` grows a `members` row
  reporting what is merged and what is missing; the status line marks the group
  `⊞N`.
- README, **Master boards**, is the contract — addressing, what crosses a board
  boundary, and what does not.

## Uninstall

Remove the symlink, delete the `pearde` block, unset the status line.

`prds/` is your data — untouched by installing, and it survives uninstalling.

The view: `python3 <skill>/view/serve.py stop`. Nothing else of it lives
outside the skill folder except `prds/.plan.json`, `prds/.history.jsonl` and
`prds/.view.html` on each board — all machine-local and regenerable.
