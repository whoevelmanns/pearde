# Plane

The board mirrors to [Plane](https://github.com/makeplane/plane), self-hosted
inside this folder. Every `prd.md` is one ticket, every `memos/<slug>.md` one
page. The board on disk stays the source of truth; Plane is a live view of it.

| file       | does                                                            |
|------------|------------------------------------------------------------------|
| `plane.sh` | installs and runs the app. Everything it creates stays in `plane-app/` beside it; data lives in docker volumes |
| `sync.py`  | mirrors the board and computes the wave plan. Python 3 stdlib, no packages |

## Install

Docker must be running. One command boots everything — the app and every board
on the machine:

```sh
<skill>/plane/plane.sh boot
```

The pieces, individually, from the target repo:

```sh
<skill>/plane/plane.sh install     # no-op when already installed
<skill>/plane/plane.sh start
<skill>/plane/plane.sh bootstrap   # no-op when already configured
<skill>/plane/plane.sh open        # → the browser, straight into the workspace
```

- `install` fetches Plane's own installer (`setup.sh`, latest release) into
  this folder, runs it non-interactively into `plane-app/`, and sets the port.
  Default 8442; override with `PLANE_PORT=<n>` on the first `install`.
- `bootstrap` removes the login step: it creates a local service account (via
  the api container's Django shell — anyone with docker access owns the
  instance anyway), the `prd` workspace, an API token, and writes
  `prds/.plane.env` for the nearest board, walking up from the cwd or taking
  the board dir as its argument. Idempotent: a working `.plane.env` is left
  alone, a lost token or password regenerated. Credentials land in
  `plane-app/bootstrap.env` — that is also the web UI login. Workspace slug:
  `PLANE_WORKSPACE_SLUG=<slug>`, default `prd`.

## Multi-project

One Plane, one workspace, one Plane project per board. Two repos with the same
directory name collide into one project — set `PLANE_PROJECT_NAME=` in one of
the `.plane.env` files.

```sh
<skill>/plane/plane.sh boot
```

`boot` is the cold start for the whole machine: install and start if needed,
then every known board bootstrapped into its own project and synced. Known
means the union of:

- the registry `plane-app/boards.list` — every board `bootstrap` ever touched
- discovery: every folder a Claude session was opened in, walked up to its repo
  root, kept when it holds `prds/`

A board that fails is reported and skipped; the rest boot. From there each
`/pearde` session keeps its own board live via the mirror rule in `README.md`.

## The browser

No login screen. `start` injects auto-login into the api container — every
request without a session is signed in server-side as the service account, so
the app opens straight into the workspace, and sign-out signs you back in. The
injection is `autologin/` beside this script, mounted via a compose override
(`plane-app/autologin.yaml`) that `start` writes; Plane's images stay stock, so
upgrades keep working.

Auto-login exists because `start` also pins the proxy to `127.0.0.1` — nothing
but this machine reaches the app. The knobs move together:

| set on          | knob                  | effect                                                     |
|-----------------|-----------------------|-------------------------------------------------------------|
| `start`         | `PLANE_AUTOLOGIN=0`   | password login again, on localhost. `open` puts the password (`prd-board-local`, or `PLANE_UI_PASSWORD` at `bootstrap`) in the clipboard |
| `start`         | `PLANE_EXPOSE_LAN=1`  | unpins the proxy AND disables auto-login. Then `PLANE_UI_PASSWORD=<strong>` on `bootstrap` is not optional |

Configuring by hand instead — one account, one workspace, one token in the web
UI — is equivalent. Write what you made as `prds/.plane.env`:

```sh
PLANE_API_URL=http://localhost:8442
PLANE_API_KEY=<the token>
PLANE_WORKSPACE=<workspace slug from the app URL>
```

Add `prds/.plane.env` and `prds/.plane-map.json` to that repo's `.gitignore` —
the env file holds the token, the map file is machine-local state.

`sync.py status` verifies the whole chain: board found, app reachable, token
valid. The first `sync` creates the Plane project (named after the repo
directory; override with `PLANE_PROJECT_NAME=`) and appends `PLANE_PROJECT_ID=`
to `.plane.env`.

## The mirror

`python3 <skill>/plane/sync.py sync` upserts every `prd.md`:

| PRD                       | ticket                                               |
|---------------------------|-------------------------------------------------------|
| `# <title>`               | name                                                  |
| body                      | description, plus a `prds/<name>/prd.md` footer       |
| `state`                   | a state of the same name, created per group below     |
| `priority` (int)          | ≥8 urgent · ≥5 high · ≥3 medium · ≥1 low · else none  |
| every other scalar key    | a `key: value` label — `est: 2h`, `blast-radius: high`|
| child PRD                 | sub-ticket (`parent`)                                 |
| wave from the last `plan` | a `wave: N` label                                     |

State groups: `open` `refine` `question` `specced` → unstarted ·
`analyzing` `claimed` → started · `done` → completed · `failed` → cancelled.

- `claim` and `needs` are not labels.
- Deleting a PRD unmaps its ticket, never deletes it in Plane.
- `sync` is incremental — `prds/.plane-map.json` holds ticket ids and content
  hashes, so an unchanged PRD costs no request.
- The orchestrator runs `sync --quiet` after every state change, right after
  the progress line, when `prds/.plane.env` exists.
- Tickets edited in Plane are overwritten on the next sync of that PRD. Fix the
  `prd.md`, not the ticket.

## Memos

The same `sync` mirrors `prds/memos/` into the project's **Pages**. A memo is a
document, not a work item — it has no state, nobody claims it, and putting it
in the issue list would put a decision in the middle of a work queue.

| memo                        | page                                                |
|-----------------------------|------------------------------------------------------|
| the set of them             | one `Memos` index page — a table folded from the frontmatter |
| `<slug>.md`                 | a `Memo · <slug> — <subject>` page                   |
| `kind` `status` `date` `updated` `supersedes` `superseded_by` | the fact line at the top of the page |
| `prds:`                     | a **governs** line naming the PRD dirs               |
| body                        | the page, plus a `prds/memos/<slug>.md` footer       |
| deleted on disk             | the page is **archived**, never deleted              |

The index sorts `open`, then `decided`, then `superseded`, and a superseded row
says what replaced it. It is a fold, not a second home: edit the memo on disk
and re-sync, never the table.

Two constraints, both Plane's rather than this skill's:

- **Pages are session-API only** (`/api/workspaces/…`, not `/api/v1`),
  reachable because `start` signs anonymous requests in as the service account.
  With auto-login off the memo mirror is skipped, `sync` says so on its last
  line, and the tickets mirror as usual — the same best-effort contract as the
  `Gantt — waves` view.
- **The pages are flat, not nested** under the index. Plane has a page tree and
  `parent` is a real field, but this build drops a page out of the project's
  page collection the moment one is set and 404s its detail route with it. A
  page nobody can list or open is worse than one at the top level, so the
  `Memo · ` prefix does the grouping the tree would have done.

Memo ids and hashes live beside the ticket ids in `prds/.plane-map.json`, so an
unchanged memo costs no request either. `python3 <skill>/memos.py check` is the
gate on the frontmatter, and `doctor.sh` reports it as `memos`.

## The plan

```sh
python3 <skill>/plane/sync.py plan [board] [--workers=N] [--no-push]
```

Computes the most-parallel execution order of the undone PRDs and prints it as
waves — wave 1 runs now, wave 2 after wave 1, all members of a wave in
parallel. `--no-push` prints the plan without writing `wave: N` labels or
Gantt dates to Plane.

- **`needs:`** in frontmatter — a list of PRD dir names — orders across waves.
  A parent implicitly needs its undone children. A need on a `done` PRD is
  satisfied. A cycle is an error.
- **`footprint` overlaps split a wave**: the higher `priority` keeps the
  earlier wave. The footprint is the union of the specs' `footprint:` and the
  PRD's own, so a PRD orders correctly before it is specced and while an
  implementer holds its spec files. A PRD with neither has no footprint and
  stays parallel; the dispatch-time overlap check in `README.md` step 5 still
  guards it.
- **The two constraints resolve together, not in sequence.** Every footprint
  bump re-applies the `needs` floor, so a bumped PRD never lands level with or
  ahead of a parent that waits on it.
- **A parent with live children weighs `0h`** — the hours are the children's,
  and counting both bills the same work twice. It still waits for them.
- **Only the states in `README.md`'s table are scheduled.** A PRD parked in a
  state of the user's own is listed as parked and left out of the waves.
- **Unestimated PRDs weigh at the board average**, or `est-default` from
  `prds/settings.md` while nothing is estimated. Workers default to `workers`
  from `prds/settings.md`; `--workers=N` overrides. Wave wall-clock =
  max(longest member, Σest ÷ workers).

The waves land in `.plane-map.json` and push to Plane two ways:

- a `wave: N` label per ticket
- `start_date` / `target_date` per scheduled ticket. The plan assigns every PRD
  a worker slot, and those est-hour offsets project onto calendar days —
  `gantt-day` hours of est per day (`prds/settings.md`, default `8h`), anchored
  on the day the plan ran. Small board looking flat in the timeline? Lower
  `gantt-day`. `done` and parked PRDs carry no dates, and a PRD that leaves the
  plan has its dates cleared on the next sync — a bar on the Gantt means work
  someone scheduled.

## Kanban and Gantt

In the project's work-items view, the layout switcher (top right) holds both:

- **Board** — the kanban. Grouped by State it is the PRD board one-to-one: the
  columns are the board states (`open`, `specced`, `claimed`, …). Group by
  Label instead to see the plan's waves as columns.
- **Timeline** — the Gantt. Bars come from the dates `plan` wrote: wave 1
  starts at the anchor day, each later wave after the one it waits on. Re-run
  `plan` to re-anchor at today.

`plan` also creates a saved view named **Gantt — waves** whose layout is the
timeline, writes its URL to the `gantt` key of `.plane-map.json` so anything
reading the board on disk can link straight at it, and prints it. That link
opens the plan as a Gantt with no layout to re-pick. It is created through the
session API, which `start`'s auto-login signs in for; with `PLANE_AUTOLOGIN=0`
the view is skipped and the switcher does the same job in two clicks.

Both fill themselves: `sync` carries every PRD in, `plan` orders them.
