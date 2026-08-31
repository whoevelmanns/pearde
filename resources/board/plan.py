#!/usr/bin/env python3
"""pearde plan — the board, read and ordered.

    plan.py plan  [board] [--workers N]   the frontier and the dispatch order
    plan.py reconcile [board]             re-order the schedule, keep the anchor
    plan.py gantt [board] [--open]        render the view to prds/.view.html
    plan.py calibrate [board]             fit hours-per-weight from every done
                                          PRD with an `actual:` on every
                                          registered board; the view prints
                                          real hours beside weight from it
    plan.py members [board]               what a master board merges
    plan.py status [board]                the board, its members, its memos
    plan.py example <dir>                 copy the example board to <dir> —
                                          an empty or new directory; never
                                          run in place
    plan.py vision [board] [--json|--next|--check]
                                          the axis prds/vision.md declares:
                                          depth per PRD, the critical chain,
                                          the off-axis set

board = the prds/ directory, a directory holding one, or omitted to walk up
from the cwd. The plan persists in prds/.plan.json. The view reads it.

Python 3 stdlib only.
"""
import collections
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
import workflows as wflib  # noqa: E402 — the skill root, one dir up

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
    # `^` as well as `\s+`: a value that is ONLY a comment is an empty value.
    # `est:   # the weight, only when complexity is absent` — the template's
    # own line — parsed to the comment TEXT while the leading run of spaces was
    # eaten by KEY_RE, so every reader of `est` got a sentence where a duration
    # was meant. `hours()` read it as 0.0 in silence; `dur()` reports it, which
    # is how it was found. A `#` inside a word (`repo: a#b`) is still a `#`.
    return re.sub(r"(^|\s+)#.*$", "", v).strip().strip("\"'")


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
                where = f"{prd['rel']}/specs/{f}"
                est += (num(fm, "complexity", where)
                        or dur(fm, "est", where))
    return est, qualify_paths(prd, [f.rstrip("/") for f in feet if f])


# Deliberately NOT `opens_an_unticked_box`, and deliberately left as it was
# when the gates widened. It answers a different question over a different
# population: the boxes under `## Acceptance` in `specs/*.md`, counted both
# ways to make a progress fraction, where `opens_an_unticked_box` reads the
# whole of `prd.md` to make a verdict. Its `[ xX]` capture is the fraction's
# alphabet — `[~]` is neither counted nor closed by it, because a struck box
# is a contract term withdrawn rather than a term met, and folding it into
# `closed/total` would move a bar that nothing was built behind. Matching it
# to the gates would be matching two rules that answer two questions.
#
# What it costs, said plainly because a reader meets it and not the argument
# above: a spec's Acceptance box spelled `+ [ ]`, `- []`, `1. [ ]` or with a
# tab after the marker is invisible to this pattern ENTIRELY — not in
# `closed`, not in `total`. So `closed == total` can be true while a contract
# term is still open, and the board offers the PRD at a clean n/n. That is
# survivable only because the `done` gates never read a spec at all
# (`done_boxes_are_ticked.rs` filters on `name == "prd.md"`), so no spec box
# in any spelling can make `collect` name a PRD a gate would refuse. An
# analyst writing `- [ ]` is what keeps the fraction honest.
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


def strip_list_marker(rest):
    """What follows one Markdown list marker at the front of `rest`, or `None`
    when `rest` does not open a list item.

    A port of `strip_list_marker` in
    `shared/shared/tests/done_boxes_are_ticked.rs`, whose body mitosys, model
    and realm adopted on 2026-08-28 (`@infra/gates-adopt-the-best-matcher`).
    Kept as its own function so it can be read beside the Rust it mirrors.

    The three bullets are Markdown's three. The ordered arm is GFM's: `digits
    > 9` is GFM's own bound on an ordered marker, and it is what keeps a year
    or a version number from being read as a list marker; `)` is admitted
    beside `.` because GFM admits both."""
    if rest[:1] in ("-", "*", "+"):
        return rest[1:]
    digits = len(rest) - len(rest.lstrip("0123456789"))
    if digits == 0 or digits > 9:
        return None
    rest = rest[digits:]
    return rest[1:] if rest[:1] in (".", ")") else None


def opens_an_unticked_box(line):
    """True when `line` opens an unticked checkbox: a list marker, then a
    bracket pair holding nothing but whitespace.

    The marker is any of Markdown's three bullets or an ordered marker, and
    the gap between marker and bracket is any run of spaces, because all of
    those render as the same open box in every viewer the board is read in.
    A reader matching one spelling only is one a stray `*`-bulleted box walks
    past, and a board file is prose, written by hand, in five repositories.

    A ticked box and a struck box are closures and do not match: their
    brackets are not empty. `- [~]` is a box whose bar the code did not
    clear, closed with a reason beside it — never work that is merely still
    owed.

    This body is the four gates' body, which is the point: `collect` naming a
    PRD a gate would reject is the defect `body_has_open_box` exists to
    remove, and it comes back the moment the two disagree about what a box
    is."""
    rest = strip_list_marker(line.lstrip())
    if rest is None:
        return False
    rest = rest.lstrip(" ")
    if not rest.startswith("["):
        return False
    rest = rest[1:]
    end = rest.find("]")
    return end >= 0 and not rest[:end].strip()


def body_has_open_box(prd):
    """True when `prd.md` itself still carries an unticked box.

    The specs are not the whole contract. All four trees' `done` gates read
    the boxes in `prd.md` over the whole file, under every heading — mitosys's
    was scoped under `## Acceptance` until 2026-08-28 and is not any more — so
    a PRD whose specs are all closed can still be one the gate refuses.
    Clearing what the gates clear is what `collect` has to do, because saying
    "collect" on a PRD a gate would reject is how a board manufactures the
    `done`-with-open-boxes defect it is trying to remove.

    The match is `opens_an_unticked_box`, the gates' own matcher, not a
    literal `- [ ]`: a `* [ ]` box is red to every tree's gate, and until
    2026-08-28 it was invisible here. `- [~]` stays a closure under it. This
    is the one place the marker set matters, which is why it is not
    `acceptance_of`'s `== "x"` test."""
    try:
        text = open(os.path.join(prd["dir"], "prd.md"), encoding="utf-8").read()
    except OSError:
        return False
    return any(opens_an_unticked_box(l) for l in text.splitlines())


def standing(prd):
    """(fraction closed, closed, total, collect) for one PRD.

    `collect` is the whole point of reading the boxes: a PRD whose every
    acceptance box is closed while a worker still holds it is finished work
    waiting to be committed and set `done`. Until that happens every PRD
    behind it waits too, so it is the most valuable thing on the board.

    `frac`/`closed`/`total` stay the SPECS' numbers — they are the only thing
    that moves while a worker works, which is what the lane bar is drawn
    from. `collect` is the stricter question and answers from `prd.md` too;
    the two deliberately disagree, and `prds/memos/done-counts-which-boxes.md`
    is why."""
    closed, total = acceptance(prd)
    frac = (closed / total) if total else 0.0
    held = prd["state"] in HOLDING_STATES
    ready = bool(held and total and closed == total
                 and not body_has_open_box(prd))
    return frac, closed, total, ready


def hours(v):
    if not v or isinstance(v, list):
        return 0.0
    v = str(v).strip()
    m = re.match(r"^([\d.]+)\s*([mhd]?)$", v)
    if not m:
        return 0.0
    try:
        n = float(m.group(1))
    except ValueError:   # `..`, `1.2.3` — the shape matches, the number does not
        return 0.0
    unit = m.group(2)
    return n / 60 if unit == "m" else n * 8 if unit == "d" else n


# ── numbers a person typed ───────────────────────────────────────────────────
# Every weight on this board is hand-written: `complexity` on every spec by
# every analyst the board has ever dispatched, `priority` on every prd.md,
# `weight-default`, `gantt-day` and `claim-ttl` in settings.md. The population
# of writers is the population of workers, so the failure mode is a typo — and
# a bare `float()` over one of them turns that typo into a traceback in `scan`,
# step 1 of every round, that names no PRD and stops every session on the
# board. Nothing here reads a number off a file a person wrote except through
# `num` and `dur`.
#
# A bad value reads as 0.0, which is what an UNSCORED value already reads as,
# and that is the whole of the decision: `compute_plan` and `weight_of` weigh
# an unscored PRD at the board average and `progress_terms` leaves it out of
# the average it computes, so a typo is weighed as "we do not know this one's
# size" rather than as free. What would be wrong is the SILENCE — a weight
# that quietly becomes 0 is a wrong number that looks like a real one, and it
# moves the PRD in the plan and in the progress percentage — so every bad
# value is said out loud, on stderr, naming the file a person has to open.
# Once per (file, key, value), never once per read: `complexity` is read by
# five functions in a round and one typo is one problem.
_BAD_SEEN = set()
# a duration that is honestly zero — `0`, `0h`, `0.0m` — so `dur` does not
# report the one value `hours()` and a broken value agree on
ZERO_RE = re.compile(r"^0*\.?0*\s*[mhd]?$")


def bad_value(where, key, v):
    """Say once that a hand-written value is not a number. Never raises."""
    seen = (str(where), str(key), repr(v))
    if seen in _BAD_SEEN:
        return
    _BAD_SEEN.add(seen)
    print(f"plan: {where or '?'} — {key}: {v!r} is not a number, weighed as "
          f"unscored", file=sys.stderr)


def num(fm, key, where="", default=0):
    """A plain number off frontmatter — `complexity`, `priority`,
    `weight-default`. 0.0 when absent or empty, 0.0 AND a report when it is
    there and is not a number. Never raises."""
    v = fm.get(key, default)
    if v is None or v == "":
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        bad_value(where, key, v)
        return 0.0


def dur(fm, key, where="", default=""):
    """A duration off frontmatter — `est`, `actual`, `gantt-day` — in hours.
    `hours()` reads the shapes; this names the file when a value is not one of
    them. 0.0 when absent or unreadable. Never raises."""
    v = fm.get(key, default)
    if v is None or v == "":
        return 0.0
    h = hours(v)
    if h == 0.0 and not ZERO_RE.match(str(v).strip()):
        bad_value(where, key, v)
    return h


# ── silence ──────────────────────────────────────────────────────────────────
# The board cannot see a worker. What it can see is files: an implementer
# writes in the repo, an analyst's probe lives in the PRD folder, and either
# moving is a live worker. A claim whose files have not moved for longer than
# `claim-ttl` is silent. `silent_of` is the one rule — the scan line, the
# page's row and `sweep` read it from here, so none of them can disagree about
# which claim has gone quiet. Read off files, never off a process.
CLAIM_TTL = "30m"
SILENT_STATES = {"claimed", "analyzing"}   # the in-flight band, and only it


def claim_ttl(settings):
    """`claim-ttl` from settings.md, in minutes. `30m`, `2h`, `1d` read as
    `hours()` reads them; a bare number is minutes. Default 30."""
    v = str(settings.get("claim-ttl", CLAIM_TTL) or CLAIM_TTL).strip()
    if v.isdigit():
        return float(v)
    h = hours(v)
    if h <= 0:
        bad_value("settings.md", "claim-ttl", v)
        return 30.0
    return h * 60


def prd_repo(prd):
    """Where the PRD's code lives — `collect`'s rule: `repo:` that is a
    directory, absolute or relative to the board's repo, else the board's own
    repo. The footprint silence is read over is the one collect commits."""
    root = (repo_root(prd["board_path"])
            or os.path.dirname(os.path.abspath(prd["board_path"])))
    raw = str(prd["fm"].get("repo", "") or "").strip()
    if raw:
        for cand in (raw, os.path.join(root, raw)):
            if os.path.isdir(cand):
                r = repo_root(cand)
                if r:
                    return r
    return root


def newest_mtime(paths):
    """The newest mtime under any of `paths` — a file's own, a directory's
    walked, dot-dirs and `__pycache__` skipped since nothing a worker does
    lives there. A path that is not on disk counts nothing: a footprint names
    what the work will touch, not what exists yet."""
    newest = 0.0
    for p in paths:
        if os.path.isfile(p):
            try:
                newest = max(newest, os.stat(p).st_mtime)
            except OSError:
                pass
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs
                           if not d.startswith(".") and d != "__pycache__"]
                for f in files:
                    try:
                        newest = max(newest,
                                     os.stat(os.path.join(root, f)).st_mtime)
                    except OSError:
                        pass
    return newest


def silent_of(prd, settings, collect=None, now=None):
    """Minutes since anything of this PRD's last moved, when that is longer
    than `claim-ttl`; None otherwise. THE rule for a quiet worker.

    "Anything of this PRD's" is its directory and every path of its footprint
    union — the PRD's own plus its specs', the union `collect` commits — in
    its repo. Only a held PRD in the in-flight band can be silent: a `blocked`
    one is waiting on a person, and a PRD to collect is a worker that
    finished, which is the opposite of one that went quiet. `collect` is
    `standing()`'s verdict; pass it when you already hold it."""
    if prd["state"] not in SILENT_STATES or not claim_of(prd["fm"]):
        return None
    if collect is None:
        collect = standing(prd)[3]
    if collect:
        return None
    repo = prd_repo(prd)
    _, feet = spec_data(prd)
    paths = [prd["dir"]] + [os.path.join(repo, f) for f in feet
                            if not f.startswith(MEMBER_SIGIL)]
    newest = newest_mtime(paths)
    if not newest:
        return None
    age = ((time.time() if now is None else now) - newest) / 60
    return age if age >= claim_ttl(settings) else None


def fmt_age(minutes):
    """`42m` under ninety minutes, `1.5h` past it — the page's own spelling
    for a holding time, so the scan and the row read the same word."""
    return f"{round(minutes)}m" if minutes < 90 else f"{minutes / 60:.1f}h"


# The round's own memory — @references/parts/round.md. Fifteen lines the
# orchestrator rewrites at every transition, so a compacted session recovers
# by reading one file instead of re-deriving the round from the tree.
ROUND_FILE = ".round.md"


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


# ── the vision axis ───────────────────────────────────────────────────────────
# `prds/vision.md` says where the board is going: `vision:` in one sentence,
# `terminals:` naming the PRDs whose completion is that destination, `edges:`
# for a dependency nobody wrote as `needs:`. @references/parts/order.md.
VISION_FILE = "vision.md"


def read_vision(board):
    """`prds/vision.md` as data — {vision, terminals, edges, title, body} —
    or None when the board has none. The one reader of the file."""
    path = os.path.join(board, VISION_FILE)
    if not os.path.isfile(path):
        return None
    fm, title, body = parse_prd(path)

    def items(key):
        v = fm.get(key, [])
        v = v if isinstance(v, list) else [v]
        return [str(x).strip() for x in v if str(x).strip()]

    edges = []
    for e in items("edges"):
        a, sep, b = e.partition("->")
        edges.append((a.strip(), b.strip()) if sep else (e, ""))
    return {"vision": str(fm.get("vision", "")).strip(),
            "terminals": items("terminals"), "edges": edges,
            "title": title, "body": body}


def resolve_addr(prds, tok, board, idx=None):
    """The rel a vision address names, or None. `needs:` resolution — own
    board first, `@<member>/<rel>` across boards — plus `@<this board's
    name>/<rel>` for the board's own PRD, which a master's file writes so its
    terminals read as one list."""
    t = str(tok).strip().rstrip("/")
    own = f"{MEMBER_SIGIL}{board_name(board)}/"
    if t.startswith(own) and t[len(own):] in prds:
        return t[len(own):]
    return resolve_need(prds, {"board": None}, t, idx)


def vision_axis(board, prds=None, vis=None):
    """The axis as data, or None when the board declares no terminals.

    `depth[rel]` is the longest serial chain from that PRD to a terminal over
    `needs:` plus `edges:` — a parent is a terminal for its subtree, a done
    PRD on the chain costs no hop — or None when no terminal is reachable:
    off the axis, neither near the vision nor far from it. `reach[rel]` is
    the undone work the PRD stands in front of. `dangling` lists every
    terminal or edge end that names no PRD — what `doctor`'s `vision` row
    reports."""
    v = read_vision(board) if vis is None else vis
    if not v or not v["terminals"]:
        return None
    prds = scan(board) if prds is None else prds
    idx = needs_index(prds)
    term, dangling = set(), []
    for t in v["terminals"]:
        r = resolve_addr(prds, t, board, idx)
        if r:
            term.add(r)
        else:
            dangling.append(f"terminal {t} names no PRD")
    after = {r: set() for r in prds}       # after[x]: the rels that wait on x
    for r, p in prds.items():
        deps = p["fm"].get("needs", [])
        for d in (deps if isinstance(deps, list) else [deps]):
            t = resolve_need(prds, p, d, idx)
            if t and t != r:
                after[t].add(r)
        for c in p["children"]:            # a parent lands after its children
            after[c].add(r)
    for a, b in v["edges"]:
        ra, rb = (resolve_addr(prds, x, board, idx) for x in (a, b))
        bad = [x for x, rx in ((a, ra), (b, rb)) if not rx]
        if bad:
            dangling.append(f"edge {a} -> {b}: {', '.join(bad)} names no PRD")
        elif ra != rb:
            after[ra].add(rb)
    depth, reach = {}, {}

    def walk(r):
        if r in depth:
            return depth[r]
        depth[r] = 0 if r in term else None   # a cycle reads this partial value
        best = depth[r]
        for nxt in after[r]:
            d = walk(nxt)
            if d is None:
                continue
            step = d if prds[nxt]["state"] == "done" else d + 1
            best = step if best is None else max(best, step)
        depth[r] = 0 if r in term else best
        return depth[r]

    def down(r):
        if r in reach:
            return reach[r]
        reach[r] = set()
        acc = set()
        for nxt in after[r]:
            if prds[nxt]["state"] != "done":
                acc.add(nxt)
            acc |= down(nxt)
        reach[r] = acc
        return acc

    for r in prds:
        walk(r)
        down(r)
    return {"vision": v["vision"], "body": v["body"],
            "terminals": v["terminals"], "term": term, "after": after,
            "depth": depth, "reach": {r: len(s) for r, s in reach.items()},
            "dangling": dangling}


def axis_depth(board, prds=None):
    """{rel: depth} from the vision axis — None for a PRD off it, {} on a
    board that declares no terminals, which orders as it always has."""
    ax = vision_axis(board, prds)
    return ax["depth"] if ax else {}


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
    `done`, or `collect` — and those are the ones to merge. It reads
    `collect` rather than the boxes so that "merge this" and "collect this"
    are one rule: a lane marked ready on a PRD whose `prd.md` still carries an
    open box is a merge into a gate that would refuse it. The rest are in
    flight and drawn as such: a lane at 50/54 boxes is worth seeing next to
    the queue it is about to join.

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
                # the board's own claim that the work is finished and
                # tested: `done`, or `collect` — every acceptance box closed
                # on a held PRD AND no open box left in its own `prd.md`
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
    day_h = dur(settings, "gantt-day", "settings.md", "8h") or 8.0
    sched = mp.get("schedule", {})
    tasks, unplanned = [], []
    done = parked = containers = 0
    for rel in sorted(prds):
        p = prds[rel]
        st = p["state"]
        weight = round(num(p["fm"], "complexity", rel)
                       or dur(p["fm"], "est", rel), 2)
        pr = num(p["fm"], "priority", rel)
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
            # the quiet worker, off the files — @references/parts/view.md.
            # None below `claim-ttl`; minutes of silence past it
            silent=silent_of(p, settings, collect=ready_to_collect),
        ))
    # Every PRD, not only the scheduled ones: the timeline draws what is left,
    # the analytics have to see what is done, parked and estimated too, and a
    # second scan of the same tree to get them would be the more expensive way
    # to say the same thing. `est` here is the PRD's own — spec_data reads every
    # spec file on the board, which is a plan-time cost, not a render one.
    everything = []
    for rel in sorted(prds):
        p = prds[rel]
        prio = num(p["fm"], "priority", rel)
        # boxes for live PRDs only: a `done` PRD's specs are history, and
        # reading every one of them is the plan-time cost this loop avoids.
        # `collect` comes from `standing`, the same reader `tasks[]` above
        # uses — this row and that one describe the same PRD in the same
        # payload, and a second spelling of the rule here is how they came to
        # disagree about a PRD whose specs are closed and whose `prd.md` is
        # not (`prds/memos/done-counts-which-boxes.md`).
        closed, total, collect = 0, 0, False
        if p["state"] in LIVE_STATES:
            _, closed, total, collect = standing(p)
        everything.append({
            "rel": rel, "name": p["name"], "title": p["title"],
            "state": p["state"], "board": p.get("board"),
            "parent": p.get("parent"),
            "prio": int(prio) if prio == int(prio) else prio,
            "est": round(dur(p["fm"], "est", rel), 2),
            "actual": round(dur(p["fm"], "actual", rel), 2),
            # the weight the board schedules by — complexity, falling back
            # to est. est and actual are records the plan never schedules
            # by; `calibrate` fits real hours from them
            "weight": round(num(p["fm"], "complexity", rel)
                            or dur(p["fm"], "est", rel), 2),
            "boxes": [closed, total],
            "collect": collect,
            "kids": len(p.get("children") or []),
            # prd.md's own mtime — cheap (one stat, no git call), unlike the
            # archive's done_at which needs `git log --follow` per PRD and is
            # deliberately kept out of this per-second-rebuilt payload. Used
            # by the board view to sort the done column by how recently each
            # PRD last changed.
            "mtime": os.path.getmtime(os.path.join(p["dir"], "prd.md")),
        })
    land, repos = landing(board, everything)
    return {
        "board": board_name(board),
        # a master's members, in plan order — the renderer groups by them
        "boards": [n for n, _ in members(board)],
        "all": everything,
        "history": read_history(board),
        # the cost series — @references/parts/guard.md. `guard` is None when
        # no session file exists, and the page says `no guard`
        "transitions": read_transitions(board),
        "guard": guard_view(board),
        # the states the loop works, then any the user parked work in
        "states": sorted(LIVE_STATES | {"done"}) + sorted(
            {p["state"] for p in prds.values()} - LIVE_STATES - {"done"}),
        "anchor": mp.get("planned_at") or datetime.date.today().isoformat(),
        "dayHours": day_h,
        # the machine-wide fit from `calibrate` — weight to real hours at the
        # display edge only; the schedule above never read it. `tune` is the
        # hand-set margin the view multiplies on top of the fit
        "calib": read_calibration(),
        "tune": TUNE,
        "workers": str(settings.get("workers", "3")),
        # the one sentence `prds/vision.md` says the board is for — the page
        # prints it under the numbers. Empty when the board declares none
        "vision": {"purpose": (read_vision(board) or {}).get("vision", "")},
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


TRANSITIONS_FILE = ".transitions.jsonl"


def read_transitions(board, last=30):
    """The last `last` rows transitions.py `record` appended — one per state
    move, carrying the guard's count for the window before it (`calls`,
    `reads`, `refused`, `tokens`, each `null` when no guard was counting).
    The analytics draw calls per transition off these; `.history.jsonl`
    stays the burn-down's."""
    rows = []
    try:
        for line in open(os.path.join(board, TRANSITIONS_FILE),
                         encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        return []
    return rows[-last:]


# The guard's session files — resources/guard.py writes them, one per
# session, and `PEARDE_GUARD_STATE` moves the directory for both. plan.py
# only reads: the newest file is the live session, because the guard touches
# its file on every tool call, and the call that runs `pearde status` is
# the last one it saw.
GUARD_DIR = os.environ.get("PEARDE_GUARD_STATE") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "state", "guard")


def guard_sessions():
    """[(session, mtime, data)] oldest first, or [] with no state dir or no
    file in it — `no guard`, never zero."""
    out = []
    try:
        names = [n for n in os.listdir(GUARD_DIR) if n.endswith(".json")]
    except OSError:
        return out
    for n in names:
        path = os.path.join(GUARD_DIR, n)
        try:
            out.append((n[:-5], os.stat(path).st_mtime,
                        json.load(open(path, encoding="utf-8"))))
        except (OSError, ValueError):
            continue
    out.sort(key=lambda x: x[1])
    return out


def guard_block(board, data):
    """The per-board counter block a session file holds for `board`, or
    None."""
    return (data.get("boards") or {}).get(os.path.realpath(board))


def guard_view(board):
    """What the analytics draw: every session that counted on this board,
    oldest first, or None when the guard has left no file at all."""
    sessions = guard_sessions()
    if not sessions:
        return None
    rows = []
    for sid, mtime, data in sessions:
        b = guard_block(board, data)
        if b is None:
            continue
        rows.append({"session": sid, "at": round(mtime, 3),
                     "refused": int(b.get("refused", 0)),
                     "calls": int(b.get("calls", 0)),
                     "transitions": int(b.get("transitions", 0))})
    return {"sessions": rows[-30:]}


def session_line(board):
    """`pearde status`'s one line on the cost of this session — the newest
    guard file's block for this board. `no guard` when there is no file;
    a session that has not counted here yet says so."""
    sessions = guard_sessions()
    if not sessions:
        return "this session: no guard"
    b = guard_block(board, sessions[-1][2])
    if b is None:
        return "this session: no calls counted on this board"
    calls = int(b.get("calls", 0))
    n = int(b.get("transitions", 0))
    per = f"{calls / n:.1f}" if n else "—"
    return (f"this session: {calls} calls · {int(b.get('refused', 0))} refused"
            f" · {n} transitions · {per} per transition")


def write_history(board, prds=None):
    """Today's row, once. Rewrites today's line rather than appending a second,
    so a daemon restarted six times in a day still leaves one point."""
    prds = scan(board) if prds is None else prds
    today = datetime.date.today().isoformat()
    row = {"d": today, "states": {}, "hleft": 0.0, "hdone": 0.0,
           "done": 0, "left": 0}
    for rel, p in prds.items():
        st = p["state"]
        row["states"][st] = row["states"].get(st, 0) + 1
        h = (num(p["fm"], "complexity", rel)
             or dur(p["fm"], "est", rel))
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


# ── calibration ───────────────────────────────────────────────────────────────
# One constant per machine, not per board: how many real hours a unit of
# weight costs THIS agent, fitted from every done PRD that recorded an
# `actual:` on every board the service has ever registered. The plan still
# schedules in weight — the constant only translates at the display edge,
# so a bad fit can mislabel an axis but never re-order the work.

STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")
CALIB_PATH = os.path.join(STATE_DIR, "calibration.json")

# The one hand-tunable knob. Hours shown = weight × fitted kw × TUNE.
# The fit says how fast this machine has been; TUNE is the margin on top —
# raise it when the board keeps finishing later than it promised, lower it
# when it keeps beating the number.
TUNE = 1.618


def fmt_w(w, calib):
    """Weight, printed as tuned real hours when a fit exists, else as raw
    weight. Display only — nothing schedules by this."""
    if calib and calib.get("kw"):
        return f"{w * calib['kw'] * TUNE:.1f}h"
    return f"{w:.1f}w"


def read_calibration():
    """The fitted constants, or None before `calibrate` has run."""
    try:
        c = json.load(open(CALIB_PATH, encoding="utf-8"))
        return c if c.get("n") else None
    except (OSError, ValueError):
        return None


def calib_rows():
    """(board, rel, est_h, actual_h, weight) for every done PRD carrying an
    `actual:`, across every registered board. est and actual are records the
    plan never schedules by — which is exactly what makes them honest
    calibration data: nobody gamed a number nothing was reading."""
    try:
        boards = json.load(open(os.path.join(STATE_DIR, "serve.json"),
                                encoding="utf-8"))
    except (OSError, ValueError):
        boards = []
    rows = []
    for b in boards:
        if not os.path.isdir(b):
            continue
        name = os.path.basename(os.path.dirname(b)) or b
        for rel, p in sorted(_scan_one(b).items()):
            if p["state"] != "done":
                continue
            act = dur(p["fm"], "actual", rel)
            if act <= 0:
                continue
            w = num(p["fm"], "complexity", rel)
            rows.append((name, rel, dur(p["fm"], "est", rel), act, w))
    return rows


def cmd_calibrate(board):
    rows = calib_rows()
    if not rows:
        print("calibrate: no done PRD carries an `actual:` on any registered"
              " board — nothing to fit.\n"
              "Record `actual:` on the DONE transition and run this again.")
        return
    for name, rel, e, a, w in rows:
        print(f"  {name:12} {rel:32} "
              + (f"est {e:6.2f}h" if e else "est      —")
              + f" · actual {a:6.2f}h"
              + (f" · w {w:.0f}" if w else ""))
    ew = [(e, a) for _, _, e, a, _ in rows if e > 0]
    ww = [(w, a) for _, _, _, a, w in rows if w > 0]
    # ratio of sums, not mean of ratios: a five-minute PRD must not outvote
    # a three-day one. The quantiles of the per-PRD ratio are the band.
    ke = round(sum(a for _, a in ew) / sum(e for e, _ in ew), 4) if ew else 0
    kw = round(sum(a for w, a in ww) / sum(w for w, _ in ww), 4) if ww else 0
    q = sorted(a / w for w, a in ww)
    pick = lambda p: round(q[min(len(q) - 1, int(p * len(q)))], 4) if q else 0
    calib = {"kw": kw, "ke": ke, "n": len(rows), "nw": len(ww),
             "p20": pick(.2), "p80": pick(.8),
             "boards": sorted({r[0] for r in rows}),
             "fitted": datetime.date.today().isoformat()}
    os.makedirs(STATE_DIR, exist_ok=True)
    json.dump(calib, open(CALIB_PATH, "w", encoding="utf-8"), indent=1)
    print(f"\nn={len(rows)} done PRDs across {len(calib['boards'])} board(s)")
    if ke:
        print(f"k est→actual    = {ke}  (agent is {round(1 / ke, 1)}× faster"
              " than its estimates)")
    if kw:
        print(f"k weight→hours  = {kw} h/w · band P20 {calib['p20']}"
              f" – P80 {calib['p80']}")
        print(f"hours shown     = weight × {kw} × {TUNE}"
              " (TUNE — the hand-set margin, hard-coded in plan.py)")
    print(f"saved: {CALIB_PATH}")
    # re-render so the open page shows the new constant without waiting for
    # the next board edit
    cmd_gantt(board)


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


def dispatchable(prd, prds, board=None):
    """None when `claim` would take this PRD now, else why not — one string,
    `<gate>: <why>`, the gate word first so `transitions.gate_claim` raises
    it as it stands and `brief` maps it to a skip word.

    The one place the gates are written. `compute_plan`'s ready band,
    `cmd_scan`'s `ready` and `gated` sections and `gate_claim` all call it,
    so the scan cannot list as ready what `claim` refuses — the memo
    `a-parked-child-holds-the-parent` is the day they disagreed. The gates:

    - unclaimed — it carries a `claim:`.
    - leaf — a child is not `done`. A parked child is neither done nor
      coming, so it holds the parent for good: `held by <child> (parked)`.
    - container — children, every one `done`, and no specs or open box of
      its own. Finished work `collect` closes, never a thing to dispatch;
      `claim` on it is the trap `a-container-cannot-reach-done` records.
    - needs — a `needs:` entry naming nothing, or a PRD not `done`.
    - footprint — overlaps a `claimed` PRD's.
    - workflow — `workflow:` names no workflow in any library it can see;
      `board` is the master's library when there is one.

    The state is not checked here: the callers partition by state first,
    and a `claimed` PRD is in flight, not refused."""
    rel = prd["rel"]
    if claim_of(prd["fm"]):
        return f"unclaimed: {rel} carries `claim: {prd['fm']['claim']}`"
    parked = [c for c in prd["children"]
              if prds[c]["state"] not in LIVE_STATES
              and prds[c]["state"] != "done"]
    if parked:
        return (f"leaf: {rel} held by "
                + ", ".join(f"{c} (parked)" for c in parked))
    live = [c for c in prd["children"] if prds[c]["state"] != "done"]
    if live:
        return (f"leaf: {rel} has children not done — "
                + ", ".join(os.path.basename(c) for c in live))
    sdir = os.path.join(prd["dir"], "specs")
    specs = (os.path.isdir(sdir)
             and any(f.endswith(".md") for f in os.listdir(sdir)))
    if prd["children"] and not specs and not body_has_open_box(prd):
        return "container: every child done — pearde collect closes it"
    deps = prd["fm"].get("needs", [])
    for d in (deps if isinstance(deps, list) else [deps]):
        t = resolve_need(prds, prd, d)
        if t is None:
            return f"needs: `{d}` names no PRD on this board"
        if prds[t]["state"] != "done":
            return f"needs: {t} is `{prds[t]['state']}`, not done"
    _, mine = spec_data(prd)
    for r, p in prds.items():
        if p["state"] != "claimed" or r == rel:
            continue
        _, theirs = spec_data(p)
        for x in mine:
            for y in theirs:
                if x == y or x.startswith(y + "/") or y.startswith(x + "/"):
                    return (f"footprint: {r} is claimed and holds `{y}`, "
                            f"which clashes with `{x}`")
    v = prd["fm"].get("workflow")
    if isinstance(v, list):
        return ("workflow: the key holds one slug — a list is a break, not "
                "an absence; fix the shape or remove the key")
    mark = workflow_marks(board or prd["board_path"], {rel: prd}).get(rel, "")
    if mark.endswith("?"):
        return (f"workflow: `{mark[:-1]}` names no workflow in "
                f"{prd['board_path']}/workflows — fix the slug or remove "
                "the key")
    return None


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
    if d.startswith("@"):
        # `@<board>/<prd>` names another board on purpose. Scanned without
        # that board — a member on its own — the honest answer is "not here",
        # never the basename. A cross-tree node writes the same child name on
        # every member, so the fallback would resolve a qualified need to the
        # very PRD doing the needing, and the cycle check would kill the scan.
        return None
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
                ds = str(d).strip()
                if warn and ds.startswith("@"):
                    print(f"plan: {r} needs '{d}' — that board is not in this "
                          f"scan, ignored", file=sys.stderr)
                    continue
                same = idx[0].get(os.path.basename(ds), [])
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
        est[r] = (e or num(p["fm"], "complexity", r)
                  or dur(p["fm"], "est", r))
        feet[r] = f
    # A parent with live children is a container: the work is in the children,
    # and weighing it too counts the same work twice. It still waits for them.
    for r, p in todo.items():
        if any(c in todo for c in p["children"]):
            est[r] = 0.0
    known = [e for e in est.values() if e > 0]
    avg = (sum(known) / len(known) if known
           else num(settings, "weight-default", "settings.md", 50) or 50)
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
    # A container — children every one `done`, nothing of its own — is
    # finished work `collect` closes, never a thing to dispatch. It joins the
    # list here, once, so `scan`, `plan` and a bare `collect` read one list.
    for r, p in todo.items():
        if (p["state"] in ("open", "specced") and r not in collect
                and (dispatchable(p, prds, board) or "")
                .startswith("container:")):
            collect.append(r)

    def prio(r):
        return num(todo[r]["fm"], "priority", r)

    # The vision axis orders the frontier: asap lanes first, then on-axis
    # deepest-first, then the old widest-door order. A PRD off the axis (or a
    # board with no axis) keeps the old order. The axis is `prds/vision.md`,
    # read by `axis_depth`; the asap lane is a PRD declaring `axis: asap`
    # in its frontmatter — the "see it working" ask, scheduled by priority,
    # not hops.
    axis = axis_depth(board, prds)
    def asap(r):
        return str(todo[r]["fm"].get("axis", "")).strip() == "asap"
    def axis_rank(r, unblocks=None):
        u = (unblocks or {}).get(r, 0)
        if asap(r):
            return (0, 0, -u, -prio(r), r)
        d = axis.get(r)
        if d is not None:
            return (1, -d, -u, -prio(r), r)
        return (2, 0, -u, -prio(r), r)

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
    ranked = sorted(todo, key=lambda x: axis_rank(x))
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
    # The ready band is `dispatchable`, the one predicate `claim` reads. A
    # PRD with no edge left that the gate would still refuse — a parked
    # child, a stale claim, a dangling workflow — is held to the tail of the
    # schedule: visible, never offered. A container is collect's, not a
    # hold; it folds at zero like any weightless PRD.
    held = {}
    for r in list(ready):
        if todo[r]["state"] not in ("open", "specced"):
            continue
        why = dispatchable(todo[r], prds, board)
        if why and not why.startswith("container:"):
            held[r] = why
            ready.remove(r)
    pending = list(held)
    running, schedule, order, t0 = [], {}, [], 0.0
    def take(pool):
        best = min(pool, key=lambda x: axis_rank(x, unblocks))
        pool.remove(best)
        return best
    def finish(r):
        for s in feeds[r]:
            left[s] -= 1
            if not left[s]:
                ready.append(s)
    while ready or running or pending:
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
        if not running and not ready and pending:
            # nothing left that can run: the held go at the tail, in order,
            # so what waits on them is scheduled after them, not never
            for r in pending:
                schedule[r] = {"start": t0, "end": t0 + est[r]}
                order.append(r)
                running.append((schedule[r]["end"], r))
            pending = []
        if not running:
            continue
        running.sort()
        t0, r = running.pop(0)
        finish(r)
    wall = max((s["end"] for s in schedule.values()), default=0.0)
    return {"prds": prds, "todo": todo, "parked": parked, "settings": settings,
            "workers": workers, "needs": needs, "est": est, "feet": feet,
            "boxes": boxes, "collect": sorted(collect), "held": held,
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


def question_counts(prd):
    """(questions, answers) in one PRD's body — the numbers step 2 asks for.

    A question is a `**Qn**` line under `## Questions`; an answer is the same
    line under `## Answers`. Counting them here is what stops a round opening
    every `question` PRD to find out whether it is still asking."""
    out = {}
    for sec in re.split(r"(?m)^##\s+", prd.get("body") or "")[1:]:
        head, _, rest = sec.partition("\n")
        head = head.strip().lower()
        if head.startswith(("questions", "answers")):
            out[head[:1]] = len(re.findall(r"(?m)^\s*(?:\*\*Q|[-*]\s)", rest))
    return out.get("q", 0), out.get("a", 0)


# One line of a round, written back. `**Q1** *(answered 2026-08-28 14:22)*
# — <the decision>`: the id says which fork, the stamp says when it was
# settled, and everything after the dash is the decision itself. The stamp is
# optional — rounds answered before the view wrote one still read, they only
# lose their place in a date order.
ANSWER_LINE_RE = re.compile(
    r"^\s*\*\*(Q?\d+[a-z]?)\*\*\s*"
    r"(?:\*?\(answered\s+([^)]*)\)\*?\s*)?[\u2014\u2013:-]*\s*(.*)$")

# `### Q1: the fork` — the question's own title, so an answer can be read
# without opening the PRD it came out of.
QUESTION_HEAD_RE = re.compile(r"(?m)^###\s+(Q?\d+[a-z]?)\s*[:.\u2014\u2013-]?\s*(.*)$")


def _h2_sections(body, name):
    """Every `## <name>` section's text. A round can be asked twice — a second
    `## Questions` round is a second section, not a replacement."""
    out = []
    for m in re.finditer(r"(?m)^##\s+" + name + r"\b[^\n]*$", body or ""):
        rest = body[m.end():]
        nxt = re.search(r"(?m)^##\s+", rest)
        out.append(rest[:nxt.start()] if nxt else rest)
    return out


def _qid(raw):
    q = raw.upper()
    return q if q.startswith("Q") else "Q" + q


def answers_of(prd):
    """Every answer written back into one PRD, in the order the file has them.

    The asks view moves an answered question out of the inbox and into the
    answered panel, and it needs the answer itself to do it — the question it
    settles, the decision, and when it was made. Reading it out of the file is
    what makes a redraw, a reload and a second reader agree: the PRD is the
    record, this is only how it is read."""
    body = prd.get("body") or ""
    titles = {}
    for sec in _h2_sections(body, "Questions"):
        for m in QUESTION_HEAD_RE.finditer(sec):
            titles.setdefault(_qid(m.group(1)), m.group(2).strip())
    out, cur = [], None
    for sec in _h2_sections(body, "Answers"):
        cur = None
        for line in sec.splitlines():
            m = ANSWER_LINE_RE.match(line)
            if m:
                qid = _qid(m.group(1))
                cur = {"id": qid, "date": (m.group(2) or "").strip(),
                       "text": m.group(3).strip(),
                       "question": titles.get(qid, "")}
                out.append(cur)
            elif cur is not None and line.strip():
                # a decision that runs over one line stays one answer
                cur["text"] = (cur["text"] + " " + line.strip()).strip()
    return out


def weight_of(prd, avg):
    """One PRD's weight, done or live — `complexity`, else the specs' sum,
    else `est`, else the board average. `compute_plan` weighs only live work;
    the progress line's percentage needs the closed PRDs too."""
    e, _ = spec_data(prd)
    return (num(prd["fm"], "complexity", prd["rel"]) or e
            or dur(prd["fm"], "est", prd["rel"]) or avg)


def progress_terms(board, prds=None, settings=None):
    """Every term of the progress line, computed once.

    @references/parts/progress.md defines them; deriving them by hand off a
    board scan is a page of arithmetic a round pays for at every state change,
    and pays again after every compaction."""
    prds = scan(board) if prds is None else prds
    settings = board_settings(board) if settings is None else settings
    live = {r: p for r, p in prds.items() if p["state"] in LIVE_STATES}
    scored = [w for w in (num(p["fm"], "complexity", r)
                          for r, p in prds.items()) if w > 0]
    avg = (sum(scored) / len(scored) if scored
           else num(settings, "weight-default", "settings.md", 50) or 50)

    def origin(p):
        return "derived" if str(p["fm"].get("origin", "")).strip() == \
            "derived" else "requested"

    req = {r: p for r, p in prds.items()
           if origin(p) == "requested" and (p["state"] in LIVE_STATES
                                            or p["state"] == "done")}
    der = {r: p for r, p in prds.items()
           if origin(p) == "derived" and (p["state"] in LIVE_STATES
                                          or p["state"] == "done")}
    wt = {r: weight_of(p, avg) for r, p in req.items()}
    done_w = sum(w for r, w in wt.items() if req[r]["state"] == "done")
    all_w = sum(wt.values())
    counts = collections.Counter(p["state"] for p in prds.values())
    parked = [r for r, p in prds.items()
              if p["state"] not in LIVE_STATES and p["state"] != "done"]
    return {
        "prds": prds, "live": live, "avg": avg, "counts": counts,
        "parked": parked,
        "done": (sum(1 for p in req.values() if p["state"] == "done"),
                 len(req)),
        "pct": round(100 * done_w / all_w) if all_w else 0,
        "derived": (sum(1 for p in der.values() if p["state"] == "done"),
                    len(der)),
        "open": (counts.get("open", 0), len(prds)),
        "openpct": (round(100 * counts.get("open", 0) / len(prds))
                    if prds else 0),
    }


def workflow_marks(board, prds):
    """{rel: "<slug>" | "<slug>?"} for every PRD carrying a `workflow:`.

    The `?` is the break @references/workflow.md names, and it covers two
    cases that read as one on a line: the slug is in no library this PRD can
    see, or the file is there and is an **atomic** — a route was asked for and
    a single step was found. Both leave the worker without a route, so both
    mark; `workflows.py check` is where they are told apart, in words.

    A member PRD resolves against its own board's library first and the
    master's second, the order `needs:` resolves in. Each library is scanned
    once per call — this runs once per `scan`, not once per PRD.
    """
    marks, libs = {}, {}

    def lib(b):
        if b not in libs:
            libs[b] = wflib.scan(b)
        return libs[b]

    for rel, p in prds.items():
        v = p["fm"].get("workflow")
        if not v:
            continue
        if isinstance(v, list):
            # A shape error, not an absence. @references/workflow.md says the
            # key holds one slug and anything else is a break, so it marks
            # like one — the line shows it and the loop does not dispatch it.
            # `workflows.py check` is where it is named in words.
            marks[rel] = ",".join(str(x).strip() for x in v) + "?"
            continue
        slug = str(v).strip()
        if not slug:
            continue
        seen = [b for b in (p.get("board_path"), board) if b]
        ok = any(lib(b).get(slug, {}).get("kind") == "workflow" for b in seen)
        marks[rel] = slug if ok else slug + "?"
    return marks


def cmd_scan(board):
    """The whole board as one page a round can hold — step 1, in one call.

    Everything the loop reads at the top of a round: the counts, the progress
    terms, what is finished and waiting to be closed, what is dispatchable
    now, what gates the rest, who holds what, and how many questions are
    standing. It replaces a tree walk plus a `prd.md` read per PRD plus a spec
    read per box count, which is the same information at a hundred times the
    tokens — and re-derives none of it after a compaction."""
    t = progress_terms(board)
    prds, avg = t["prds"], t["avg"]
    r = compute_plan(board, None, warn=False)
    order = r["order"] if r else []
    boxes = r["boxes"] if r else {}
    needs = r["needs"] if r else {}
    after = r["after"] if r else {}
    est = r["est"] if r else {}
    wf = workflow_marks(board, prds)
    settings = board_settings(board)     # `claim-ttl`, for the silent word
    mem = [n for n, _ in members(board)]
    # The axis, when the board declares one: how much live work is on the way
    # to the vision and how much is not. A board with no terminals prints
    # neither this nor the marks below — its scan reads as it always has.
    vis = read_vision(board)
    ax = vision_axis(board, prds, vis) if vis else None
    axis_note = ""
    if ax:
        on = sum(1 for x in t["live"] if ax["depth"].get(x) is not None)
        axis_note = f" · axis: {on} on · {len(t['live']) - on} off"
    print(f"board: {board} · {len(prds)} PRDs"
          + (f" · master of {len(mem)}: " + ", ".join(mem) if mem else "")
          + (f" · workers={r['workers']}" if r else "")
          + axis_note)
    if vis and vis["vision"]:
        print(f"vision: {vis['vision']}")
    if t["counts"]:
        print("counts: " + " · ".join(f"{s} {n}" for s, n in sorted(
            t["counts"].items(), key=lambda kv: -kv[1])))
    rd, rn = t["done"]
    dd, dn = t["derived"]
    o, n = t["open"]
    print(f"progress: done {rd}/{rn} · {t['pct']}%"
          + (f" · derived {dd}/{dn}" if dn else "")
          + f" · open {o}/{n} · {t['openpct']}%")
    if t["parked"]:
        print("parked: " + ", ".join(sorted(t["parked"])))

    why = {}                              # rel → `dispatchable` reason, below

    def line(x):
        p = prds[x]
        c, tt = boxes.get(x, (0, 0))
        cl = claim_of(p["fm"])
        q, a = question_counts(p)
        bits = [f"{p['state']:9}", x, f"p{p['fm'].get('priority', 0)}",
                f"w{est.get(x, 0):.0f}"]
        if wf.get(x):
            bits.append("wf " + wf[x])
        if ax and ax["depth"].get(x) is None:
            bits.append("off-axis")
        if tt:
            bits.append(f"boxes {c}/{tt}")
        if needs.get(x):
            bits.append("needs " + ",".join(os.path.basename(d)
                                            for d in needs[x]))
        if after.get(x):
            bits.append("after " + ",".join(os.path.basename(d)
                                            for d in after[x]))
        if why.get(x) and not needs.get(x) and not after.get(x):
            # the gate's own words, when no `needs`/`after` bit already
            # says it — `held by <child> (parked)`, a container, a clash
            bits.append(why[x])
        if cl:
            bits.append(f"claim {cl['who']}"
                        + (f" since {cl['since']}" if cl["since"] else ""))
        if q:
            bits.append(f"questions {q}/{a} answered")
        # the same word the page prints on the row — one rule, `silent_of`
        sil = silent_of(p, settings, collect=x in collect)
        if sil is not None:
            bits.append(f"silent {fmt_age(sil)}")
        return "  " + " · ".join(bits)

    # One PRD, one section, in THE PRESSURE ORDER — the single ranking this
    # board is worked in, and the same one the timeline stacks its rows by.
    # See @references/parts/order.md. Everything above `in flight` is something
    # this round can act on now; `in flight` is held by somebody else. A PRD
    # listed twice is a round that has to work out which line meant it.
    collect = list(r["collect"]) if r else []
    rest = [x for x in order if x not in collect]
    # `blocked` is a wall a person has to take down, not a free PRD. It holds
    # its worker, so it is not in flight either — filing it under `ready` was
    # the scan calling a PRD dispatchable that nothing can dispatch.
    yours = [x for x in rest if prds[x]["state"] in ("question", "blocked",
                                                     "refine", "failed")]
    flight = [x for x in rest if prds[x]["state"] in ("analyzing", "claimed")
              and x not in yours]
    free = [x for x in rest if x not in flight and x not in yours]
    # `dispatchable` is the one predicate `claim` reads: a PRD it refuses is
    # never listed as ready. A container — children all done, nothing of its
    # own — is already in `collect`: `compute_plan` put it there, the one list
    # `scan`, `plan` and a bare `collect` read.
    why = {x: dispatchable(prds[x], prds, board) for x in free}
    for x in collect:   # a container's row says why it is here, in its own words
        w = (dispatchable(prds[x], prds, board)
             if prds[x]["state"] in ("open", "specced") else None)
        if (w or "").startswith("container:"):
            why[x] = w
    ready = [x for x in free
             if not why[x] and not needs.get(x) and not after.get(x)]
    gated = [x for x in free if x not in ready]
    for title, group in (
            (f"collect — {len(collect)} finished, waiting to be closed",
             collect),
            (f"waiting on you — {len(yours)}", yours),
            (f"in flight — {len(flight)} held by a worker", flight),
            (f"ready — {len(ready)} dispatchable now, in order", ready),
            (f"gated — {len(gated)}, as their gates clear", gated)):
        if not group:
            continue
        print("\n" + title)
        for x in group:
            print(line(x))
    rf = os.path.join(board, ROUND_FILE)
    print(f"\nround: {rf}" + ("" if os.path.isfile(rf) else "  (not written)"))


def plan_frontier(r):
    """`plan`'s ready set — every PRD nothing gates, in dispatch order. The
    same list `vision --next` prints alone."""
    return [x for x in r["order"]
            if not r["needs"][x] and not r["after"][x] and r["est"][x] > 0
            and x not in r["held"]]


def cmd_plan(board, workers):
    r = compute_plan(board, workers)
    if not r:
        print("plan: nothing to do — no undone PRDs")
        return
    prds, todo, parked = r["prds"], r["todo"], r["parked"]
    est, feet, needs, after = r["est"], r["feet"], r["needs"], r["after"]
    sched, unblocks = r["schedule"], r["unblocks"]
    cal = read_calibration()
    fw = lambda w: fmt_w(w, cal)
    mem = [n for n, _ in members(board)]
    print(f"plan: {len(todo)} PRDs"
          f" · workers={r['workers']} · unspecced est'd at {fw(r['avg'])}"
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
    frontier = plan_frontier(r)
    wf = workflow_marks(board, prds)
    if frontier:
        # `ready now` is the dispatch list, and step 5 of @references/parts/
        # loop.md skips a PRD whose `workflow:` names no workflow. The other
        # two skips already show here — an unmet `needs:` drops a PRD out of
        # this list, a footprint clash prints `after … (footprint)` — so
        # without this the one skip the ordering does NOT model is the one
        # the list silently contradicts. Display only: the mark is printed,
        # the order is untouched. Only the `?` form prints, because this
        # parenthetical is the register of what holds a PRD back and a slug
        # that resolves holds back nothing.
        print(f"\nready now — {len(frontier)} in parallel, widest door first")
        for x in frontier:
            p = todo[x]
            hot = p["state"] in ("question", "blocked", "refine", "failed")
            tags = ["waiting on you"] if hot else [] if feet[x] \
                else ["unspecced"]
            if wf.get(x, "").endswith("?"):
                tags.append("wf " + wf[x])
            print(f"  · {x} [{p['state']}] p{p['fm'].get('priority', 0)}"
                  f" {fw(est[x])} · unblocks {fw(unblocks[x])}"
                  + (f"  ({'; '.join(tags)})" if tags else ""))
    held = r["held"]
    gated = [x for x in r["order"]
             if (needs[x] or after[x] or x in held) and est[x] > 0]
    if gated:
        print("\nthen, as gates clear — dispatch order")
        for x in gated:
            p = todo[x]
            why = []
            if x in held:
                why.append(held[x])
            if needs[x]:
                why.append("needs " + ", ".join(os.path.basename(d)
                                                for d in needs[x]))
            if after[x]:
                why.append("after " + ", ".join(os.path.basename(d)
                                                for d in after[x])
                           + " (footprint)")
            if not feet[x]:
                why.append("unspecced")
            if wf.get(x, "").endswith("?"):
                # the mark the ready line carries, on the line the hold
                # moved it to — a dangling slug is visible in both lists
                why.append("wf " + wf[x])
            print(f"  · {x} [{p['state']}] p{p['fm'].get('priority', 0)}"
                  f" {fw(est[x])}" + (f"  ({'; '.join(why)})" if why else ""))
    print(f"\n≈ {fw(r['wall'])} wall @ {r['workers']} workers — a staffing"
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
    print(session_line(board))


def vision_json(board, prds, ax):
    """What `.vision.json` held, as data: every live PRD with its depth and
    reach, deepest first, and the off-axis set by address."""
    name = board_name(board)
    idx = needs_index(prds)
    rows = []
    for r, p in prds.items():
        if p["state"] not in LIVE_STATES:
            continue
        deps = p["fm"].get("needs", [])
        unmet = []
        for d in (deps if isinstance(deps, list) else [deps]):
            t = resolve_need(prds, p, d, idx)
            if t is None or prds[t]["state"] != "done":
                unmet.append(str(d).strip())
        specs = os.path.join(p["dir"], "specs")
        prio = num(p["fm"], "priority", r)
        d = ax["depth"].get(r)
        rows.append({
            "addr": (r if r.startswith(MEMBER_SIGIL)
                     else f"{MEMBER_SIGIL}{name}/{r}"),
            "board": p["board"] or name, "rel": p["local"],
            "state": p["state"], "depth": d, "reach": ax["reach"].get(r, 0),
            "est": dur(p["fm"], "est", r) or None, "prio": prio,
            "ready": (not p["children"] and not unmet
                      and p["state"] in ("open", "specced", "failed")),
            "on_axis": d is not None, "blocked_by": unmet,
            "nspecs": len(os.listdir(specs)) if os.path.isdir(specs) else 0,
        })
    on = sorted((x for x in rows if x["on_axis"]),
                key=lambda x: (-x["depth"], -x["reach"], -x["prio"], x["addr"]))
    return {"vision": ax["vision"], "terminals": ax["terminals"],
            "longest_chain": max((x["depth"] for x in on), default=0),
            "prds": on,
            "off_axis": [x["addr"] for x in rows if not x["on_axis"]]}


def critical_chain(ax, prds, start):
    """The serial chain from `start` to a terminal: at each hop, the
    dependent that carries the depth — a done one costs no hop."""
    chain, cur = [start], start
    while cur not in ax["term"]:
        nxt = None
        for cand in sorted(ax["after"][cur]):
            d = ax["depth"].get(cand)
            hop = 0 if prds[cand]["state"] == "done" else 1
            if d is not None and d + hop == ax["depth"][cur]:
                nxt = cand
                break
        if nxt is None or nxt in chain:
            break
        chain.append(nxt)
        cur = nxt
    return chain


def cmd_vision(board, flags):
    """`pearde vision` — the axis for a person: depth per PRD, the critical
    chain, the off-axis set. `--json` prints what `.vision.json` held.
    `--next` prints `plan`'s ready set alone, in axis order. `--check` is the
    `doctor` row: one line, exit 0, or the dangling names, exit 1."""
    prds = scan(board)
    vis = read_vision(board)
    ax = vision_axis(board, prds, vis) if vis else None
    live = [r for r, p in prds.items() if p["state"] in LIVE_STATES]
    on = sorted((r for r in live if ax and ax["depth"].get(r) is not None),
                key=lambda r: (-ax["depth"][r], -ax["reach"][r], r))
    off = sorted(r for r in live if not ax or ax["depth"].get(r) is None)
    chain = max((ax["depth"][r] for r in on), default=0) if ax else 0
    if "--check" in flags:
        if not vis:
            print("no vision.md")
        elif ax and ax["dangling"]:
            for line in ax["dangling"]:
                print(line)
            return 1
        elif not ax:
            print("vision declared · no terminals — no axis")
        else:
            print(f"{len(ax['terminals'])} terminal"
                  f"{'' if len(ax['terminals']) == 1 else 's'}"
                  f" · {len(on)} on · {len(off)} off · longest chain {chain}")
        return 0
    if not ax:
        if vis and vis["vision"]:
            print(f"vision: {vis['vision']}")
        print("no terminals declared — " + (
            f"write prds/{VISION_FILE} first: the destination in one sentence,"
            " and terminals: naming the PRDs whose completion is it"
            if not vis else
            "the board orders by dependency, weight and priority alone"))
        return 1
    if "--json" in flags:
        json.dump(vision_json(board, prds, ax), sys.stdout, indent=1)
        print()
        return 0
    if "--next" in flags:
        r = compute_plan(board, None, warn=False)
        nxt = plan_frontier(r) if r else []
        print(f"next — {len(nxt)} dispatchable now, in axis order")
        for x in nxt:
            d = ax["depth"].get(x)
            print(f"  · {x} [{prds[x]['state']}] "
                  + (f"depth {d}" if d is not None else "off-axis")
                  + f" · unblocks {ax['reach'].get(x, 0)}")
        return 0
    print(f"vision: {ax['vision']}")
    print(f"axis: {len(on)} on · {len(off)} off · longest chain {chain}")
    for line in ax["dangling"]:
        print(f"dangling: {line}")
    if on:
        print("chain: " + " → ".join(critical_chain(ax, prds, on[0])))
    for d in sorted({ax["depth"][r] for r in on}, reverse=True):
        here = [r for r in on if ax["depth"][r] == d]
        print(f"\ndepth {d} — {len(here)} PRD{'' if len(here) == 1 else 's'}"
              + ("  ← the vision" if d == 0 else ""))
        for r in here:
            print(f"  {r} [{prds[r]['state']}]"
                  f" p{prds[r]['fm'].get('priority', 0)}"
                  f" · unblocks {ax['reach'][r]}")
    if off:
        print(f"\noff-axis — {len(off)} with no path to a terminal")
        for r in off:
            print(f"  {r} [{prds[r]['state']}]")
    return 0


class Flags:
    """What one command takes: `valued` are `--name <v>` (or `--name=<v>`),
    `switches` are bare, `multi` are the valued ones that repeat. `str()` is
    the list the refusal and `--help` print — one list, so they cannot
    drift. transitions.py `Args` is the one parser of it; the class is here
    because that module imports this one, and the two commands below declare
    at import time."""

    def __init__(self, valued=(), switches=(), multi=()):
        self.valued, self.switches = tuple(valued), tuple(switches)
        self.multi = tuple(multi)

    def __str__(self):
        return (", ".join("--" + k for k in self.valued + self.switches)
                or "no flags")


VISION_FLAGS = Flags(("board",), ("json", "next", "check"))
EXAMPLE_FLAGS = Flags()


def _vision_cli(argv):
    """`pearde vision [board] [--board <path>] [--json|--next|--check]` —
    argv is everything after the command name, the return is the exit code.
    A flag outside the declaration is refused before the board is read,
    exit 2, naming the flag and the list."""
    import transitions as translib       # the parser; it imports this module
    try:
        args = translib.Args(argv, VISION_FLAGS, "vision")
    except translib.FlagRefused as e:
        print(f"pearde vision: {e}", file=sys.stderr)
        return 2
    board = find_board(args.opt.get("board")
                       or (args.pos[0] if args.pos else None))
    return cmd_vision(board, ["--" + f for f in args.flags])


# ── the example board ─────────────────────────────────────────────────────────
# resources/board/example/ — one small board with a row in every band. Every
# check in this repo runs against a COPY of it: a check that ticks a box in
# the example changes what every other check sees.
EXAMPLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "example")


def cmd_example(argv):
    """`pearde example <dir>` — copy the example board to <dir>. Refuses an
    existing non-empty directory; an empty or missing one is filled. Prints
    the board path and the scan to run next. argv is everything after the
    command name, the return is the exit code. It declares no flag, and
    refuses one before anything is copied, exit 2."""
    import transitions as translib       # the parser; it imports this module
    try:
        args = translib.Args(argv, EXAMPLE_FLAGS, "example")
    except translib.FlagRefused as e:
        print(f"pearde example: {e}", file=sys.stderr)
        return 2
    if len(args.pos) != 1:
        print("usage: plan.py example <dir>", file=sys.stderr)
        return 2
    dest = os.path.abspath(args.pos[0])
    if os.path.isdir(dest) and os.listdir(dest):
        print(f"pearde: {dest} exists and is not empty — pick an empty or "
              "new directory", file=sys.stderr)
        return 2
    if os.path.exists(dest) and not os.path.isdir(dest):
        print(f"pearde: {dest} is a file, not a directory", file=sys.stderr)
        return 2
    try:
        import shutil
        shutil.copytree(EXAMPLE, dest, dirs_exist_ok=True)
    except OSError as e:
        print(f"pearde: could not copy the example to {dest} — {e}",
              file=sys.stderr)
        return 2
    print(f"example: {os.path.join(dest, 'prds')}")
    print(f"      python3 {os.path.abspath(__file__)} scan {dest}")
    return 0


# What the `pearde` dispatcher discovers: {name: callable(argv) -> exit code}.
_vision_cli.flags = VISION_FLAGS      # what `pearde vision --help` prints
cmd_example.flags = EXAMPLE_FLAGS
COMMANDS = {"vision": _vision_cli}
COMMANDS["example"] = cmd_example


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    cmd = args[0] if args else "status"
    if cmd == "example":          # its argument is not a board yet
        sys.exit(cmd_example(sys.argv[2:]))
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
    elif cmd == "calibrate":
        cmd_calibrate(board)
    elif cmd == "status":
        cmd_status(board)
    elif cmd == "scan":
        cmd_scan(board)
    elif cmd == "vision":
        sys.exit(cmd_vision(board, flags))
    else:
        die(f"unknown command '{cmd}' — scan | plan | reconcile | gantt"
            " | calibrate | members | status | vision | example")


if __name__ == "__main__":
    main()
