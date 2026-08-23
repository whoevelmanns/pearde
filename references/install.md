# Install

`pearde` is a normal skill: installing is putting this folder where skills are
discovered — no scripts, no repo wiring. `<skill>` is the folder holding
`README.md`; it holds everything.

`bash <skill>/doctor.sh --fix` answers whether installing worked, for all
three steps below plus the board itself, and repairs what it can. Run it after
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
- `SKILL.md` carries the name and description that make `pearde` invocable.
- Already a real directory at that path? Stop and ask. Never replace it.

**Where instructions are read from a file instead**: append
`references/system.md` to it, commonly `AGENTS.md` at the repo root, creating
it if absent. Replace `<skill>` with the skill folder's actual path. The block
carries `pearde:begin` / `:end` markers — marker present means installed,
leave it alone.

Nothing else to fill in. The first run creates `prds/settings.md` and asks the
user for the board language, per `references/settings.md`.

## 2. Status line

Optional. `statusline.sh` renders `<dir> <branch> · <model>`, plus
`▸pearde <d>/<n> <p>% · open <o> <q>%` when a board is in scope. It walks up
from the cwd to the nearest board and stays quiet where there is none, so it
is safe globally.

Input: the status JSON on stdin, or `$PRD_STATUS_JSON`. Output: one line. Wire
it wherever a status line can run a command — a config entry pointing at
`bash <skill>/statusline.sh`, or at a symlink to it.

- **Wire it in the config that is in force.** `$CLAUDE_CONFIG_DIR` moves the
  whole config, so a machine can hold several profiles; an entry in the wrong
  one is correct and inert. `doctor.sh` prints the config directory it read.
- **A symlink is what rots** — the path resolves to nothing and the line reads
  as "no status line configured". `doctor.sh` reports `broken`; `--fix`
  repoints it.
- **An existing status line is composed with, never overwritten.** Export
  `$PRD_STATUS_JSON` once, call both, join the output. Only the board segment
  is pearde's — drop the dir/branch/model part if the existing line shows it.

## 3. The view

Optional, one command. The board reads and plans without it; the view is how a
person looks at it and edits it. Requires Python 3, nothing else — no Docker,
no account, one loopback port.

```sh
python3 <skill>/view/serve.py ensure     # start the service, register this board
```

It prints the URL: `http://127.0.0.1:8443/board/<name>`. Every registered
board is listed at `/`.

- **One daemon per machine**, singleton by port bind — `ensure` on another
  board registers it with the same service. `PEARDE_PORT` moves the port.
- **Nothing leaves the machine.** It binds `127.0.0.1`, reads the board's
  files, writes the same files back on an edit.
- `serve.py status` says what it watches; `serve.py stop` ends it. `doctor.sh`
  reports a board the service is not watching; `--fix` registers it.
- `view/state/` holds the registry and the log — machine-local, gitignored.
- No service at all? `python3 <skill>/view/plan.py gantt --open` writes the
  same render to `prds/.view.html` as one self-contained file.

## 4. A master board

Optional, nothing to install: a board becomes the parent of several others by
naming them.

```yaml
# <parent-repo>/prds/settings.md
members:
  - ../mitosys/prds
  - ../model/prds
```

- The members stay where they are, boards in their own right. The parent gets
  the merged scan, the merged plan, one timeline.
- Run the round in the parent from then on. `doctor.sh` grows a `members` row;
  the status line marks the group `⊞N`.
- README, **Master boards**, is the contract.

## Uninstall

Remove the symlink, delete the `pearde` block, unset the status line. `prds/`
is your data — untouched by installing, survives uninstalling.

The view: `python3 <skill>/view/serve.py stop`. Nothing else lives outside the
skill folder except `prds/.plan.json`, `prds/.history.jsonl` and
`prds/.view.html` on each board — machine-local and regenerable.
