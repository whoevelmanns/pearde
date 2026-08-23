# Plane

The board mirrors to [Plane](https://github.com/makeplane/plane), self-hosted
inside this folder. Every `prd.md` is one ticket. The board on disk stays the
source of truth; Plane is a live view of it.

- `plane.sh` — installs and runs the app. Everything it creates stays in
  `plane-app/` beside it; data lives in docker volumes.
- `sync.py` — mirrors the board and computes the wave plan. Python 3 stdlib,
  no packages.

## Install

Docker must be running. One command boots everything — the app and every
board on the machine:

```sh
<skill>/plane/plane.sh boot
```

The pieces, individually, from the target repo:

```sh
<skill>/plane/plane.sh install     # no-op when already installed
<skill>/plane/plane.sh start
<skill>/plane/plane.sh bootstrap   # no-op when already configured
<skill>/plane/plane.sh open       # → the browser, straight into the workspace
```

`install` fetches Plane's own installer (`setup.sh`, latest release) into this
folder, runs it non-interactively into `plane-app/`, and sets the port. Default
port 8442; override with `PLANE_PORT=<n>` on the first `install`.

`bootstrap` removes the login step: it creates a local service account
(via the api container's Django shell — anyone with docker access owns the
instance anyway), the `prd` workspace, an API token, and writes
`prds/.plane.env` for the nearest board — walking up from the cwd, or pass the
board dir as the argument. Idempotent: a working `.plane.env` is left alone; a
lost token or password is regenerated. The account credentials land in
`plane-app/bootstrap.env` — that is also your login for the web UI. Workspace
slug: `PLANE_WORKSPACE_SLUG=<slug>`, default `prd`.

## Multi-project

One Plane, one workspace, one Plane project per board. Two repos with the
same directory name would collide into one project — set
`PLANE_PROJECT_NAME=` in one of the `.plane.env` files.

```sh
<skill>/plane/plane.sh boot
```

`boot` is the cold start for the whole machine: install and start if needed,
then every known board is bootstrapped into its own project and synced. Known
means the union of:

- the registry `plane-app/boards.list` — every board `bootstrap` ever touched
- discovery: every folder a Claude session was opened in, walked up to its
  repo root, kept when it holds `prds/`

A board that fails is reported and skipped; the rest boot. From there each
`/pearde` session keeps its own board live via the mirror rule in README.md.

## The browser

No login screen: `start` injects auto-login into the api container — every
request without a session is signed in server-side as the service account, so
the app opens straight into the workspace. Sign-out signs you back in. The
injection is `autologin/` beside this script, mounted via a compose override
(`plane-app/autologin.yaml`) that `start` writes; Plane's images stay stock,
so upgrades keep working.

Auto-login exists because `start` also pins the proxy to `127.0.0.1` — nothing
but this machine reaches the app. The knobs move together:

- `PLANE_AUTOLOGIN=0` on `start` — password login again, on localhost. `open`
  then puts the password (`prd-board-local`, or `PLANE_UI_PASSWORD` at
  `bootstrap`) in the clipboard.
- `PLANE_EXPOSE_LAN=1` on `start` — unpins the proxy AND disables auto-login;
  then `PLANE_UI_PASSWORD=<strong>` on `bootstrap` is not optional.

Configuring by hand instead — one account, one workspace, one token in the
web UI — is equivalent; write what you made as `prds/.plane.env`:

```sh
PLANE_API_URL=http://localhost:8442
PLANE_API_KEY=<the token>
PLANE_WORKSPACE=<workspace slug from the app URL>
```

Add `prds/.plane.env` and `prds/.plane-map.json` to that repo's `.gitignore` —
the env file holds the token, the map file is machine-local state.

`sync.py status` verifies the whole chain: board found, app reachable, token
valid. The first `sync` creates the Plane project (named after the repo
directory; override with `PLANE_PROJECT_NAME=`) and appends
`PLANE_PROJECT_ID=` to `.plane.env`.

## The mirror

`python3 <skill>/plane/sync.py sync` upserts every `prd.md`:

| PRD                       | ticket                                             |
|---------------------------|----------------------------------------------------|
| `# <title>`               | name                                               |
| body                      | description, plus a `prds/<name>/prd.md` footer    |
| `state`                   | a state of the same name, created per group below  |
| `priority` (int)          | ≥8 urgent · ≥5 high · ≥3 medium · ≥1 low · else none |
| every other scalar key    | a `key: value` label — `est: 2h`, `blast-radius: high` |
| child PRD                 | sub-ticket (`parent`)                              |
| wave from the last `plan` | a `wave: N` label                                  |

State groups: `open` `refine` `question` `specced` → unstarted ·
`analyzing` `claimed` → started · `done` → completed · `failed` → cancelled.
`claim` and `needs` are not labels; deleting a PRD unmaps its ticket but never
deletes it in Plane.

`sync` is incremental — `prds/.plane-map.json` holds ticket ids and content
hashes, so an unchanged PRD costs no request. The orchestrator runs
`sync --quiet` after every state change, right after the progress line, when
`prds/.plane.env` exists. Tickets edited in Plane get overwritten on the next
sync of that PRD: fix the `prd.md`, not the ticket.

## The plan

`python3 <skill>/plane/sync.py plan [--workers=N] [--no-push]` computes the
most-parallel execution order of the undone PRDs and prints it as waves —
wave 1 runs now, wave 2 after wave 1, all members of a wave in parallel:

- `needs:` in frontmatter — a list of PRD dir names — orders across waves.
  A parent implicitly needs its undone children. A need on a `done` PRD is
  satisfied. A cycle is an error.
- `footprint` overlaps split a wave: the higher `priority` keeps the earlier
  wave. The footprint is the union of the specs' `footprint:` and the PRD's
  own, so a PRD orders correctly before it is specced and while an implementer
  holds its spec files. A PRD with neither has no footprint and stays
  parallel; the dispatch-time overlap check in README.md step 5 still guards
  it.
- The two constraints resolve together, not in sequence: every footprint bump
  re-applies the `needs` floor, so a bumped PRD never lands level with or ahead
  of a parent that waits on it.
- A parent with live children weighs `0h` — the hours are the children's, and
  counting both bills the same work twice. It still waits for them.
- Only the states in README.md's table are scheduled. A PRD parked in a state
  of the user's own is listed as parked and left out of the waves.
- Unestimated PRDs weigh at the board average, or `est-default` from
  `prds/settings.md` while nothing is estimated. Workers default to
  `workers` from `prds/settings.md`; `--workers=N` overrides. Wave
  wall-clock = max(longest member, Σest ÷ workers).

The waves land in `.plane-map.json` and push to Plane two ways:

- a `wave: N` label per ticket
- `start_date`/`target_date` per scheduled ticket: the plan assigns every PRD a
  worker slot, and those est-hour offsets project onto calendar days —
  `gantt-day` hours of est per day (`prds/settings.md`, default `8h`),
  anchored on the day the plan ran. Small board looking flat in the timeline?
  Lower `gantt-day`. `done` and parked PRDs carry no dates, and a PRD that
  leaves the plan has its dates cleared on the next sync — a bar on the Gantt
  means work someone scheduled.

## Kanban and Gantt

In the project's work-items view, the layout switcher (top right) holds both:

- **Board** — the kanban. Grouped by State it is the PRD board one-to-one:
  the columns are the board states (`open`, `specced`, `claimed`, …). Group
  by Label instead to see the plan's waves as columns.
- **Timeline** — the Gantt. Bars come from the dates `plan` wrote: wave 1
  starts at the anchor day, each later wave after the one it waits on.
  Re-run `plan` to re-anchor at today.

`plan` also creates a saved view named **Gantt — waves** whose layout is the
timeline, writes its URL to the `gantt` key of `.plane-map.json` so anything
reading the board on disk can link straight at it, and prints it: that link opens the plan as a Gantt with no
layout to re-pick. It is created through the session API, which `start`'s
auto-login signs in for; with `PLANE_AUTOLOGIN=0` the view is skipped and the
switcher does the same job in two clicks.

Both fill themselves: `sync` carries every PRD in, `plan` orders them.
