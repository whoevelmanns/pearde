# Install

A skill here is a folder under `skills/` holding a `SKILL.md`. Installing is
putting that folder where an agent looks, or telling an agent where it
already is. Nothing is compiled, nothing is registered, and no agent is
required to do it.

```bash
git clone https://github.com/yesitsfebreeze/pearde
bash pearde/resources/install.sh --apply .
```

`.` is the project you want the board in — the per-project rows resolve
against it. Machine-wide rows ignore it.

Run it with no `--apply` first and it only reports. `bash
@resources/doctor.sh --fix` checks the same ground plus the board itself and
calls back into it, so either command is a way in.

## 1. What it does

Every agent it knows about is one row in @references/targets.md, and the row
is the whole of what this repo knows about that agent — no agent is named in
any script here. Adding one is adding a row.

- An agent that discovers **skill folders** gets one symlink per skill in
  `skills/`, in the directory its row names.
- An agent that reads **one instructions file** gets the block from
  @references/system.md appended to it, between `pearde:begin` /
  `pearde:end` markers. The block points at the folders where they are, so
  nothing is copied.
- An agent that does **neither** is not a gap. Every skill folder reads where
  it lies; point yours at `skills/<name>/SKILL.md` by hand and that is the
  install. `@resources/doctor.sh` prints those paths when it finds no
  supported agent at all.

Scope is spelled by the path in the row. `$VAR`, `~` and `/` are
machine-wide and installed once. A bare relative path is per-project.

**A variable that moves an agent's whole configuration is why rows carry
alternatives.** A machine can hold several profiles, and a link written into
the wrong one is correct and inert — an install that is present and broken
looks exactly like one that is absent. `@resources/targets.py` resolves to
the profile in force, and doctor prints which one that was.

**A symlink, not a copy** — one source of truth, so editing this folder
updates every install at once.

- **Windows**: a symlink needs Developer Mode or Administrator. Without that,
  Git Bash's `ln -s` silently makes a *copy*, and the two trees drift with
  nothing to say it happened. Two ways out:
  - `MSYS=winsymlinks:nativestrict` in the environment before installing —
    a real symlink, once enabled.
  - Clone the repo straight into the agent's skills directory; `git pull`
    keeps it the one source of truth, where a local patch on a copy would
    not.

  `@resources/doctor.sh` tells the three apart: a symlink and a clone report
  `ok`, a plain copy reports `broken` and is never repaired for you — it may
  hold your edits.
- **Already a real directory where a link belongs?** Reported, never
  replaced. Reconcile it yourself.

The first run of the board creates `prds/settings.md` and asks the user for
the board language, per @references/settings.md.

## 2. Status line

Optional. `@resources/statusline.sh` renders `<dir> <branch> · <model>`, plus
`▸pearde <d>/<n> <p>% · open <o> <q>%` when a board is in scope. It walks up
from the cwd to the nearest board and stays quiet where there is none, so it
is safe globally.

Input: the status JSON on stdin, or `$PRD_STATUS_JSON`. Output: one line.

Which agents render one, and the file and key each reads it from, is the
`status` column of @references/targets.md — several spellings in the order
the agent itself reads them, so what doctor reports is the one in force.
Wire it as `bash @resources/statusline.sh`, or as a symlink to it.

- **A symlink is what rots** — the path resolves to nothing and the line
  reads as "nothing configured". `@resources/doctor.sh` reports `broken`;
  `--fix` repoints it.
- **An existing status line is composed with, never overwritten.** Export
  `$PRD_STATUS_JSON` once, call both, join the output. Only the board segment
  is pearde's — drop the dir/branch/model part if the existing line shows it.
- Settings files are the user's. Doctor prints the line to add and never
  writes it.

## 3. The view

Optional, one command. The board reads and plans without it. The view is how a
person looks at it and edits it. Requires Python 3 — no Docker, no account,
one loopback port.

```bash
python3 @resources/view/serve.py ensure   # start the service, register this board
```

It prints the URL: `http://127.0.0.1:8443/board/<name>`. Every registered
board is listed at `/`.

- **One daemon per machine**, singleton by port bind — `ensure` on another
  board registers it with the same service. `PEARDE_PORT` moves the port.
- **Nothing leaves the machine.** It binds `127.0.0.1`, reads the board's
  files, writes the same files back on an edit.
- `@resources/view/serve.py status` says what it watches;
  `@resources/view/serve.py stop` ends it. `@resources/doctor.sh` reports a
  board the service is not watching; `--fix` registers it.
- `resources/view/state/` holds the registry and the log — machine-local, gitignored.
- No service at all? `python3 @resources/view/plan.py gantt --open` writes the
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
- Run the round in the parent from then on. `@resources/doctor.sh` grows a
  `members` row; the status line marks the group `⊞N`.
- `@references/parts/master.md` is the contract.

## Uninstall

```bash
bash @resources/install.sh --remove .
```

Unlinks every link it made and strips the block from every instructions file,
leaving everything outside the markers alone. Unset the status line yourself
— that file is yours.

`prds/` is your data — untouched by installing, survives uninstalling.

The view: `python3 @resources/view/serve.py stop`. Nothing else lives outside
this folder except `prds/.plan.json`, `prds/.history.jsonl` and
`prds/.view.html` on each board — machine-local and regenerable.
