#!/usr/bin/env python3
"""pearde plan — the board, read and ordered.

    plan.py plan  [board] [--workers N]   the frontier and the dispatch order
    plan.py reconcile [board]             re-order the schedule, keep the anchor
    plan.py gantt [board] [--open]        render the view to prds/.view.html
    plan.py members [board]               what a master board merges
    plan.py status [board]                the board, its members, its memos

board = the prds/ directory, a directory holding one, or omitted to walk up
from the cwd. The plan persists in prds/.plan.json. The view reads it.

Python 3 stdlib only.
"""
import datetime
import hashlib
import html
import json
import math
import os
import re
import subprocess
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
# edges, the schedule, the merged mirror — lives at the master.
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
    """(weight, footprints) unioned over specs/*.md, plus the PRD's own
    `footprint:`. The weight is each spec's `complexity`, falling back to its
    `est`. A PRD declares its footprint before it is specced and while an
    implementer holds its spec files — the planner needs the paths either way,
    and frontmatter on prd.md is the one place no worker writes."""
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


BOX_RE = re.compile(r"^\s*[-*]\s+\[([ xX])\]", re.M)


def acceptance_of(text):
    """(closed, total) acceptance boxes in one spec's text.

    `## Acceptance` only. A box anywhere else in a spec is a note the analyst
    left itself, and counting it would make the number say something other
    than "how much of the contract is standing"."""
    closed = total = 0
    for sec in re.split(r"(?m)^##\s+", text)[1:]:
        head = sec.split("\n", 1)[0].strip().lower()
        if not head.startswith("acceptance"):
            continue
        for box in BOX_RE.findall(sec):
            total += 1
            closed += box.lower() == "x"
    return closed, total


def acceptance(prd):
    """(closed, total) over every spec of one PRD.

    This is the only thing on the board that moves while a worker works.
    Everything else — the state, the est, the report — is written at the
    transitions either side of it, so a plan that reads nothing else stands
    still for the whole of the run it is supposed to be showing."""
    sdir = os.path.join(prd["dir"], "specs")
    closed = total = 0
    for f in sorted(os.listdir(sdir)) if os.path.isdir(sdir) else []:
        if not f.endswith(".md"):
            continue
        try:
            text = open(os.path.join(sdir, f), encoding="utf-8").read()
        except OSError:
            continue
        c, t = acceptance_of(text)
        closed, total = closed + c, total + t
    return closed, total


# The states in which a worker holds the PRD and its acceptance boxes are the
# live record of the run. `analyzing` holds it too, but an analyst writes the
# boxes rather than closing them — its progress is the spec files appearing.
HOLDING_STATES = {"claimed", "blocked"}

CLAIM_TS_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?)?"
    r"(?:Z|[+-]\d{2}:?\d{2})?)")


def claim_of(fm):
    """`claim: <worker> <started>` → {"who", "since"}, or None.

    The timestamp is whatever ISO-ish thing the orchestrator wrote. The worker
    name is the rest. Neither is required — a claim with no timestamp still
    says who holds the PRD."""
    raw = fm.get("claim")
    if not raw or isinstance(raw, list):
        return None
    raw = str(raw).strip()
    m = CLAIM_TS_RE.search(raw)
    who = (raw[:m.start()] + raw[m.end():]).strip() if m else raw
    return {"who": who, "since": m.group(1) if m else ""}


def standing(prd):
    """(fraction closed, closed, total, collect) for one PRD.

    `collect` is the whole point of reading the boxes: a PRD whose every
    acceptance box is closed while a worker still holds it is finished work
    waiting to be committed and set `done`. Until that happens every PRD
    behind it waits too, so it is the most valuable thing on the board."""
    closed, total = acceptance(prd)
    frac = (closed / total) if total else 0.0
    held = prd["state"] in HOLDING_STATES
    return frac, closed, total, bool(held and total and closed == total)


def hours(v):
    if not v or isinstance(v, list):
        return 0.0
    v = str(v).strip()
    m = re.match(r"^([\d.]+)\s*([mhd]?)$", v)
    if not m:
        return 0.0
    n, unit = float(m.group(1)), m.group(2)
    return n / 60 if unit == "m" else n * 8 if unit == "d" else n


# The states the loop moves work through. A board state outside LIVE_STATES is
# the user's own and terminal to the loop — the planner does not schedule it,
# and the view lists it as parked rather than folding it into `open`.
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
        # dirname's fixpoint is not always "/" — a Windows drive root ("C:/")
        # maps to itself, and without this guard the walk never exits
        nxt = os.path.dirname(d)
        if nxt == d:
            break
        d = nxt
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


# ── lanes: what main has not seen ─────────────────────────────────────────────
# Work happens on a branch per PRD — `lane/<slug>` or `lane/<n>-<slug>` — and
# it lands by merging into that repo's main.
# A lane that is still unmerged is work that exists on this machine and nowhere
# else, no matter what the board says about it.
#
# The board and git each know half of it, and neither half is enough: the board
# knows the work is finished and its acceptance boxes are closed, git knows main
# has never seen the commits. Crossing them is the whole point — a finished PRD
# whose lane is merged is history, an unmerged lane whose PRD is still open is
# in flight, and only the intersection is a queue of things to land.

LANE_RE = re.compile(r"^lane/(?:(\d+)-)?(.+?)(?:-\d+)?$")
LANE_TTL = 3.0          # git is cheap, but not once per row per render
_LANES = {}             # board path -> (expires, scan)


def repo_root(path):
    """The repo a board sits in, by walk-up. `git rev-parse --show-toplevel`
    answers the same question and costs a fork, and the watcher asks once a
    second per board — so it walks."""
    d = os.path.abspath(path)
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return d
        nxt = os.path.dirname(d)
        if nxt == d:
            return None
        d = nxt


def ref_stamp(path):
    """The git side of a board, as (mtime, size) over the refs a merge moves.
    Pure stats: this is what the watcher polls to notice that a lane landed,
    and it must not fork anything. A `.git` file (a worktree) has no refs of
    its own here and stamps as nothing."""
    root = repo_root(path)
    g = os.path.join(root, ".git") if root else None
    if not g or not os.path.isdir(g):
        return ()
    out = []
    for rel in ("refs/heads", "packed-refs", "HEAD"):
        try:
            st = os.stat(os.path.join(g, rel))
            out.append((rel, st.st_mtime_ns, st.st_size))
        except OSError:
            out.append((rel, 0, 0))
    return (root, tuple(out))


def git(root, *args):
    """stdout, or None if git said no. Never raises: a board that is not in a
    repo is an ordinary case here, not an error."""
    try:
        r = subprocess.run(("git", "-C", root) + args,
                           capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def scan_lanes(path):
    """{"root", "ahead", "lanes": {slug: {"branch"}}} for one board.

    `ahead` is main's commits that origin has not got — None when the repo has
    no remote at all, which is a different thing from being in sync and is
    drawn as such. A board outside a repo scans to nothing and says so quietly.

    Only `lane/` branches count — the agent worktrees (`worktree-wf_*`) are
    scratch, not lanes."""
    root = repo_root(path)
    if not root:
        return {"root": None, "ahead": None, "lanes": {}}
    lanes = {}
    out = git(root, "branch", "--no-merged", "main",
              "--format=%(refname:short)") or ""
    for b in out.split("\n"):
        m = LANE_RE.match(b.strip())
        if m:
            slug = m.group(2)
            # a retry (`-2`, `-3`) is the same lane; first branch name wins
            if slug not in lanes:
                lanes[slug] = {"branch": b.strip()}
    ahead = None
    if git(root, "remote", "get-url", "origin"):
        n = git(root, "rev-list", "--count", "origin/main..main")
        ahead = int(n.strip()) if n and n.strip().isdigit() else None
    return {"root": root, "ahead": ahead, "lanes": lanes}


def lanes(path):
    now = time.time()
    hit = _LANES.get(path)
    if hit and hit[0] > now:
        return hit[1]
    got = scan_lanes(path)
    _LANES[path] = (now + LANE_TTL, got)
    return got


def landing(board, everything):
    """(rows, repos) — the lanes this machine is holding, in the order they
    should land.

    A row is one unmerged lane matched to the PRD it was cut for, by the slug
    both share. `ready` marks the ones the board says are finished — state
    `done`, or held with every acceptance box closed — and those are the ones
    to merge. The rest are in flight and drawn as such: a lane at 50/54 boxes
    is worth seeing next to the queue it is about to join.

    Ready first, then by priority, then by name for stability — merging is
    collect's work, and collect goes best door first, not oldest first."""
    roots = members(board) or [(None, board)]
    rows, repos = [], []
    for name, path in roots:
        got = lanes(path)
        if got["root"] is None:
            continue
        repos.append({"board": name or board_name(board),
                      "ahead": got["ahead"], "lanes": len(got["lanes"])})
        if not got["lanes"]:
            continue
        by_slug = {}
        for t in everything:
            if (t.get("board") or None) == name:
                by_slug.setdefault(os.path.basename(t["rel"]), t)
        for slug, ln in sorted(got["lanes"].items()):
            t = by_slug.get(slug)
            boxes = (t or {}).get("boxes") or [0, 0]
            state = (t or {}).get("state") or "?"
            rows.append({
                "slug": slug, "branch": ln["branch"],
                "board": name, "rel": (t or {}).get("rel") or slug,
                "name": (t or {}).get("name") or slug,
                "title": (t or {}).get("title") or "",
                "state": state, "boxes": boxes,
                "prio": (t or {}).get("prio") or 0,
                "est": (t or {}).get("est") or 0,
                # the board's own claim that the work is finished and tested:
                # `done`, or every acceptance box closed on a held PRD
                "ready": state == "done" or bool((t or {}).get("collect")),
                # a lane whose slug matches no PRD at all — the PRD was renamed
                # or never existed. Shown, because an unmerged branch nobody
                # can name is exactly the thing that gets lost
                "orphan": t is None,
            })
    rows.sort(key=lambda r: (not r["ready"], -r["prio"], r["slug"]))
    repos.sort(key=lambda r: str(r["board"]))
    return rows, repos


# ── map file ──────────────────────────────────────────────────────────────────

def load_map(board):
    path = os.path.join(board, ".plan.json")
    if os.path.isfile(path):
        return json.load(open(path, encoding="utf-8")), path
    return {"after": {}, "schedule": {}}, path


def save_map(mp, path):
    json.dump(mp, open(path, "w", encoding="utf-8"), indent=1, sort_keys=True)


def gantt_payload(board, prds, mp, settings):
    """What the local timeline renders: one bar per scheduled leaf, day offsets
    from the plan's hour offsets at `gantt-day` hours per day. Parents weigh
    nothing in the plan, so a zero-length schedule entry is a container and
    folds away.

    Done and parked PRDs carry a bar too — `past: true` and `parked: true`.
    The plan is only the half in front of us. The track runs from the first
    thing that landed to the vision — a timeline that starts at now shows a
    board that looks perpetually at its own beginning. The renderer lays
    the past out to the LEFT of now and pins the parked at now, so where we
    are is a place on the whole track, not kilometre zero of a shrinking
    one."""
    day_h = hours(settings.get("gantt-day", "8h")) or 8.0
    sched = mp.get("schedule", {})
    tasks, unplanned = [], []
    done = parked = containers = 0
    for rel in sorted(prds):
        p = prds[rel]
        st = p["state"]
        weight = round(float(p["fm"].get("complexity", 0) or 0)
                       or hours(p["fm"].get("est", "")), 2)
        try:
            pr = float(p["fm"].get("priority", 0))
        except (TypeError, ValueError):
            pr = 0.0
        nd = p["fm"].get("needs", [])
        nd = nd if isinstance(nd, list) else [nd]
        base = {
            "rel": rel, "name": p["name"], "title": p["title"],
            "board": p.get("board"), "state": st,
            "prio": int(pr) if pr == int(pr) else pr,
            "est": weight, "boxes": [0, 0], "part": 0,
            "held": False, "collect": False, "claim": None,
            "needs": [resolve_need(prds, p, str(n)) or str(n) for n in nd],
        }
        if st == "done":
            done += 1
            if weight > 0:
                tasks.append(dict(base, past=True))
            continue
        if st not in LIVE_STATES:
            parked += 1
            if weight > 0:
                tasks.append(dict(base, parked=True))
            continue
        s = sched.get(rel)
        if not s:
            unplanned.append(rel)
            continue
        if s["end"] <= s["start"]:
            containers += 1
            continue
        # what the run itself has closed so far, and who is holding it. Read
        # per PRD rather than once at plan time: this is the half of the
        # payload that moves between two transitions, and a view that only
        # learns it when `plan` runs is not live.
        frac, closed, total, ready_to_collect = standing(p)
        tasks.append(dict(base,
            est=round(s["end"] - s["start"], 2),
            startDay=round(s["start"] / day_h, 4),
            endDay=round(s["end"] / day_h, 4),
            # a footprint clash, serialized pairwise: this PRD starts when
            # those end. An edge, so nothing else on the board waits with it
            after=mp.get("after", {}).get(rel, []),
            boxes=[closed, total],
            part=round(frac, 4),
            held=st in HOLDING_STATES or st == "analyzing",
            collect=ready_to_collect,
            claim=claim_of(p["fm"]),
        ))
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
        # boxes for live PRDs only: a `done` PRD's specs are history, and
        # reading every one of them is the plan-time cost this loop avoids
        closed, total, held = 0, 0, p["state"] in HOLDING_STATES
        if p["state"] in LIVE_STATES:
            closed, total = acceptance(p)
        everything.append({
            "rel": rel, "name": p["name"], "title": p["title"],
            "state": p["state"], "board": p.get("board"),
            "parent": p.get("parent"),
            "prio": int(prio) if prio == int(prio) else prio,
            "est": round(hours(p["fm"].get("est", "")), 2),
            "actual": round(hours(p["fm"].get("actual", "")), 2),
            # the weight the board schedules by — complexity, falling back
            # to est. est and actual are records, never inputs
            "weight": round(float(p["fm"].get("complexity", 0) or 0)
                            or hours(p["fm"].get("est", "")), 2),
            "boxes": [closed, total],
            "collect": bool(held and total and closed == total),
            "kids": len(p.get("children") or []),
        })
    land, repos = landing(board, everything)
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
        "counts": {"done": done, "parked": parked, "containers": containers,
                   "collect": sum(1 for t in tasks if t["collect"]),
                   "held": sum(1 for t in tasks if t["held"])},
        "unplanned": unplanned,
        "tasks": tasks,
        # what this machine is holding that main has never seen
        "landing": land, "repos": repos,
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
        h = (float(p["fm"].get("complexity", 0) or 0)
             or hours(p["fm"].get("est", "")))
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
        cmd_plan(board, None)
        mp, _ = load_map(board)
    path = renderlib.write(
        board, gantt_payload(board, scan(board), mp, board_settings(board)))
    print(f"gantt: {path}")
    if open_after:
        import webbrowser
        webbrowser.open("file://" + os.path.abspath(path))



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
    """The plan as data — None when there is nothing to schedule.

    Separate from the printing because a master board's plan is a function of
    every member's state: it has to be recomputable on a file change, not only
    when somebody remembers to run `plan`. `cmd_plan` prints what this
    returns. `reconcile` only saves it."""
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
        # complexity is the weight. est is the fallback for an unscored PRD
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

    # In flight, a PRD weighs only what is LEFT of it. An implementer closes an
    # acceptance box as it lands the check behind it, so the specs on disk say
    # how much of a held PRD is already standing — and a plan that keeps
    # weighing the whole of it stands still exactly while the board is moving
    # fastest. The floor is a twentieth: collecting the work is itself work,
    # and a bar of zero width is a PRD that vanished off the timeline.
    boxes, collect = {}, []
    for r, p in todo.items():
        frac, closed, total, ready_to_collect = standing(p)
        boxes[r] = (closed, total)
        if ready_to_collect:
            collect.append(r)
        if total and p["state"] in HOLDING_STATES:
            est[r] = max(est[r] * (1 - frac), est[r] * 0.05)

    def prio(r):
        try:
            return float(todo[r]["fm"].get("priority", 0))
        except ValueError:
            return 0.0

    # A footprint clash serializes the PAIR, never a round. An agent starts
    # the moment its own gates clear, so a barrier would hold back every PRD
    # it shares nothing with. The clash is an edge: the lower-priority PRD is
    # `after` the higher one, and only that pair is ordered. Two PRDs already
    # ordered by a dependency path need no edge — the path is the order.
    edges = {r: list(needs[r]) for r in todo}

    def path(a, b, _seen=None):
        """a reaches b along edges — a runs after b already."""
        if _seen is None:
            _seen = set()
        if a == b:
            return True
        _seen.add(a)
        return any(d not in _seen and path(d, b, _seen) for d in edges[a])

    after = {r: [] for r in todo}
    ranked = sorted(todo, key=lambda x: (-prio(x), x))
    for i, r in enumerate(ranked):
        for s in ranked[i + 1:]:
            if (overlap(feet[r], feet[s])
                    and not path(s, r) and not path(r, s)):
                after[s].append(r)      # s yields: r outranks it
                edges[s].append(r)

    # topological order over needs + after; a cycle in `needs` is an error
    # (an `after` edge is only ever added between unordered PRDs, so it
    # cannot close one)
    depth, visiting = {}, set()
    def dp(r):
        if r in depth:
            return depth[r]
        if r in visiting:
            die(f"needs cycle through {r}")
        visiting.add(r)
        depth[r] = 1 + max((dp(d) for d in edges[r]), default=0)
        visiting.discard(r)
        return depth[r]
    for r in todo:
        dp(r)

    # what dispatching a PRD opens: the weight transitively waiting behind it.
    # The frontier orders by this — the door that opens widest goes first
    feeds = {r: [] for r in todo}
    for r, ds in edges.items():
        for d in ds:
            feeds[d].append(r)
    down = {}
    for r in sorted(todo, key=lambda x: -depth[x]):
        acc = set()
        for s in feeds[r]:
            acc.add(s)
            acc |= down[s]
        down[r] = acc
    unblocks = {r: sum(est[s] for s in down[r]) for r in todo}

    # The calendar is a simulation, not the plan: dispatch every PRD the
    # moment its edges are done and a worker is free, best door first. The
    # dispatch order it visits IS the plan's order. The offsets only feed the
    # Gantt dates — a staffing guess, never a fact about the plan.
    nslots = max(workers, 1)
    left = {r: len(edges[r]) for r in todo}
    ready = [r for r in todo if not left[r]]
    running, schedule, order, t0 = [], {}, [], 0.0
    def take(pool):
        best = min(pool, key=lambda x: (-unblocks[x], -prio(x), x))
        pool.remove(best)
        return best
    def finish(r):
        for s in feeds[r]:
            left[s] -= 1
            if not left[s]:
                ready.append(s)
    while ready or running:
        # a container weighs nothing and holds no worker — it folds away the
        # moment its children are done
        while ready:
            zero = [r for r in ready if est[r] <= 0]
            if not zero:
                break
            for r in zero:
                ready.remove(r)
                schedule[r] = {"start": t0, "end": t0}
                order.append(r)
                finish(r)
        while ready and len(running) < nslots:
            r = take(ready)
            schedule[r] = {"start": t0, "end": t0 + est[r]}
            order.append(r)
            running.append((schedule[r]["end"], r))
        if not running:
            continue
        running.sort()
        t0, r = running.pop(0)
        finish(r)
    wall = max((s["end"] for s in schedule.values()), default=0.0)
    return {"prds": prds, "todo": todo, "parked": parked, "settings": settings,
            "workers": workers, "needs": needs, "est": est, "feet": feet,
            "boxes": boxes, "collect": sorted(collect),
            "after": after, "schedule": schedule, "order": order,
            "unblocks": unblocks, "wall": wall, "avg": avg,
            "prio": {r: prio(r) for r in todo}}


def reconcile(board):
    """Recompute the schedule in place, keeping the anchor day. True when it
    moved.

    A master board's plan spans repos nobody re-plans by hand — a state
    written in one member re-orders the whole board. Re-anchoring is `plan`'s
    work. This only re-orders, so the bars keep the day the plan was made."""
    r = compute_plan(board, None, warn=False)
    if not r:
        return False
    mp, mp_path = load_map(board)
    if (mp.get("after") == r["after"] and mp.get("schedule") == r["schedule"]
            and mp.get("planned_at")):
        return False
    mp["after"], mp["schedule"] = r["after"], r["schedule"]
    mp.setdefault("planned_at", datetime.date.today().isoformat())
    save_map(mp, mp_path)
    if os.path.isfile(os.path.join(board, renderlib.VIEW_FILE)):
        renderlib.write(board, gantt_payload(board, r["prds"], mp, r["settings"]))
    return True


def cmd_plan(board, workers):
    r = compute_plan(board, workers)
    if not r:
        print("plan: nothing to do — no undone PRDs")
        return
    prds, todo, parked = r["prds"], r["todo"], r["parked"]
    est, feet, needs, after = r["est"], r["feet"], r["needs"], r["after"]
    sched, unblocks = r["schedule"], r["unblocks"]
    mem = [n for n, _ in members(board)]
    print(f"plan: {len(todo)} PRDs"
          f" · workers={r['workers']} · unspecced est'd at {r['avg']:.1f}w"
          + (f" · master of {len(mem) + 1} boards: "
             + ", ".join([os.path.basename(os.path.dirname(board))] + mem)
             if mem else "")
          + (f" · {len(parked)} parked: " + ", ".join(
              f"{os.path.basename(r_)} [{prds[r_]['state']}]" for r_ in parked)
             if parked else ""))
    # Before everything else, because it comes before everything else: every
    # PRD here is finished work, and every PRD waiting on one of them waits
    # until it is committed and set `done`.
    if r["collect"]:
        print(f"\ncollect: {len(r['collect'])} finished, waiting to be closed")
        for x in r["collect"]:
            c, t = r["boxes"][x]
            print(f"  ✓ {x} [{todo[x]['state']}] {c}/{t} boxes closed")
    # The frontier, then the queue. There are no rounds: a PRD starts the
    # moment its own gates clear, so the plan is the dispatch order and what
    # gates each entry — not waves that would hold unrelated work hostage to
    # the slowest member of a round.
    frontier = [x for x in r["order"]
                if not needs[x] and not after[x] and est[x] > 0]
    if frontier:
        print(f"\nready now — {len(frontier)} in parallel, widest door first")
        for x in frontier:
            p = todo[x]
            hot = p["state"] in ("question", "blocked", "refine", "failed")
            print(f"  · {x} [{p['state']}] p{p['fm'].get('priority', 0)}"
                  f" {est[x]:.1f}w · unblocks {unblocks[x]:.0f}w"
                  + ("  (waiting on you)" if hot
                     else "" if feet[x] else "  (unspecced)"))
    gated = [x for x in r["order"] if (needs[x] or after[x]) and est[x] > 0]
    if gated:
        print("\nthen, as gates clear — dispatch order")
        for x in gated:
            p = todo[x]
            why = []
            if needs[x]:
                why.append("needs " + ", ".join(os.path.basename(d)
                                                for d in needs[x]))
            if after[x]:
                why.append("after " + ", ".join(os.path.basename(d)
                                                for d in after[x])
                           + " (footprint)")
            if not feet[x]:
                why.append("unspecced")
            print(f"  · {x} [{p['state']}] p{p['fm'].get('priority', 0)}"
                  f" {est[x]:.1f}w" + (f"  ({'; '.join(why)})" if why else ""))
    print(f"\n≈ {r['wall']:.1f}w wall @ {r['workers']} workers — a staffing"
          " guess, not a promise. The dependency structure above is the plan")

    mp, mp_path = load_map(board)
    mp["after"] = r["after"]
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
        cmd_plan(board, workers)
    elif cmd == "reconcile":
        moved = reconcile(board)
        print(f"reconcile: {'schedule re-ordered' if moved else 'no change'}")
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
