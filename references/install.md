# Install

One explanation, for any agent. Read it, work out what your own setup calls
each thing, and make the links. Nothing here is specific to one agent, and
there is no list of agents to be on — if yours is not described below, the
last section still works.

## What the system is

Three folders, and the split between them is the whole design.

| folder | holds | who touches it |
|---|---|---|
| `skills/` | one `.md` per skill — frontmatter and a short body | an agent, as an entry point |
| `references/` | everything **read**: the workflow, personas, templates, rules | an agent, mid-task |
| `resources/` | everything **run**: the board service, scout, the status line, doctor | a shell, never read for meaning |

A skill file is thin on purpose. Its frontmatter — `name` and `description` —
is what makes it findable and what decides when it fires. Its body points into
`references/` and stops. The knowledge is not in the skill; the skill is the
door.

`@index.md` is the map both `@<path>` and `@@<keyword>` resolve against.

## What installing means

Putting each file in `skills/` where your agent looks for a skill, without
copying anything.

**The one catch.** A skill file says `Read @README.md` — a path relative to
the skill's own folder. Drop the bare `.md` file into a skills directory and
that path resolves to nothing. So a skill is installed as a *folder*, built
out of links:

```
<skills-dir>/<name>/
    SKILL.md    -> <repo>/skills/<name>.md
    README.md   -> <repo>/README.md
    index.md    -> <repo>/index.md
    references  -> <repo>/references
    resources   -> <repo>/resources
```

Five links, one skill, nothing copied. Read through them, every `@<path>` in
the repo resolves exactly as it does here. `@resources/install.sh` does this
for all of `skills/` in one command if you would rather not do it by hand:

```bash
bash @resources/install.sh <skills-dir>          # say what it would make
bash @resources/install.sh --apply <skills-dir>  # make it
bash @resources/install.sh --remove <skills-dir> # take it back out
```

- **Links, not copies.** One source of truth, so editing this repo updates
  every install at once. A copy drifts, and nothing says it happened.
- **Windows** needs Developer Mode or Administrator for a symlink. Without
  it, `ln -s` in Git Bash silently *copies*. Either turn it on
  (`MSYS=winsymlinks:nativestrict`), or clone this repo straight into the
  skills directory and let `git pull` be the update path.
- **Something real already sitting where a link goes** is never replaced. It
  may hold someone's edits. Reconcile it by hand.

## Finding where the links go

You know your own setup; this repo does not. Work it out, in this order, and
stop at the first that is true.

1. **This repo is already inside a skills directory.** If the folder holding
   `@SKILL.md` is itself sitting in the place your agent scans for skills,
   then `pearde` is installed and its slot is taken. Install the *others* —
   every file in `skills/` except `pearde.md` — as siblings.
2. **Your agent has a skills directory.** Make the folders there. Prefer the
   machine-wide one if you want the skills everywhere, the project-local one
   if you want them here only.
   - **Check which configuration is actually in force first.** Where an
     environment variable can move an agent's whole configuration directory, a
     machine can hold several profiles, and links written into the wrong one
     are correct and inert. An install that is present and broken looks
     exactly like one that is absent — that is the failure worth one extra
     command to avoid.
3. **Your agent reads one instructions file instead** — a single file it loads
   every session, whatever it is called. Append `@references/system.md` to it,
   creating it if absent. The block carries `pearde:begin` / `pearde:end`
   markers, so nothing outside them is ever read back out; marker already
   there means installed — leave it alone, or replace what is between the
   markers if the block has changed.
   - **Substitute `<PEARDE>` for this repo's absolute path** as you write it.
     The block is going into a file belonging to some other repo, where a
     relative `@references/...` resolves against *that* tree — silently, into
     a file that is not ours or into nothing at all. The placeholder is there
     to stop exactly that.
4. **Neither.** Nothing is broken. Every skill reads where it lies — point
   yourself at `skills/<name>.md` and its `references/` and you have the whole
   system. That is a complete install, it is just one you do by hand each
   time.

Say which of the four you did, and where. That sentence is the only record
the install has.

## The status line

Optional, and separate — a skills directory has nothing to do with it.

`@resources/statusline.sh` renders `<dir> <branch> · <model>`, plus
`▸pearde <d>/<n> <p>% · open <o> <q>%` when a board is in scope. It walks up
from the working directory to the nearest board and stays silent where there
is none, so it is safe to wire globally.

- Input: the status JSON on stdin, or `$PRD_STATUS_JSON`. Output: one line.
- Wire `bash @resources/statusline.sh` wherever your setup runs a command for
  its status line. If it has no such hook, the same numbers on demand are
  `bash @resources/statusline.sh <<< '{}'`.
- **Compose, never overwrite.** An existing status line keeps working: export
  `$PRD_STATUS_JSON` once, call both, join the output. Only the board segment
  is this repo's — drop the dir/branch/model part if the other line shows it.
- A settings file is the user's. Print the line to add; do not write it.

## The view

Optional, one command. The board reads and plans without it. The view is how a
person looks at it and edits it. Needs Python 3 — no Docker, no account, one
loopback port.

```bash
python3 @resources/board/serve.py ensure   # start the service, register this board
```

It prints the URL: `http://127.0.0.1:8443/board/<name>`. Every registered
board is listed at `/`.

- **One daemon per machine**, singleton by port bind — `ensure` on another
  board registers it with the same service. `PEARDE_PORT` moves the port.
- **Nothing leaves the machine.** It binds `127.0.0.1`, reads the board's
  files, writes the same files back on an edit.
- `@resources/board/serve.py status` says what it watches;
  `@resources/board/serve.py stop` ends it. `@resources/doctor.sh` reports a
  board the service is not watching; `--fix` registers it.
- `resources/board/state/` holds the registry and the log — machine-local,
  gitignored.
- No service at all? `python3 @resources/board/plan.py gantt --open` writes
  the same render to `prds/.view.html` as one self-contained file.

## A master board

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

## The first run

The board creates `prds/settings.md` and asks the user for the board
language, per @references/settings.md. Nothing about installing does that,
and nothing about installing touches `prds/`.

## Uninstall

Remove the skill folders you made, or `bash @resources/install.sh --remove
<skills-dir>`. Delete the `pearde:begin`/`:end` block from the instructions
file, leaving the rest of it alone. Unwire the status line yourself — that
file is yours.

`prds/` is your data: untouched by installing, and it survives uninstalling.
The view stops with `python3 @resources/board/serve.py stop`. Nothing else of
this system lives outside this folder except `prds/.plan.json`,
`prds/.history.jsonl` and `prds/.view.html` on each board — machine-local and
regenerable.
