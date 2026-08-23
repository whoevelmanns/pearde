# Install

`pearde` is a normal skill. Installing is putting this folder where skills are
discovered — no scripts, no repo wiring.

`<skill>` is the skill folder, the one holding `README.md`. It holds
everything: the definition (`README.md`), the docs and templates in
`references/`, the status line, `memos.py`, `plane/`.

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

## 3. Plane

Optional. Mirrors the board as tickets in a self-hosted
[Plane](https://github.com/makeplane/plane) running inside the skill. Requires
Docker and Python 3, nothing else.

```sh
<skill>/plane/plane.sh boot        # everything: install + start + every board
                                   # on the machine synced into its own project
```

The pieces `boot` is made of, when one is needed alone:

```sh
<skill>/plane/plane.sh install     # fetches Plane's installer into <skill>/plane/,
                                   # installs into <skill>/plane/plane-app/,
                                   # sets port 8442; no-op when already installed
<skill>/plane/plane.sh start       # starts the containers, waits for the API
<skill>/plane/plane.sh bootstrap   # run from the target repo: creates the
                                   # account, workspace, API token, and writes
                                   # prds/.plane.env; no-op when configured
<skill>/plane/plane.sh open        # the app in the browser — no login screen
<skill>/plane/plane.sh status      # installed? running? reachable?
```

- **No login anywhere.** `bootstrap` creates everything itself, and `start`
  pins the app to `127.0.0.1` and injects auto-login, so the browser opens
  straight into the workspace. The knobs — password login back, LAN exposure —
  are in `plane/plane.md`, with the config keys, the manual path, and what maps
  to what.
- Port taken? Set `PLANE_PORT=<n>` before the first `install`.
- **A running app is not a mirror.** Each board needs its own `bootstrap`,
  which writes that board's `prds/.plane.env`. `plane.sh status [board]` and
  `doctor.sh` both report a board the app is up for and was never bootstrapped
  for.
- `plane-app/` and the fetched `setup.sh` are machine-local and gitignored, so
  a fresh clone of the skill re-runs `install` on each machine. Data lives in
  docker volumes and survives stop, start, and upgrade.

## Uninstall

Remove the symlink, delete the `pearde` block, unset the status line.

`prds/` is your data — untouched by installing, and it survives uninstalling.

Plane: `plane.sh stop`, then delete `<skill>/plane/plane-app/` and the
`plane-app` docker volumes.
