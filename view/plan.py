#!/usr/bin/env python3
"""pearde plan — the board, read and ordered.

    plan.py plan  [board] [--workers N]   the most-parallel wave plan
    plan.py reconcile [board]             re-order the waves, keep the anchor
    plan.py gantt [board] [--open]        render the view to prds/.view.html
    plan.py members [board]               what a master board merges
    plan.py status [board]                the board, its members, its memos

board = the prds/ directory, a directory holding one, or omitted to walk up
from the cwd. The plan persists in prds/.plan.json; the view reads it.

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
# win: a cp1252 console cannot encode the box/greek glyphs this prints,
# and the trailing summary dies on UnicodeEncodeError. Force UTF-8 out.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memos as memolib  # noqa: E402 — the skill root, one dir up
import render as renderlib  # noqa: E402 — beside this script

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
    print(f"pearde: {msg}", file=sys.stderr)
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


# ── master boards ─────────────────────────────────────────────────────────────
# A master board merges other boards into one plan. The PRDs never move: each
# member keeps its own prds/, its own settings, its own view, and the
# orchestrator writes state into the member's own prd.md. Only the plan — the
# waves, the schedule, the merged mirror — lives at the master.
#
# A member PRD is addressed `@<member>/<rel>` board-wide. The sigil is what
# makes one flat namespace safe: a PRD directory is never named `@…`, so a
# qualified rel can never collide with a master's own PRD.
MEMBER_SIGIL = "@"

MEMBER_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def members(board):
    """[(name, path)] — the member boards a master board merges.

    `members:` in prds/settings.md, one `- <path>` or `- <name>: <path>` per
    line. A relative path resolves against the board dir, so a master beside
    its members reads `- ../model/prds`; a path at a repo root gains `/prds`
    when that exists. The name is the address, so it defaults to the same
    walk-up that names the board and is suffixed rather than replaced
    on a collision — two members must never share a key."""
    raw = board_settings(board).get("members", [])
    if isinstance(raw, str):
        raw = [raw]
    out, seen = [], set()
    for item in raw:
        head, sep, tail = str(item).partition(":")
        if sep and MEMBER_NAME_RE.match(head.strip()):
            name, path = head.strip(), tail
        else:
            name, path = "", str(item)
        path = os.path.expanduser(path.strip())
        # absolute always: this path is handed to the daemon, which walks it
        # from a working directory that has nothing to do with the board's
        path = os.path.abspath(os.path.join(board, path))
        if os.path.basename(path) != "prds" and os.path.isdir(
                os.path.join(path, "prds")):
            path = os.path.join(path, "prds")
        name = name or re.sub(r"[^A-Za-z0-9_.-]", "-", project_name(path))
        base, n = name, 2
        while name in seen:
            name, n = f"{base}-{n}", n + 1
        seen.add(name)
        out.append((name, path))
    return out


def is_master(board):
    return bool(members(board))


def members_missing(board):
    """Declared members that are not on disk — an unmounted volume, a repo
    moved, a typo. They read exactly like a board that shrank, so nothing that
    removes anything runs while one of them is unresolved."""
    return [n for n, p in members(board) if not os.path.isdir(p)]


def qualify_paths(prd, paths):
    """A member's footprint is written relative to its own repo, so two
    projects both touching `src/lib.ts` are not touching the same file:
    qualify it with the member name before anything compares two of them. An
    absolute path is left as written — that is how a deliberate cross-repo
    overlap still clashes."""
    b = prd.get("board")
    if not b:
        return paths
    return [p if p.startswith("/") else f"{MEMBER_SIGIL}{b}/{p}" for p in paths]


def _scan_one(board, prefix="", bname=None):
    prds = {}
    for root, dirs, files in os.walk(board):
        dirs[:] = [d for d in dirs if d not in ("specs",)]
        if "prd.md" in files and root != board:
            local = os.path.relpath(root, board)
            rel = prefix + local
            fm, title, body = parse_prd(os.path.join(root, "prd.md"))
            prds[rel] = {
                "rel": rel,
                "local": local,
                "name": os.path.basename(local),
                "fm": fm,
                "title": title or os.path.basename(local),
                "body": body,
                "state": fm.get("state", "open"),
                "dir": root,
                "board": bname,            # None on the board's own PRDs
                "board_path": board,
                # where a reader finds the file: the real path for a member,
                # the contract path for the board's own
                "footer": (os.path.join(root, "prd.md") if bname
                           else f"prds/{local}/prd.md"),
            }
    return prds


def scan(board):
    """{rel: prd} for every dir holding prd.md — the board's own, and every
    member board's when this is a master, addressed `@<member>/<rel>`."""
    prds = _scan_one(board)
    for name, path in members(board):
        if os.path.isdir(path):
            prds.update(_scan_one(path, f"{MEMBER_SIGIL}{name}/", name))
    for rel, p in prds.items():
        p["children"] = [r for r in prds if os.path.dirname(r) == rel]
        parent = os.path.dirname(rel)
        p["parent"] = parent if parent in prds else None
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
                est += float(fm.get("complexity", 0) or 0) or hours(fm.get("est", ""))
    return est, qualify_paths(prd, [f.rstrip("/") for f in feet if f])


def hours(v):
    if not v or isinstance(v, list):
        return 0.0
    v = str(v).strip()
    m = re.match(r"^([\d.]+)\s*([mhd]?)$", v)
    if not m:
        return 0.0
    n, unit = float(m.group(1)), m.group(2)
    return n / 60 if unit == "m" else n * 8 if unit == "d" else n


# The states the loop moves work through. A board state outside STATE_GROUP is
# the user's own and terminal to the loop: the wave planner does not schedule
# it, and the view lists it as parked rather than folding it into `open`.
LIVE_STATES = {"open", "analyzing", "refine", "question", "specced",
               "claimed", "blocked", "failed"}


def project_name(board):
    """The board's containing dir names the project — except a dot-dir
    (`.mi/prds`), which is not a name anyone means: walk up until an ancestor
    can carry it. `board` as the last resort, never empty."""
    d = os.path.dirname(os.path.abspath(board))
    while d and d != "/":
        base = os.path.basename(d)
        if base and not base.startswith("."):
            return base
        d = os.path.dirname(d)
    return "board"


def infer_name(board):
    """A master board's name from its members — `mitosys+model+realm+shared`.

    A master board is named for what it owns, and until somebody names it the
    members are the only honest description of that. Long lists fold: past
    four names the join is a wall of text nobody reads, and the count carries
    the same information."""
    names = [n for n, _ in members(board)]
    if not names:
        return project_name(board)
    joined = "+".join(names)
    if len(joined) <= 40 and len(names) <= 4:
        return joined
    return f"{names[0]}+{len(names) - 1} more"


def board_name(board):
    """What the board calls itself: `name:` in prds/settings.md, else inferred
    — from the members on a master board, from the directory walk-up on a
    plain one. Inference is a placeholder: the first round that meets an
    unnamed master board asks the user and writes `name:`."""
    raw = str(board_settings(board).get("name", "")).strip()
    return re.sub(r"[^A-Za-z0-9_. -]", "-", raw) or infer_name(board)


def scan_memos(board):
    """{slug: memo} — the board's own memos, plus every member board's when
    this is a master, slugged `@<member>/<slug>`. The file never moves: a
    decision belongs to the repo it governs, and the master only folds them
    into one index the way it folds the plan into one timeline."""
    ms = dict(memolib.scan(board))
    for name, path in members(board):
        for slug, m in memolib.scan(path).items():
            q = f"{MEMBER_SIGIL}{name}/{slug}"
            ms[q] = dict(m, slug=q)
    return ms


# ── map file ──────────────────────────────────────────────────────────────────

def load_map(board):
    path = os.path.join(board, ".plan.json")
    if os.path.isfile(path):
        return json.load(open(path, encoding="utf-8")), path
    return {"issues": {}, "memos": {}, "waves": {}, "schedule": {}}, path


def save_map(mp, path):
    json.dump(mp, open(path, "w", encoding="utf-8"), indent=1, sort_keys=True)


def gantt_payload(board, prds, mp, settings):
    """What the local timeline renders: one bar per scheduled leaf, day offsets
    from the plan's hour offsets at `gantt-day` hours per day. Parents weigh
    nothing in the plan, so a zero-length schedule entry is a container and
    folds away; done and parked PRDs carry no bar, only a count."""
    day_h = hours(settings.get("gantt-day", "8h")) or 8.0
    sched = mp.get("schedule", {})
    tasks, unplanned = [], []
    done = parked = containers = 0
    for rel in sorted(prds):
        p = prds[rel]
        st = p["state"]
        if st == "done":
            done += 1
            continue
        if st not in LIVE_STATES:
            parked += 1
            continue
        s = sched.get(rel)
        if not s:
            unplanned.append(rel)
            continue
        if s["end"] <= s["start"]:
            containers += 1
            continue
        try:
            prio = float(p["fm"].get("priority", 0))
        except (TypeError, ValueError):
            prio = 0.0
        needs = p["fm"].get("needs", [])
        needs = needs if isinstance(needs, list) else [needs]
        tasks.append({
            "rel": rel, "name": p["name"], "title": p["title"],
            "board": p.get("board"),
            "state": st,
            "prio": int(prio) if prio == int(prio) else prio,
            "est": round(s["end"] - s["start"], 2),
            "startDay": round(s["start"] / day_h, 4),
            "endDay": round(s["end"] / day_h, 4),
            "wave": mp.get("waves", {}).get(rel),
            # full rels, not basenames: a dependency arrow has to land on a
            # row, and across a master's members a basename names nothing
            "needs": [resolve_need(prds, p, str(n)) or str(n) for n in needs],
        })
    # Every PRD, not only the scheduled ones: the timeline draws what is left,
    # the analytics have to see what is done, parked and estimated too, and a
    # second scan of the same tree to get them would be the more expensive way
    # to say the same thing. `est` here is the PRD's own — spec_data reads every
    # spec file on the board, which is a plan-time cost, not a render one.
    everything = []
    for rel in sorted(prds):
        p = prds[rel]
        try:
            prio = float(p["fm"].get("priority", 0))
        except (TypeError, ValueError):
            prio = 0.0
        everything.append({
            "rel": rel, "name": p["name"], "title": p["title"],
            "state": p["state"], "board": p.get("board"),
            "parent": p.get("parent"),
            "prio": int(prio) if prio == int(prio) else prio,
            "est": round(hours(p["fm"].get("est", "")), 2),
            "actual": round(hours(p["fm"].get("actual", "")), 2),
            "kids": len(p.get("children") or []),
        })
    return {
        "board": board_name(board),
        # a master's members, in plan order — the renderer groups by them
        "boards": [n for n, _ in members(board)],
        "all": everything,
        "history": read_history(board),
        # the states the loop works, then any the user parked work in
        "states": sorted(LIVE_STATES | {"done"}) + sorted(
            {p["state"] for p in prds.values()} - LIVE_STATES - {"done"}),
        "anchor": mp.get("planned_at") or datetime.date.today().isoformat(),
        "dayHours": day_h,
        "workers": str(settings.get("workers", "3")),
        "counts": {"done": done, "parked": parked, "containers": containers},
        "unplanned": unplanned,
        "tasks": tasks,
    }


HISTORY_FILE = ".history.jsonl"


def read_history(board):
    """One line per day, appended by the live service: what the board looked
    like that day. It is the only thing here with a memory — every other number
    is what is true now — so the burn-down is the one chart that cannot be
    derived from a scan."""
    rows = []
    try:
        for line in open(os.path.join(board, HISTORY_FILE), encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        return []
    return rows[-400:]


def write_history(board, prds=None):
    """Today's row, once. Rewrites today's line rather than appending a second,
    so a daemon restarted six times in a day still leaves one point."""
    prds = scan(board) if prds is None else prds
    today = datetime.date.today().isoformat()
    row = {"d": today, "states": {}, "hleft": 0.0, "hdone": 0.0,
           "done": 0, "left": 0}
    for p in prds.values():
        st = p["state"]
        row["states"][st] = row["states"].get(st, 0) + 1
        h = hours(p["fm"].get("est", ""))
        if st == "done":
            row["done"] += 1
            row["hdone"] += h
        elif st in LIVE_STATES:
            row["left"] += 1
            row["hleft"] += h
    row["hleft"], row["hdone"] = round(row["hleft"], 2), round(row["hdone"], 2)
    path = os.path.join(board, HISTORY_FILE)
    rows = [r for r in read_history(board) if r.get("d") != today] + [row]
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    os.replace(tmp, path)
    return row


def cmd_gantt(board, open_after=False):
    mp, _ = load_map(board)
    if not mp.get("schedule") or not mp.get("planned_at"):
        print("gantt: no plan on record — planning first\n")
        cmd_plan(board, None, push=False)
        mp, _ = load_map(board)
    path = renderlib.write(
        board, gantt_payload(board, scan(board), mp, board_settings(board)))
    print(f"gantt: {path}")
    if open_after:
        import webbrowser
        webbrowser.open("file://" + os.path.abspath(path))


# The board blocks on the user, and a user who is not at the terminal cannot see
# that. So the question goes where the person is: a comment on the ticket. The
# reply is the answer — edit.py reads a comment on a `question` PRD as kind
# `answer`, writes it under `## Answers` and sets the PRD back to `open`, which
# is exactly what loop step 2 does with an answer typed in the terminal. The two
# halves are one round trip: the board can be steered by someone who never opens
# a shell.


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


def plan_workers(board, workers):
    if workers is not None:
        return workers
    try:
        return int(board_settings(board).get("workers", 3))
    except ValueError:
        return 3


def needs_index(prds):
    """(by dir name, by (board, name-or-rel)) — what a `needs:` entry is
    looked up in."""
    by_name, local = {}, {}
    for r in sorted(prds):
        by_name.setdefault(os.path.basename(r), []).append(r)
        local.setdefault((prds[r]["board"], os.path.basename(r)), r)
        local.setdefault((prds[r]["board"], prds[r]["local"]), r)
    return by_name, local


def resolve_need(prds, prd, d, idx=None):
    """The rel one `needs:` entry names, or None.

    Own board first, so a member's `needs: sibling` keeps meaning its own
    sibling and joining a master rewrites no member PRD. Across boards the
    form is qualified — `@<member>/<prd>`. A bare name matching PRDs on two
    boards resolves to nothing on purpose: guessing which was meant is how a
    worker gets sent at code another repo has not written."""
    by_name, local = idx or needs_index(prds)
    d = str(d).strip().rstrip("/")
    if d in prds:
        return d
    if (prd.get("board"), d) in local:
        return local[(prd.get("board"), d)]
    same = by_name.get(os.path.basename(d), [])
    return same[0] if len(same) == 1 else None


def resolve_needs(prds, todo, warn=True):
    """rel → the rels it waits on. A parent implicitly needs its undone
    children — work flows to the leaves — and a need on a `done` PRD is
    satisfied."""
    idx = needs_index(prds)
    needs = {}
    for r, p in todo.items():
        deps = p["fm"].get("needs", [])
        deps = deps if isinstance(deps, list) else [deps]
        needs[r] = [c for c in p["children"] if c in todo]
        for d in deps:
            t = resolve_need(prds, p, d, idx)
            if t is None:
                same = idx[0].get(os.path.basename(str(d).strip()), [])
                if warn and len(same) > 1:
                    print(f"plan: {r} needs '{d}' — {len(same)} PRDs of that "
                          f"name ({', '.join(same)}); qualify it as "
                          f"@<board>/<prd>", file=sys.stderr)
                elif warn:
                    print(f"plan: {r} needs '{d}' — no such PRD, ignored",
                          file=sys.stderr)
            elif t in todo and t not in needs[r]:
                needs[r].append(t)
    return needs


def compute_plan(board, workers=None, warn=True):
    """The wave plan as data — None when there is nothing to schedule.

    Separate from the printing because a master board's plan is a function of
    every member's state: it has to be recomputable on a file change, not only
    when somebody remembers to run `plan`. `cmd_plan` prints and pushes what
    this returns; `reconcile` only saves it."""
    settings = board_settings(board)
    workers = plan_workers(board, workers)
    prds = scan(board)
    todo = {r: p for r, p in prds.items() if p["state"] in LIVE_STATES}
    parked = sorted(r for r, p in prds.items()
                    if p["state"] not in LIVE_STATES and p["state"] != "done")
    if not todo:
        return None
    needs = resolve_needs(prds, todo, warn)

    est, feet = {}, {}
    for r, p in todo.items():
        e, f = spec_data(p)
        # complexity is the weight; est is a legacy fallback and is not asked for
        est[r] = (e or float(p["fm"].get("complexity", 0) or 0)
                  or hours(p["fm"].get("est", "")))
        feet[r] = f
    # A parent with live children is a container: the work is in the children,
    # and weighing it too counts the same work twice. It still waits for them.
    for r, p in todo.items():
        if any(c in todo for c in p["children"]):
            est[r] = 0.0
    known = [e for e in est.values() if e > 0]
    avg = (sum(known) / len(known) if known
           else float(settings.get("weight-default", 50) or 50))
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

    # schedule each PRD onto a worker slot — the offsets feed the Gantt dates
    nwaves = max(wave.values())
    schedule, order, t0 = {}, [], 0.0
    for n in range(1, nwaves + 1):
        ms = sorted((r for r in wave if wave[r] == n),
                    key=lambda x: (-prio(x), x))
        order.append(ms)
        if not ms:
            continue
        slots = [0.0] * max(workers, 1)
        for r in ms:
            i = min(range(len(slots)), key=lambda k: slots[k])
            schedule[r] = {"start": t0 + slots[i], "end": t0 + slots[i] + est[r]}
            slots[i] += est[r]
        t0 += max(slots)
    return {"prds": prds, "todo": todo, "parked": parked, "settings": settings,
            "workers": workers, "needs": needs, "est": est, "feet": feet,
            "waves": wave, "schedule": schedule, "order": order,
            "nwaves": nwaves, "wall": t0, "avg": avg,
            "prio": {r: prio(r) for r in todo}}


def reconcile(board):
    """Recompute the waves in place, keeping the anchor day. True when they
    moved.

    A master board's plan spans repos nobody re-plans by hand: a state written
    in one member re-orders the whole board, and a Gantt still drawing
    yesterday's order is worse than one drawn a second late. Re-anchoring is
    what `plan` does; this only re-orders, so the bars keep the day the plan
    was made."""
    r = compute_plan(board, None, warn=False)
    if not r:
        return False
    mp, mp_path = load_map(board)
    if (mp.get("waves") == r["waves"] and mp.get("schedule") == r["schedule"]
            and mp.get("planned_at")):
        return False
    mp["waves"], mp["schedule"] = r["waves"], r["schedule"]
    mp.setdefault("planned_at", datetime.date.today().isoformat())
    save_map(mp, mp_path)
    if os.path.isfile(os.path.join(board, renderlib.VIEW_FILE)):
        renderlib.write(board, gantt_payload(board, r["prds"], mp, r["settings"]))
    return True


def cmd_plan(board, workers, push=False):
    r = compute_plan(board, workers)
    if not r:
        print("plan: nothing to do — no undone PRDs")
        return
    prds, todo, parked = r["prds"], r["todo"], r["parked"]
    est, feet, needs, wave = r["est"], r["feet"], r["needs"], r["waves"]
    mem = [n for n, _ in members(board)]
    print(f"plan: {len(todo)} PRDs in {r['nwaves']} wave(s)"
          f" · workers={r['workers']} · unspecced est'd at {r['avg']:.1f}h"
          + (f" · master of {len(mem) + 1} boards: "
             + ", ".join([os.path.basename(os.path.dirname(board))] + mem)
             if mem else "")
          + (f" · {len(parked)} parked: " + ", ".join(
              f"{os.path.basename(r_)} [{prds[r_]['state']}]" for r_ in parked)
             if parked else ""))
    for n, ms in enumerate(r["order"], start=1):
        if not ms:
            continue
        load = sum(est[x] for x in ms)
        wall = max(r["schedule"][x]["end"] for x in ms) - min(
            r["schedule"][x]["start"] for x in ms)
        print(f"\nwave {n} — {len(ms)} in parallel · Σ{load:.1f}h"
              f" · ~{wall:.1f}h wall")
        for x in ms:
            p = todo[x]
            why = []
            if needs[x]:
                why.append("needs " + ", ".join(os.path.basename(d)
                                                for d in needs[x]))
            if not feet[x]:
                why.append("unspecced")
            print(f"  · {x} [{p['state']}] p{p['fm'].get('priority', 0)}"
                  f" {est[x]:.1f}h" + (f"  ({'; '.join(why)})" if why else ""))
    print(f"\n≈ {r['wall']:.1f}h wall-clock @ {r['workers']} workers")

    mp, mp_path = load_map(board)
    mp["waves"] = r["waves"]
    mp["schedule"] = r["schedule"]
    mp["planned_at"] = datetime.date.today().isoformat()
    save_map(mp, mp_path)
    lpath = renderlib.write(board, gantt_payload(board, prds, mp, r["settings"]))
    print(f"\nview: {lpath}")
    print(f"      {serve_url(board)}   (live, with the board's other views)")


def serve_url(board):
    """Where the live view is, if the service is up. The file above always
    works; this one is the same render with the detail pane and the edits."""
    port = os.environ.get("PEARDE_PORT", "8443")
    return f"http://127.0.0.1:{port}/board/{board_name(board)}"


def cmd_status(board):
    prds = scan(board)
    ms = scan_memos(board)
    bad = memolib.check(board) if memolib.scan(board) else []
    memo_note = ""
    if ms:
        memo_note = (f" · {len(ms)} memos"
                     + (f" ({len(bad)} failing the check)" if bad else ""))
    mem = members(board)
    print(f"board: {board} · {len(prds)} PRDs{memo_note}"
          + (f" · master of {len(mem)} member board(s)" if mem else ""))
    for name, path in mem:
        if not os.path.isdir(path):
            print(f"  @{name:14} MISSING — {path}")
            continue
        n = len(_scan_one(path))
        own = "" if os.path.isfile(os.path.join(path, "settings.md")) else \
            " · no settings.md"
        print(f"  @{name:14} {n:4} PRDs · {path}{own}")
    print(f"view: {serve_url(board)}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    cmd = args[0] if args else "status"
    board = find_board(args[1] if len(args) > 1 else None)
    if cmd == "plan":
        workers = next((int(f.split("=")[1]) for f in flags
                        if f.startswith("--workers=")), None)
        cmd_plan(board, workers, push="--no-push" not in flags)
    elif cmd == "reconcile":
        moved = reconcile(board)
        print(f"reconcile: {'waves re-ordered' if moved else 'no change'}")
    elif cmd == "members":
        mem = members(board)
        if not mem:
            print(f"{board} is not a master board — no members: in settings.md")
        for name, path in mem:
            mark = "" if os.path.isdir(path) else "  MISSING"
            print(f"@{name}\t{path}{mark}")
    elif cmd == "gantt":
        cmd_gantt(board, open_after="--open" in flags)
    elif cmd == "status":
        cmd_status(board)
    else:
        die(f"unknown command '{cmd}' — plan | reconcile | gantt"
            " | members | status")


if __name__ == "__main__":
    main()
