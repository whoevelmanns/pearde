#!/usr/bin/env python3
"""pearde plane — mirror the board to a Plane project, and pre-plan waves.

    sync.py sync [board]                upsert one ticket per prd.md
    sync.py plan [board] [--workers N] [--no-push]
                                        compute the most-parallel wave plan,
                                        print it, push `wave: N` labels
    sync.py status [board]              config + connectivity check

board = the prds/ directory, a directory holding one, or omitted to walk up
from the cwd. Config in prds/.plane.env (see plane.md beside this script).
Ticket ids and pushed waves persist in prds/.plane-map.json.

Python 3 stdlib only.
"""
import datetime
import hashlib
import html
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request

# ── board ─────────────────────────────────────────────────────────────────────

def find_board(arg):
    if arg:
        p = os.path.abspath(arg)
        if os.path.basename(p) == "prds" and os.path.isdir(p):
            return p
        if os.path.isdir(os.path.join(p, "prds")):
            return os.path.join(p, "prds")
        die(f"no prds/ board at {arg}")
    d = os.getcwd()
    while True:
        if os.path.isdir(os.path.join(d, "prds")):
            return os.path.join(d, "prds")
        nxt = os.path.dirname(d)
        if nxt == d:
            die("no prds/ board found walking up from the cwd")
        d = nxt


def die(msg, code=2):
    print(f"plane-sync: {msg}", file=sys.stderr)
    sys.exit(code)


# Frontmatter: match a key by name at any indentation, anywhere in the block.
# Scalars and simple `- item` lists. Names are unique within one file.
KEY_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_-]*):\s*(.*?)\s*$")
ITEM_RE = re.compile(r"^\s*-\s+(.*?)\s*$")


def strip_comment(v):
    return re.sub(r"\s+#.*$", "", v).strip().strip("\"'")


def parse_prd(path):
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    fm, body_start = {}, 0
    if lines and lines[0].strip() == "---":
        i, cur_list = 1, None
        while i < len(lines) and lines[i].strip() != "---":
            line = lines[i]
            m = KEY_RE.match(line)
            item = ITEM_RE.match(line)
            if m:
                key, val = m.group(1), strip_comment(m.group(2))
                if val:
                    fm[key] = val
                    cur_list = None
                else:
                    fm[key] = []
                    cur_list = key
            elif item and cur_list is not None:
                v = strip_comment(item.group(1))
                if v:
                    fm[cur_list].append(v)
            i += 1
        body_start = i + 1
    body = "\n".join(lines[body_start:]).strip()
    title = None
    for line in body.splitlines():
        if line.startswith("# "):
            title = line[2:].strip().strip("<>").strip()
            break
    fm = {k: v for k, v in fm.items() if v != [] or k == "needs"}
    return fm, title, body


def scan(board):
    """{relpath-of-dir: prd} for every dir holding prd.md."""
    prds = {}
    for root, dirs, files in os.walk(board):
        dirs[:] = [d for d in dirs if d not in ("specs", ".plane")]
        if "prd.md" in files and root != board:
            rel = os.path.relpath(root, board)
            fm, title, body = parse_prd(os.path.join(root, "prd.md"))
            prds[rel] = {
                "rel": rel,
                "name": os.path.basename(rel),
                "fm": fm,
                "title": title or os.path.basename(rel),
                "body": body,
                "state": fm.get("state", "open"),
                "dir": root,
            }
    for rel, p in prds.items():
        p["children"] = [r for r in prds if os.path.dirname(r) == rel]
        p["parent"] = os.path.dirname(rel) or None
    return prds


def spec_data(prd):
    """(est_hours, footprints) unioned over specs/*.md, plus the PRD's own
    `footprint:`. A PRD declares its footprint before it is specced, and while
    an implementer holds its spec files — the wave planner needs the paths
    either way, and frontmatter on prd.md is the one place no worker writes."""
    sdir = os.path.join(prd["dir"], "specs")
    own = prd["fm"].get("footprint", [])
    feet = list(own) if isinstance(own, list) else [own]
    est = 0.0
    if os.path.isdir(sdir):
        for f in sorted(os.listdir(sdir)):
            if f.endswith(".md"):
                fm, _, _ = parse_prd(os.path.join(sdir, f))
                fp = fm.get("footprint", [])
                feet += fp if isinstance(fp, list) else [fp]
                est += hours(fm.get("est", ""))
    return est, [f.rstrip("/") for f in feet if f]


def hours(v):
    if not v or isinstance(v, list):
        return 0.0
    v = str(v).strip()
    m = re.match(r"^([\d.]+)\s*([mhd]?)$", v)
    if not m:
        return 0.0
    n, unit = float(m.group(1)), m.group(2)
    return n / 60 if unit == "m" else n * 8 if unit == "d" else n


# ── config + api ──────────────────────────────────────────────────────────────

ENV_TEMPLATE = """\
PLANE_API_URL=http://localhost:8442
PLANE_API_KEY=<workspace settings → API tokens>
PLANE_WORKSPACE=<workspace slug from the app URL>
"""


QUIET = False


def cfg_path_of(board):
    return os.path.join(board, ".plane.env")


def load_cfg(board):
    path = os.path.join(board, ".plane.env")
    if not os.path.isfile(path):
        return None, path
    cfg = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg, path


class Api:
    def __init__(self, cfg):
        self.base = cfg["PLANE_API_URL"].rstrip("/")
        self.key = cfg["PLANE_API_KEY"]
        self.ws = cfg["PLANE_WORKSPACE"]
        self.issue_seg = None  # "issues" or "work-items", probed once

    # Plane throttles an API key (API_KEY_RATE_LIMIT, 60/minute by default), and
    # one board's first sync is hundreds of requests. A 429 is a pause, not a
    # failure: wait out the window and repeat the same request, so a big board
    # syncs slowly instead of dying half-written.
    RETRY_WAITS = (5, 15, 30, 60, 60, 60)

    def call(self, method, path, payload=None):
        for attempt in range(len(self.RETRY_WAITS) + 1):
            req = urllib.request.Request(
                f"{self.base}/api/v1{path}",
                data=json.dumps(payload).encode() if payload is not None else None,
                headers={"X-API-Key": self.key, "Content-Type": "application/json"},
                method=method,
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    raw = r.read()
                    return json.loads(raw) if raw else {}
            except urllib.error.HTTPError as e:
                body = e.read().decode(errors="replace")[:300]
                if e.code == 429 and attempt < len(self.RETRY_WAITS):
                    nap = int(e.headers.get("Retry-After") or self.RETRY_WAITS[attempt])
                    if not QUIET:
                        print(f"  rate-limited, {nap}s …", file=sys.stderr)
                    time.sleep(nap)
                    continue
                raise ApiError(e.code, f"{method} {path}: HTTP {e.code} {body}")
            except urllib.error.URLError as e:
                die(f"cannot reach Plane at {self.base}: {e.reason}")

    def listing(self, path):
        """Every page, not the first. A project past 100 tickets used to return
        a third of itself, and a lookup that misses a ticket creates a second
        one."""
        sep = "&" if "?" in path else "?"
        out = self.call("GET", f"{path}{sep}per_page=100")
        if not (isinstance(out, dict) and "results" in out):
            return out
        rows = list(out["results"])
        cursor = out.get("next_cursor") if out.get("next_page_results") else None
        while cursor:
            page = self.call("GET", f"{path}{sep}per_page=100&cursor={cursor}")
            rows += page.get("results", [])
            cursor = page.get("next_cursor") if page.get("next_page_results") else None
        return rows

    def proj(self, pid, sub):
        return f"/workspaces/{self.ws}/projects/{pid}/{sub}"

    def issues_seg(self, pid):
        if self.issue_seg is None:
            try:
                self.listing(self.proj(pid, "issues/"))
                self.issue_seg = "issues"
            except ApiError as e:
                if e.code == 404:
                    self.issue_seg = "work-items"
                else:
                    raise
        return self.issue_seg


class ApiError(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code


# ── plane objects ─────────────────────────────────────────────────────────────

STATE_GROUP = {
    "open": "unstarted", "analyzing": "started", "refine": "unstarted",
    "question": "unstarted", "specced": "unstarted", "claimed": "started",
    "done": "completed", "failed": "cancelled",
}
# The states the loop moves work through. A board state outside STATE_GROUP is
# the user's own and terminal to the loop: it gets its own Plane state rather
# than borrowing `open`'s, and the wave planner does not schedule it.
LIVE_STATES = {"open", "analyzing", "refine", "question", "specced",
               "claimed", "failed"}
PRIO = [(8, "urgent"), (5, "high"), (3, "medium"), (1, "low")]


def plane_priority(v):
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "none"
    return next((name for cut, name in PRIO if n >= cut), "none")


def ensure_project(api, cfg, cfg_path, board):
    pid = cfg.get("PLANE_PROJECT_ID")
    if pid:
        try:
            api.call("GET", f"/workspaces/{api.ws}/projects/{pid}/")
            return pid
        except ApiError as e:
            if e.code not in (403, 404):
                raise
            pid = None  # deleted in the app — find or create anew
    name = cfg.get("PLANE_PROJECT_NAME") or os.path.basename(os.path.dirname(board))
    for p in api.listing(f"/workspaces/{api.ws}/projects/"):
        if p["name"] == name:
            pid = p["id"]
            break
    if not pid:
        ident = re.sub(r"[^A-Z0-9]", "", name.upper())[:5] or "PRD"
        pid = api.call("POST", f"/workspaces/{api.ws}/projects/",
                       {"name": name, "identifier": ident})["id"]
        print(f"created Plane project '{name}'")
    lines = [l for l in open(cfg_path, encoding="utf-8").read().splitlines()
             if not l.startswith("PLANE_PROJECT_ID=")]
    lines.append(f"PLANE_PROJECT_ID={pid}")
    open(cfg_path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    cfg["PLANE_PROJECT_ID"] = pid
    return pid


def ensure_states(api, pid, extra=()):
    """board-state → plane state id; custom-named states, group default as fallback.
    `extra` are board states outside STATE_GROUP — each gets its own state in the
    `cancelled` group, so a PRD nobody is working does not read as `open`. An
    existing state of that name is adopted, so a regroup made in the app holds."""
    have = {s["name"].lower(): s for s in api.listing(api.proj(pid, "states/"))}
    by_group = {}
    for s in have.values():
        by_group.setdefault(s["group"], s["id"])
    out = {}
    for bstate, group in list(STATE_GROUP.items()) + [(e, "cancelled") for e in extra]:
        if bstate in have:
            out[bstate] = have[bstate]["id"]
            continue
        try:
            s = api.call("POST", api.proj(pid, "states/"),
                         {"name": bstate, "group": group, "color": "#8a8a8a"})
            out[bstate] = s["id"]
        except ApiError:
            out[bstate] = by_group.get(group) or next(iter(by_group.values()))
    return out


GANTT_VIEW = "Gantt — waves"


def ensure_gantt_view(api, pid):
    """A saved view whose layout IS the timeline, so the plan opens as a Gantt
    instead of a list someone has to re-pick a layout for. Views live on the
    session API, not /api/v1: reachable because `start` signs anonymous
    requests in as the service account. Best-effort — with auto-login off it
    cannot be created, and the layout is two clicks in the app."""
    root = f"{api.base}/api/workspaces/{api.ws}/projects/{pid}/views/"

    def session(method, payload=None):
        req = urllib.request.Request(
            root, method=method,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Content-Type": "application/json", "Referer": api.base + "/"})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}

    try:
        for v in session("GET") or []:
            if v.get("name") == GANTT_VIEW:
                return f"{api.base}/{api.ws}/projects/{pid}/views/{v['id']}/"
        v = session("POST", {
            "name": GANTT_VIEW,
            "description": "the wave plan — parents after children, "
                           "footprint clashes in separate waves",
            "access": 1,
            "filters": {},
            "display_filters": {"layout": "gantt_chart",
                                "order_by": "start_date", "group_by": None},
            "display_properties": {"key": True, "state": True, "priority": True,
                                   "labels": True, "start_date": True,
                                   "due_date": True},
        })
        return f"{api.base}/{api.ws}/projects/{pid}/views/{v['id']}/"
    except Exception:
        return None


def ensure_labels(api, pid, names):
    have = {l["name"]: l["id"] for l in api.listing(api.proj(pid, "labels/"))}
    for n in sorted(names - set(have)):
        try:
            have[n] = api.call("POST", api.proj(pid, "labels/"), {"name": n})["id"]
        except ApiError as e:
            print(f"  label '{n}' failed: {e}", file=sys.stderr)
    return have


# ── markdown → html (minimal, lossless enough for a ticket description) ───────

def md_html(md):
    out, para, fence = [], [], False
    def flush():
        if para:
            out.append("<p>" + "<br/>".join(para) + "</p>")
            para.clear()
    for line in md.splitlines():
        if line.strip().startswith("```"):
            flush()
            out.append("<pre>" if not fence else "</pre>")
            fence = not fence
            continue
        if fence:
            out.append(html.escape(line))
            continue
        s = html.escape(line.rstrip())
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            flush()
            n = len(m.group(1))
            out.append(f"<h{n}>{m.group(2)}</h{n}>")
        elif re.match(r"^\s*-\s+", s):
            flush()
            out.append("<ul><li>" + re.sub(r"^\s*-\s+", "", s) + "</li></ul>")
        elif not s.strip():
            flush()
        else:
            para.append(s)
    flush()
    if fence:
        out.append("</pre>")
    return "\n".join(out)


# ── map file ──────────────────────────────────────────────────────────────────

def load_map(board):
    path = os.path.join(board, ".plane-map.json")
    if os.path.isfile(path):
        return json.load(open(path, encoding="utf-8")), path
    return {"issues": {}, "waves": {}, "schedule": {}}, path


def save_map(mp, path):
    json.dump(mp, open(path, "w", encoding="utf-8"), indent=1, sort_keys=True)


# ── sync ──────────────────────────────────────────────────────────────────────

SKIP_KEYS = {"state", "priority", "claim", "needs", "time"}


# A label is a filter, not a field. Plane rejects a name over 255 characters,
# and a frontmatter value that long — a full verify command, a paragraph — is
# not something anyone filters a board by. It stays in the file.
LABEL_MAX = 120


def label_names(prd, wave):
    names = set()
    for k, v in prd["fm"].items():
        if k in SKIP_KEYS or isinstance(v, list) or v == "":
            continue
        name = f"{k}: {v}"
        if len(name) > LABEL_MAX:
            continue
        names.add(name)
    if wave:
        names.add(f"wave: {wave}")
    return names


def gantt_dates(mp, rel, day_h):
    """(start_date, target_date) from the plan's hour offsets — est-hours
    projected onto calendar days at day_h hours per day, anchored at plan
    time. None when the PRD is not in the last plan."""
    sched = mp.get("schedule", {}).get(rel)
    anchor = mp.get("planned_at")
    if not sched or not anchor:
        return None, None
    base = datetime.date.fromisoformat(anchor)
    start = base + datetime.timedelta(days=int(sched["start"] // day_h))
    end = base + datetime.timedelta(
        days=max(int(sched["start"] // day_h),
                 math.ceil(sched["end"] / day_h) - 1))
    return start.isoformat(), end.isoformat()


def cmd_sync(board, quiet=False):
    global QUIET
    QUIET = quiet
    cfg, cfg_path = load_cfg(board)
    if cfg is None:
        die(f"no {cfg_path} — write it first:\n{ENV_TEMPLATE}")
    for k in ("PLANE_API_KEY", "PLANE_WORKSPACE"):
        if not cfg.get(k) or cfg[k].startswith("<"):
            die(f"{k} not set in {cfg_path}")
    cfg.setdefault("PLANE_API_URL", "http://localhost:8442")
    api = Api(cfg)
    pid = ensure_project(api, cfg, cfg_path, board)
    seg = api.issues_seg(pid)
    prds = scan(board)
    states = ensure_states(
        api, pid, sorted({p["state"] for p in prds.values()} - set(STATE_GROUP)))
    mp, mp_path = load_map(board)
    # A crash between a POST and the map write used to orphan the ticket it had
    # just created, and the next run created it again. Adopt by exact title
    # instead: the project is the record of what exists, the map only caches it.
    mapped = {e.get("id") for e in mp["issues"].values() if e.get("id")}
    by_title = {}
    for it in api.listing(api.proj(pid, f"{seg}/")):
        by_title.setdefault(it["name"], []).append(it["id"])
    labels = ensure_labels(
        api, pid,
        set().union(*(label_names(p, mp["waves"].get(r))
                      for r, p in prds.items())) if prds else set())

    day_h = hours(board_settings(board).get("gantt-day", "8h")) or 8.0
    changed = 0
    for rel in sorted(prds):  # parents sort before children
        p = prds[rel]
        lnames = label_names(p, mp["waves"].get(rel))
        payload = {
            "name": p["title"][:250],
            "description_html": md_html(p["body"]) +
                f"\n<p><code>prds/{rel}/prd.md</code></p>",
            "state": states.get(p["state"], states["open"]),
            "priority": plane_priority(p["fm"].get("priority")),
            "labels": sorted(labels[n] for n in lnames if n in labels),
        }
        # Always written, never only set: a PRD the last plan dropped — finished,
        # or parked in a state the loop does not work — must lose its bar, or the
        # Gantt keeps showing work nobody scheduled.
        start, target = (gantt_dates(mp, rel, day_h)
                         if p["state"] in LIVE_STATES else (None, None))
        payload["start_date"], payload["target_date"] = start, target
        parent_id = mp["issues"].get(p["parent"], {}).get("id") if p["parent"] else None
        digest = hashlib.sha1(
            json.dumps([payload, parent_id], sort_keys=True).encode()).hexdigest()
        ent = mp["issues"].get(rel, {})
        if not ent.get("id"):
            for oid in by_title.get(payload["name"], []):
                if oid not in mapped:
                    ent["id"] = oid
                    mapped.add(oid)
                    mp["issues"][rel] = ent
                    save_map(mp, mp_path)
                    break
        if ent.get("hash") == digest and ent.get("id"):
            continue
        if parent_id:
            payload["parent"] = parent_id
        try:
            if ent.get("id"):
                api.call("PATCH", api.proj(pid, f"{seg}/{ent['id']}/"), payload)
            else:
                ent["id"] = api.call("POST", api.proj(pid, f"{seg}/"), payload)["id"]
        except ApiError as e:
            if ent.get("id") and e.code == 404:  # deleted in the app — recreate
                ent["id"] = api.call("POST", api.proj(pid, f"{seg}/"), payload)["id"]
            else:
                raise
        ent["hash"] = digest
        mp["issues"][rel] = ent
        mapped.add(ent["id"])
        save_map(mp, mp_path)  # an id survives the next 429, not just a clean run
        changed += 1
        if not quiet:
            print(f"  ↑ {rel} [{p['state']}]")

    gone = [r for r in mp["issues"] if r not in prds]
    for r in gone:
        del mp["issues"][r]
    save_map(mp, mp_path)
    if not quiet or changed:
        print(f"plane-sync: {changed} updated, {len(prds) - changed} unchanged"
              + (f", {len(gone)} unmapped" if gone else ""))


# ── plan ──────────────────────────────────────────────────────────────────────

def overlap(a, b):
    return any(x == y or x.startswith(y + "/") or y.startswith(x + "/")
               for x in a for y in b)


def board_settings(board):
    path = os.path.join(board, "settings.md")
    if os.path.isfile(path):
        fm, _, _ = parse_prd(path)
        return fm
    return {}


def cmd_plan(board, workers, push):
    settings = board_settings(board)
    if workers is None:
        try:
            workers = int(settings.get("workers", 3))
        except ValueError:
            workers = 3
    prds = scan(board)
    todo = {r: p for r, p in prds.items() if p["state"] in LIVE_STATES}
    parked = sorted(r for r, p in prds.items()
                    if p["state"] not in LIVE_STATES and p["state"] != "done")
    if not todo:
        print("plan: nothing to do — no undone PRDs")
        return

    # resolve `needs` to relpaths; a need on a done PRD is satisfied.
    # A parent implicitly needs its undone children — work flows to the leaves.
    by_name = {}
    for r in prds:
        by_name.setdefault(os.path.basename(r), r)
    needs = {}
    for r, p in todo.items():
        deps = p["fm"].get("needs", [])
        deps = deps if isinstance(deps, list) else [deps]
        needs[r] = [c for c in p["children"] if c in todo]
        for d in deps:
            t = by_name.get(d, d if d in prds else None)
            if t is None:
                print(f"plan: {r} needs '{d}' — no such PRD, ignored", file=sys.stderr)
            elif t in todo and t not in needs[r]:
                needs[r].append(t)

    est, feet = {}, {}
    for r, p in todo.items():
        e, f = spec_data(p)
        est[r] = e or hours(p["fm"].get("est", ""))
        feet[r] = f
    # A parent with live children is a container: the work is in the children,
    # and weighing it too bills the same hours twice. It still waits for them.
    for r, p in todo.items():
        if any(c in todo for c in p["children"]):
            est[r] = 0.0
    known = [e for e in est.values() if e > 0]
    avg = (sum(known) / len(known) if known
           else hours(settings.get("est-default", "4h")) or 4.0)
    for r, p in todo.items():
        if not est[r] and not any(c in todo for c in p["children"]):
            est[r] = avg

    # wave = longest needs-chain; cycles are an error
    wave, visiting = {}, set()
    def w(r):
        if r in wave:
            return wave[r]
        if r in visiting:
            die(f"needs cycle through {r}")
        visiting.add(r)
        wave[r] = 1 + max((w(d) for d in needs[r]), default=0)
        visiting.discard(r)
        return wave[r]
    for r in todo:
        w(r)

    # footprint conflicts never share a wave: keep the higher priority, bump the rest
    def prio(r):
        try:
            return float(todo[r]["fm"].get("priority", 0))
        except ValueError:
            return 0.0
    # Both constraints to a joint fixed point. A bump for a footprint clash
    # moves one PRD forward, which can put it level with — or ahead of — a
    # parent that waits on it, so the needs floor is re-applied after every
    # bump rather than once before them.
    moved = True
    while moved:
        moved = False
        for r in sorted(todo, key=lambda x: (-prio(x), x)):
            for s in sorted(todo, key=lambda x: (-prio(x), x)):
                if r < s and wave[r] == wave[s] and overlap(feet[r], feet[s]):
                    bump = s if prio(r) >= prio(s) else r
                    wave[bump] += 1
                    moved = True
        for r in sorted(todo, key=lambda x: wave[x]):
            floor = max((wave[d] + 1 for d in needs[r]), default=1)
            if wave[r] < floor:
                wave[r] = floor
                moved = True

    nwaves = max(wave.values())
    print(f"plan: {len(todo)} PRDs in {nwaves} wave(s)"
          f" · workers={workers} · unspecced est'd at {avg:.1f}h"
          + (f" · {len(parked)} parked: " + ", ".join(
              f"{os.path.basename(r)} [{prds[r]['state']}]" for r in parked)
             if parked else ""))
    # schedule each PRD onto a worker slot — the offsets feed the Gantt dates
    schedule, t0 = {}, 0.0
    for n in range(1, nwaves + 1):
        members = sorted((r for r in wave if wave[r] == n),
                         key=lambda x: (-prio(x), x))
        if not members:
            continue
        load = sum(est[r] for r in members)
        slots = [0.0] * max(workers, 1)
        for r in members:
            i = min(range(len(slots)), key=lambda k: slots[k])
            schedule[r] = {"start": t0 + slots[i], "end": t0 + slots[i] + est[r]}
            slots[i] += est[r]
        wall = max(slots)
        print(f"\nwave {n} — {len(members)} in parallel · Σ{load:.1f}h · ~{wall:.1f}h wall")
        for r in members:
            p = todo[r]
            why = []
            if needs[r]:
                why.append("needs " + ", ".join(os.path.basename(d) for d in needs[r]))
            if not feet[r]:
                why.append("unspecced")
            print(f"  · {r} [{p['state']}] p{p['fm'].get('priority', 0)}"
                  f" {est[r]:.1f}h" + (f"  ({'; '.join(why)})" if why else ""))
        t0 += wall
    print(f"\n≈ {t0:.1f}h wall-clock @ {workers} workers")

    mp, mp_path = load_map(board)
    mp["waves"] = {r: wave[r] for r in wave}
    mp["schedule"] = schedule
    mp["planned_at"] = datetime.date.today().isoformat()
    save_map(mp, mp_path)
    cfg, _ = load_cfg(board)
    if push and cfg:
        cmd_sync(board, quiet=True)
        api = Api(cfg)
        pid = cfg.get("PLANE_PROJECT_ID") or ensure_project(api, cfg, cfg_path_of(board), board)
        url = ensure_gantt_view(api, pid)
        if url:
            # persisted so anything reading the board on disk — the status line
            # included — can link straight at the timeline
            mp, mp_path = load_map(board)
            mp["gantt"] = url
            save_map(mp, mp_path)
            print(f"\ngantt: {url}")
        else:
            print("\ngantt: switch the layout to Timeline in the app — "
                  "a saved view needs auto-login on")
    elif push:
        print("no prds/.plane.env — plan saved locally, not pushed")


def cmd_status(board):
    cfg, cfg_path = load_cfg(board)
    prds = scan(board)
    print(f"board: {board} · {len(prds)} PRDs")
    if cfg is None:
        print(f"not configured — write {cfg_path}:\n{ENV_TEMPLATE}")
        return
    api = Api({**{"PLANE_API_URL": "http://localhost:8442"}, **cfg})
    me = api.call("GET", "/users/me/")
    pid = cfg.get("PLANE_PROJECT_ID", "(auto-create on first sync)")
    print(f"plane: {api.base} · user {me.get('email', '?')}"
          f" · workspace {api.ws} · project {pid}")


def cmd_prune(board, apply=False):
    """One ticket per PRD. Tickets sharing a title are duplicates — an
    interrupted sync's leftovers — and every one but the mapped keeper goes. A
    title matching no PRD is reported, never deleted: it is someone's own
    ticket, and the mirror does not own it."""
    cfg, cfg_path = load_cfg(board)
    if cfg is None:
        die(f"no {cfg_path} — nothing to prune")
    api = Api(cfg)
    pid = ensure_project(api, cfg, cfg_path, board)
    seg = api.issues_seg(pid)
    prds = scan(board)
    mp, mp_path = load_map(board)
    titles = {p["title"][:250]: rel for rel, p in prds.items()}
    keep = {e["id"] for e in mp["issues"].values() if e.get("id")}

    by_title = {}
    for it in api.listing(api.proj(pid, f"{seg}/")):
        by_title.setdefault(it["name"], []).append(it["id"])

    dupes, foreign = [], []
    for name, ids in by_title.items():
        if name not in titles:
            foreign.append((name, len(ids)))
            continue
        keeper = next((i for i in ids if i in keep), ids[0])
        dupes += [i for i in ids if i != keeper]

    print(f"plane-prune: {len(by_title)} titles · {sum(len(v) for v in by_title.values())} tickets"
          f" · {len(dupes)} duplicate(s)")
    for name, n in foreign:
        print(f"  ? {name[:70]} ×{n} — matches no PRD, left alone")
    if not dupes:
        return
    if not apply:
        print(f"  {len(dupes)} to delete — re-run with --apply")
        return
    for i, iid in enumerate(dupes, 1):
        api.call("DELETE", api.proj(pid, f"{seg}/{iid}/"))
        if i % 25 == 0:
            print(f"  deleted {i}/{len(dupes)}")
    print(f"plane-prune: deleted {len(dupes)} duplicate(s)")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    cmd = args[0] if args else "sync"
    board = find_board(args[1] if len(args) > 1 else None)
    if cmd == "sync":
        cmd_sync(board, quiet="--quiet" in flags)
    elif cmd == "plan":
        workers = next((int(f.split("=")[1]) for f in flags
                        if f.startswith("--workers=")), None)
        cmd_plan(board, workers, push="--no-push" not in flags)
    elif cmd == "status":
        cmd_status(board)
    elif cmd == "prune":
        cmd_prune(board, apply="--apply" in flags)
    else:
        die(f"unknown command '{cmd}' — sync | plan | status | prune")


if __name__ == "__main__":
    main()
