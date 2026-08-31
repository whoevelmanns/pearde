#!/usr/bin/env python3
"""pearde serve — the board's live service: one daemon per machine, watching
every registered board and serving the view that reads and writes it.

    serve.py ensure [board]   start the daemon if none runs, register a board
                              (default: walk up from the cwd); safe to run on
                              every session start
    serve.py run              the daemon, foreground — what `ensure` detaches
    serve.py status           the daemon and every board it watches
    serve.py wait  [board]    block until the board moves, then say what did
    serve.py forget <name>    stop watching one board
    serve.py stop             stop the daemon

Singleton by port bind: the daemon owns 127.0.0.1:8443 (PEARDE_PORT
overrides), and a second `run` refuses to start because the bind fails. That
is the whole locking story — no pidfile to go stale.

What it does, per registered board, within about a second of a file changing:

  - re-orders a master board's schedule in place, keeping the anchor day, so a
    state written in one member re-plans the whole board
  - writes the day's history row, which is the only memory the board has
  - bumps a per-board sequence number the view and any agent long-poll on

It watches its own source too: edit render.py (or any module here) and the
daemon re-execs and every open page reloads itself, within about a second. The
data swap keeps its place; a code reload keeps only what the URL holds — which
view, which filter, which PRD — because that is where the page writes it.

A board keys by repo name plus any dot-dirs on its path (`racer/.mi/prds` →
`racer-mi`), or by `name:` in its settings.md when it has one — so two boards
in one repo still get distinct watch entries and /board/ URLs.

A master board (`members:` in its settings.md) is watched over its members'
files too, and registering one registers every member as a board in its own
right: the master carries the merged plan, each member keeps its own.

Everything is local. The board is the files; this serves them, and the edits
the view makes go back into the same files through one set of writers
(edit.py). The registry and log live in state/ beside this script
(machine-local, gitignored): serve.json, serve.log.

HTTP API, all JSON, all 127.0.0.1-only:

  GET  /status                     daemon + boards: seq, last pass, last error
  GET  /data?board=<name>          the view payload + seq
  GET  /wait?board=<name>&seq=<n>[&boot=<s>]
                                   long-poll: 200 {seq, boot} on change, 204
                                   quiet — and 200 at once on a stale boot,
                                   which tells the page to reload its code
  GET  /board/<name>               the view itself
  GET  /                           302 to a board — the title is the switcher,
                                   so there is no index page to keep
  GET  /prd?board=<name>&rel=<rel> one PRD in full: frontmatter, body, specs
  GET  /report?board=<name>        `prds/report.md`, the board for a person
  GET  /memos?board=<name>         the board's decision records
  GET  /answers?board=<name>       every question the board has answered,
                                   newest first
  GET  /adapters                   configured launch targets: [{id, name}] —
                                   resources/board/adapters/*.json, see below
  POST /register {"cwd": path}     add the board found walking up from cwd
  POST /sync     {"board": name}   force a pass now
  POST /new      {"board","title","body"?,"parent"?,"priority"?,"est"?}
                                   write a new PRD
  POST /edit     {"board","prd","title"?,"fm"?,"body"?,"append"?}
                                   write one PRD — what the detail pane saves
  POST /report   {"board","prd","text"}   a worker's report → `## Report`
  POST /run      {"board","prd","adapter"?}
                                   launch that PRD's round with one configured
                                   adapter — its own command, its own prompt
                                   template (resources/board/adapters/*.json;
                                   `claude.json` ships by default). `adapter`
                                   optional only when exactly one is
                                   configured. Detached, cwd the repo root.
                                   `open` only; 409 otherwise
  POST /unregister {"board": name} stop watching it
  POST /stop                       shut the daemon down

Python 3 stdlib only.
"""
import datetime
import json
import os
import re
import shutil
import socket
import subprocess
import sys
# win: a cp1252 console cannot encode the box/greek glyphs this prints,
# and the trailing summary dies on UnicodeEncodeError. Force UTF-8 out.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan as planlib  # noqa: E402
import render as renderlib  # noqa: E402
import memos as memoslib  # noqa: E402
import edit as editlib  # noqa: E402
import transitions as translib  # noqa: E402 — the one writer of `state:`

PORT = int(os.environ.get("PEARDE_PORT", "8443"))
DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(DIR, "state")
REG_PATH = os.path.join(APP_DIR, "serve.json")
LOG_PATH = os.path.join(APP_DIR, "serve.log")
POLL_S = 1.0       # how often each board is stat-swept
SETTLE_S = 0.4     # a change must hold still this long before a sync
WAIT_MAX_S = 25    # long-poll ceiling; clients just re-poll

# Two reloaders, two stamps. The board hot-reloads its data. The page
# hot-reloads its own code, and the daemon hot-reloads itself — but they move
# separately now. `PY_SOURCES` is what the daemon re-execs on: `render.py` was
# imported once, so editing it changes nothing until the process is replaced.
# `view.js` and `view.css` never need a re-exec — the page fetches them by
# stamp, and a live page re-imports a moved view without a reload.
PY_SOURCES = [os.path.join(DIR, f)
              for f in ("serve.py", "render.py", "plan.py", "edit.py",
                        "transitions.py")]
PY_SOURCES.append(os.path.join(os.path.dirname(DIR), "memos.py"))
VIEW_SOURCES = [os.path.join(DIR, f) for f in ("view.css", "view.js")]


def source_stamp():
    """The Python code — what a re-exec gives a fresh copy of."""
    return ",".join(str(os.stat(p).st_mtime_ns)
                    for p in PY_SOURCES if os.path.exists(p))


def view_stamp():
    """The page's own code — what an open page swaps in place, no reload.

    Baked into the served page and returned on every /wait, so an open page
    that renders against a stale stamp re-imports `view.js` where it stands
    (LIVE_JS), and the ?v= on each linked asset busts the browser's cache of
    it. Not part of the re-exec: the daemon only serves these two files."""
    return ",".join(str(os.stat(p).st_mtime_ns)
                    for p in VIEW_SOURCES if os.path.exists(p))


BOOT = source_stamp()
REFUSED = None     # a stamp that would not compile; do not say so twice


# ── boards ─────────────────────────────────────────────────────────────────────

def serve_name(path):
    """The daemon's board key: the repo name, plus the dot-dirs between it and
    prds/ — `racer/.mi/prds` keys as `racer-mi`, `realm/.claude/prds` as
    `realm-claude`. Two boards may legitimately want the same name, but a
    daemon key cannot: it is the watch entry and the /board/ URL, and two
    boards must never share one.

    This is the name that must always exist and always be unique, so it stays a
    pure function of the path. A board that renamed itself is preferred over it
    by `register()`, which can see whether that name is free — see
    `declared_name()`."""
    dots, d = [], os.path.dirname(os.path.abspath(path))
    while d and d != "/":
        base = os.path.basename(d)
        if not base.startswith("."):
            break
        dots.append(re.sub(r"[^A-Za-z0-9_-]", "", base))
        d = os.path.dirname(d)
    return "-".join([planlib.project_name(path)] + list(reversed(dots)))


class Board:
    def __init__(self, path):
        self.path = path  # the prds/ directory
        self.name = serve_name(path)
        self.seq = 0
        self.refs = ()      # the repos' refs, so a merge is a change too
        self.digest = None       # of the .md files — what "changed" means
        self.plan_digest = None  # of after+planned_at — fires a mirror
                                 # when `plan` re-ordered
        self.last_sync = None
        self.last_error = None
        self.history_day = None
        self.lock = threading.Lock()      # one mirror pass at a time
        self.cond = threading.Condition()  # /wait sleepers


BOARDS = {}  # name → Board
BOARDS_LOCK = threading.Lock()

# ── the Start button: a click launches a round ────────────────────────────────
# The view has no way to drive a Claude Code session itself — the daemon does,
# since it already runs local Python with subprocess access. RUNNING tracks one
# in-flight launch per (board, prd) so a second click while the first round is
# still starting up is refused rather than spawning a duplicate session; it is
# not the board's own claim tracking (`claim:` in the PRD, which the spawned
# round writes for itself once it picks the PRD up) and is dropped the moment
# the process this daemon started exits.
RUNNING = {}  # (board name, prd rel) → Popen
RUN_LOCK = threading.Lock()

ADAPTERS_DIR = os.path.join(DIR, "adapters")


def load_adapters():
    """Every configured launch target — one JSON file per adapter in
    resources/board/adapters/. `{"name": <picker label>, "command":
    [argv...], "prompt": <template, default "/pearde run {rel}">}`.
    `{prompt}` in `command` is replaced by the rendered prompt string,
    `{rel}` in either by the PRD's relative path. Each adapter phrases its
    own prompt: a pearde-aware agent (claude.json ships one) gets the
    `/pearde run <rel>` handle; an adapter for something that has never
    heard of pearde would instead template a plain-language task
    description in its own `prompt` field — this function does not care
    which, it only fills in placeholders.

    Missing dir or no valid files: empty list — the Start button then
    simply does not render (`ADAPTERS.length > 0` in view.js), same as an
    unserved page today. A malformed file is skipped with a stderr line,
    not a crash: one bad adapter must not take the others down with it."""
    if not os.path.isdir(ADAPTERS_DIR):
        return []
    out = []
    for fn in sorted(os.listdir(ADAPTERS_DIR)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(ADAPTERS_DIR, fn)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            command = data.get("command")
            if not isinstance(command, list) or not command or not all(
                    isinstance(p, str) for p in command):
                raise ValueError("'command' must be a non-empty list of strings")
            out.append({
                "id": fn[:-5],
                "name": data.get("name") or fn[:-5],
                "command": command,
                "prompt": data.get("prompt") or "/pearde run {rel}",
            })
        except Exception as e:
            print(f"serve: adapter {fn!r} invalid, skipped ({e})", file=sys.stderr)
    return out


def adapter_bin(argv0):
    """Resolves one adapter's command[0] to a runnable path. An adapter that
    already names an existing absolute path is trusted as-is — an install
    with two adapters under test, each its own stand-in binary, needs both
    to resolve independently. Only a bare/relative name (the common case:
    `"claude"`, found via PATH) falls through to `PEARDE_ADAPTER_BIN`,
    which overrides *that* resolution for a machine where it is not the
    PATH entry, or a build under test naming its own; replaces the old
    adapter-specific `PEARDE_CLAUDE_BIN` now that an install can configure
    more than one adapter."""
    if os.path.isabs(argv0) and os.path.exists(argv0):
        return argv0
    override = os.environ.get("PEARDE_ADAPTER_BIN")
    if override:
        return override
    return shutil.which(argv0)


def plan_digest(path):
    """Of the plan alone — its edges and the day it was made. Hashing the
    content rather than stat-ing the file means a write that changed no order
    is not a change: the watcher fires when `plan` actually re-ordered."""
    mp, _ = planlib.load_map(path)
    return hash(json.dumps([mp.get("after"), mp.get("planned_at")],
                           sort_keys=True))


def member_paths(path):
    """The member boards of a master, the live ones only. Read fresh on every
    pass: `members:` is a setting, and a board joins or leaves a master by one
    line in settings.md — the daemon must not need a restart for that."""
    try:
        return [p for _, p in planlib.members(path) if os.path.isdir(p)]
    except Exception:
        return []


def lane_digest(path):
    """The board's git side: the refs of every repo it draws lanes from. A
    lane merging into main moves these and nothing else — the landing queue
    shrinks, the plan does not change — so this is watched apart from the
    board's own files and answered with a bump rather than a whole sync."""
    return tuple(planlib.ref_stamp(p)
                 for _, p in (planlib.members(path) or [(None, path)]))


def digest(path):
    """(rel, mtime, size) over every .md under the board — prd.md, specs,
    memos, settings — plus the board's own `view.user.css` and `view.user.js`,
    and the same under every member board when this is a master: the master's
    plan is a function of their states, so a change there is a change here.
    The map file and the rendered gantt are ours and excluded, or every sync
    would trigger the next.

    A user asset is board content, not skill source — it belongs here rather
    than in SOURCES, so editing one reloads the page without re-execing the
    daemon."""
    rows = []
    roots = [path] + member_paths(path)
    mdir, external = memoslib.memos_dir(path)
    if external and os.path.isdir(mdir):
        roots.append(mdir)  # decisions living outside the board still mirror live
    for base in roots:
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                if f.endswith(".md") or (root == base and f in (
                        renderlib.USER_CSS, renderlib.USER_JS)):
                    fp = os.path.join(root, f)
                    try:
                        st = os.stat(fp)
                    except OSError:
                        continue
                    # keyed by root too: two boards under one master both
                    # have a settings.md, and one rel must not shadow the other
                    rows.append((base + "::" + os.path.relpath(fp, base),
                                 st.st_mtime_ns, st.st_size))
    return hash(tuple(sorted(rows)))


EPHEMERAL = ("/tmp/", "/private/tmp/", "/var/folders/", "/private/var/folders/")


def load_registry():
    """A board on an ephemeral filesystem registers but never persists — it
    would be a dead entry after the next reboot, and the registry must not
    accumulate those."""
    try:
        rows = json.load(open(REG_PATH, encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [p for p in rows if not p.startswith(EPHEMERAL)]


REGISTRY_LOADED = False   # only the daemon holds the whole list


def save_registry():
    """Persist the watch list, but only in a process that read it first.

    `register()` saves as a side effect. Without the flag, importing this
    module and calling it — an in-process test of the naming, say — writes the
    registry from whatever partial set that process holds and drops every board
    it did not register. The daemon sets the flag once it has loaded the file.
    Every other process keeps the registry read-only by construction."""
    if not REGISTRY_LOADED:
        return
    os.makedirs(APP_DIR, exist_ok=True)
    with BOARDS_LOCK:
        paths = sorted(b.path for b in BOARDS.values()
                       if not b.path.startswith(EPHEMERAL))
    json.dump(paths, open(REG_PATH, "w", encoding="utf-8"), indent=1)


def declared_name(path):
    """`name:` from the board's settings.md, or "" — one name across the
    project, the watch entry and the `/board/<name>` URL. A master board needs
    it: it is named for what it owns, not for the directory it sits in.

    A preference, not a key. Two projects may share a name on purpose —
    `realm/.mi/prds` and `realm/.claude/prds` both declare `realm` to mirror
    into one project. Two boards must never share a watch key, so `register()`
    takes this name only when it is free and falls back to the path
    derivation, which is unique by construction — the loser keeps its
    meaningful `realm-claude` instead of an order-dependent `realm-2`."""
    declared = str(planlib.board_settings(path).get("name", "")).strip()
    return re.sub(r"[^A-Za-z0-9_.-]", "-", declared) if declared else ""


def register(path):
    """Add one prds/ dir. The board's declared name keys it when that name is
    free, else the project-dir name — two boards sharing a name is already the
    collision `register()` breaks by suffixing."""
    path = os.path.abspath(path)
    b = Board(path)
    with BOARDS_LOCK:
        for name, cur in BOARDS.items():
            if cur.path == path:
                return cur, False
        want = declared_name(path)
        if want and want not in BOARDS:
            b.name = want
        n = 2
        while b.name in BOARDS:  # same key, different path: suffix, never replace
            b.name = f"{serve_name(path)}-{n}"
            n += 1
        BOARDS[b.name] = b
    save_registry()
    return b, True


def boards():
    with BOARDS_LOCK:
        return list(BOARDS.values())


def by_name(name):
    with BOARDS_LOCK:
        return BOARDS.get(name or "")


# ── the mirror pass ────────────────────────────────────────────────────────────

def bump(b):
    with b.cond:
        b.seq += 1
        b.cond.notify_all()


def history(b):
    """One row a day per board, written by whoever is watching. It is the only
    memory the board has — without it the burn-down has nothing to draw."""
    try:
        row = planlib.write_history(b.path)
        b.history_day = row["d"]
    except Exception:
        pass


def mirror(b, force=False):
    """One pass over a board that changed: re-order its schedule, write the
    day's history row, bump the sequence every reader is parked on. It writes
    nothing but the board's own files."""
    with b.lock:
        # Every board re-orders before it mirrors, master or not. A master's
        # plan spans repos nobody re-plans by hand. A plain board's goes stale
        # for a nearer reason — a held PRD weighs what is LEFT of it, so
        # closing one acceptance box re-sizes its bar and moves everything
        # downstream. The anchor day is kept: `plan` re-anchors, this only
        # re-orders, and reconcile returns early when nothing moved.
        try:
            planlib.reconcile(b.path)
        except SystemExit:
            b.last_error = "plan: needs cycle — reconcile skipped"
        except Exception as e:
            b.last_error = f"reconcile: {type(e).__name__}: {e}"
        bump(b)
        try:
            if b.history_day != datetime.date.today().isoformat():
                history(b)
            b.plan_digest = plan_digest(b.path)
            b.last_sync = time.time()
            b.last_error = None
        except Exception as e:  # a pass must never kill the watcher
            b.last_error = f"{type(e).__name__}: {e}"


def restart(stamp):
    """This view's own code moved — replace the process with itself.

    Safe because nothing lives in memory that is not also on disk: the
    registry is state/serve.json and `run` reloads it, the listening socket is
    not inherited across exec so the port frees itself, and every client parked
    on /wait reconnects on its own and finds the new BOOT. A file caught
    half-written does not compile — say so once and keep serving the old code
    rather than exec'ing into a daemon that cannot start."""
    global REFUSED
    time.sleep(SETTLE_S)              # an editor mid-save settles first
    if source_stamp() != stamp:
        return                        # still moving; the next tick finds it
    for p in PY_SOURCES:
        # every source here is Python — a page's .css and .js are not reloaded
        # by re-exec any more: they are served by stamp, read fresh on each
        # request, and a live page re-imports a moved view without a reload.
        if not p.endswith(".py"):
            continue
        try:
            with open(p, "rb") as fh:
                compile(fh.read(), p, "exec")
        except SyntaxError as e:
            REFUSED = stamp
            print(f"serve: {os.path.basename(p)}:{e.lineno}: {e.msg} "
                  f"— not reloading", flush=True)
            return
        except OSError:
            return
    print("serve: source changed — reloading", flush=True)
    sys.stdout.flush()
    os.execv(sys.executable,
             [sys.executable, os.path.abspath(__file__), "run"])


def watch():
    last_view = None
    while True:
        stamp = source_stamp()
        if stamp != BOOT and stamp != REFUSED:
            restart(stamp)
        # the page's own code moved — wake every parked /wait so the pages
        # learn the new view stamp now, not after their 25s timeout
        vs = view_stamp()
        if vs != last_view:
            last_view = vs
            for b in boards():
                with b.cond:
                    b.cond.notify_all()
        for b in boards():
            try:
                d = digest(b.path)
            except OSError:
                d = None
            if d is not None and d != b.digest:
                time.sleep(SETTLE_S)  # a worker mid-write settles first
                d2 = digest(b.path)
                if d2 == d:           # still moving? next tick finds it at rest
                    b.digest = d2
                    mirror(b)
            elif d is not None and plan_digest(b.path) != b.plan_digest:
                mirror(b)             # `plan` moved, and it writes only the map
            else:
                try:
                    refs = lane_digest(b.path)
                except OSError:
                    refs = b.refs
                if refs != b.refs:    # a lane landed: redraw, do not re-plan
                    b.refs = refs
                    bump(b)
        time.sleep(POLL_S)


# ── http ───────────────────────────────────────────────────────────────────────

LIVE_JS = """<script>
/* The board moved. Fetch the payload and hand it to the page, which swaps it
   in where it stands — scroll, zoom, selection and the open inspector all
   survive. A page that cannot swap, or a payload that will not parse, reloads.

   The view's own code moving is the other case, and a swap cannot help there:
   the page was rendered against a stamp a newer view.js no longer is, so it
   re-imports the module where it stands. The new module disposes the
   listeners the old copy left behind and mounts itself — from a payload made
   fresh just before, and with the dirty inspector and the scroll handed over
   in __pearde_restore. No reload: the daemon's JSON contract never changed,
   so only the page itself has to come across. */
(async () => {
  let seq = __SEQ__;
  let view = "__VIEW__";   // the page's own code this page was rendered from
  for (;;) {
    try {
      const base = window.__BASE || "";
      // the page's own view stamp travels with the poll — the daemon answers
      // at once when the view's code moved, so a page does not wait out a
      // board's silence to hear that its own file changed
      const r = await fetch(base + "/wait?board=__NAME__&seq=" + seq +
                            "&view=" + encodeURIComponent(view));
      if (r.status === 200) {
        const out = await r.json();
        if (out.view && out.view !== view) {
          view = out.view;
          // hand the half-typed inspector and the scroll to the next copy
          if (typeof window.__pearde_save === "function") window.__pearde_save();
          try {
            const d = await (await fetch(base + "/data?board=__NAME__")).json();
            if (d.payload) window.__PAYLOAD__ = d.payload;
            await import(base + "/view.js?v=" + encodeURIComponent(view));
          } catch (e) { location.reload(); return; }
          seq = out.seq;
          continue;
        }
        seq = out.seq;
        // never write over someone typing in the inspector — the page is
        // live, but a half-written body is not the board's to throw away.
        // Hold, and pick the change up when the field is clean.
        while (window.__pearde_hold && window.__pearde_hold())
          await new Promise(s => setTimeout(s, 2000));
        if (window.__pearde_refresh) await window.__pearde_refresh();
        else { location.reload(); return; }
      }
    } catch (e) { await new Promise(s => setTimeout(s, 3000)); }
  }
})();
</script>"""


def board_json(b):
    return {"name": b.name, "path": b.path, "seq": b.seq,
            "last_sync": b.last_sync, "last_error": b.last_error,
            "members": [n for n, _ in planlib.members(b.path)]}


class Handler(BaseHTTPRequestHandler):
    server_version = "pearde-serve"

    def log_message(self, fmt, *args):  # requests go to serve.log, quietly
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def reply(self, code, body, ctype="application/json"):
        raw = body if isinstance(body, bytes) else (
            body.encode() if isinstance(body, str)
            else json.dumps(body).encode())
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    # A prefix a reverse proxy may mount this under. Stripped here and
    # remembered, so every route below is written once and the page it renders
    # knows which base its own fetches have to use.
    PREFIX = "/timeline"

    def q(self):
        from urllib.parse import urlparse, parse_qs
        u = urlparse(self.path)
        path = u.path
        self.base = ""
        if path == self.PREFIX or path.startswith(self.PREFIX + "/"):
            self.base = self.PREFIX
            path = path[len(self.PREFIX):] or "/"
        return path, {k: v[0] for k, v in parse_qs(u.query).items()}

    def do_GET(self):
        path, q = self.q()
        if path == "/status":
            return self.reply(200, {"pid": os.getpid(), "port": PORT,
                                    "boot": BOOT,
                                    "boards": [board_json(b) for b in boards()]})
        if path == "/data":
            b = by_name(q.get("board"))
            if not b:
                return self.reply(404, {"error": "unknown board"})
            # enriched, not raw: the critical-path arithmetic is Python's, and
            # the page swaps this payload in without a reload — so what it gets
            # here has to be exactly what the initial render embedded.
            payload = renderlib.enrich(planlib.gantt_payload(
                b.path, planlib.scan(b.path), planlib.load_map(b.path)[0],
                planlib.board_settings(b.path)))
            return self.reply(200, {"seq": b.seq, "payload": payload})
        if path in ("/view.js", "/view.css"):
            # the page's own code, served as files so a live page can re-import
            # a moved view where it stands. Every request reads the file fresh;
            # the `?v=` stamp on the page's links is the cache-buster, so these
            # are served uncached — what the browser already has is never stale
            # for long enough to matter. Python never re-execs for these: an
            # open page swaps the new module in on its own.
            name = path[1:]
            try:
                body = open(os.path.join(DIR, name), encoding="utf-8").read()
            except OSError:
                return self.reply(404, {"error": "no such asset"})
            ctype = ("text/javascript; charset=utf-8" if name == "view.js"
                     else "text/css; charset=utf-8")
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body.encode())))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body.encode())
            return
        if path == "/prd":
            # everything the timeline cannot fit on a bar: the PRD itself, its
            # specs and its file. The chart asks for this when a row is
            # clicked, so the view is a place to read the work and not only to
            # look at its shape.
            b = by_name(q.get("board"))
            if not b:
                return self.reply(404, {"error": "unknown board"})
            rel = q.get("rel") or ""
            prd = planlib.scan(b.path).get(rel)
            if not prd:
                return self.reply(404, {"error": f"no PRD at {rel}"})
            specs = []
            sdir = os.path.join(prd["dir"], "specs")
            for f in sorted(os.listdir(sdir)) if os.path.isdir(sdir) else []:
                if not f.endswith(".md"):
                    continue
                fm, title, body = planlib.parse_prd(os.path.join(sdir, f))
                closed, total = planlib.acceptance_of(body)
                specs.append({"file": f, "title": title or f,
                              "est": fm.get("est", ""),
                              "complexity": fm.get("complexity", ""),
                              "state": fm.get("state", ""),
                              "footprint": fm.get("footprint", []),
                              "boxes": [closed, total],
                              "body": body})
            return self.reply(200, {
                "rel": rel, "title": prd["title"], "state": prd["state"],
                "fm": {k: v for k, v in prd["fm"].items()},
                "body": prd["body"], "specs": specs,
                "path": prd.get("footer") or f"prds/{rel}/prd.md",
                "file": os.path.join(prd["dir"], "prd.md"),
                "board": prd.get("board"),
            })
        if path == "/answers":
            # what the board has already settled. The asks view takes an
            # answered question out of the inbox and shows it here instead,
            # newest first — so going through a round is a list that empties,
            # and a decision made a week ago is still readable next to it.
            b = by_name(q.get("board"))
            if not b:
                return self.reply(404, {"error": "unknown board"})
            out = []
            for rel, prd in planlib.scan(b.path).items():
                for a in planlib.answers_of(prd):
                    out.append(dict(a, rel=rel, prd=prd["title"],
                                    state=prd["state"], board=prd.get("board")))
            # by date, and a stamped answer sorts above an unstamped one:
            # undated is older than anything the view has written
            out.sort(key=lambda a: (a["date"] or "", a["rel"], a["id"]),
                     reverse=True)
            return self.reply(200, {"answers": out})
        if path == "/memos":
            b = by_name(q.get("board"))
            if not b:
                return self.reply(404, {"error": "unknown board"})
            ms = memoslib.scan(b.path)
            out = [{"slug": m["slug"], "subject": m.get("subject"),
                    "kind": m.get("kind"), "status": m.get("status"),
                    "date": str(m.get("date") or ""), "path": m.get("path"),
                    "prds": (m["fm"].get("prds") if isinstance(
                        m["fm"].get("prds"), list) else
                        [m["fm"]["prds"]] if m["fm"].get("prds") else []),
                    "body": m.get("body", "")}
                   for m in ms.values()]
            out.sort(key=lambda m: (str(m["status"]), str(m["date"])),
                     reverse=True)
            return self.reply(200, {"memos": out})
        if path == "/adapters":
            return self.reply(200, [{"id": a["id"], "name": a["name"]}
                                    for a in load_adapters()])
        if path == "/report":
            # the board's state for a person — `prds/report.md`, read from
            # disk on each call like `/prd`. Not parsed here: the page renders
            # the text, and an absent file is `null`, which draws nothing.
            b = by_name(q.get("board"))
            if not b:
                return self.reply(404, {"error": "unknown board"})
            fp = os.path.join(b.path, "report.md")
            try:
                text = open(fp, encoding="utf-8").read()
            except OSError:
                text = None
            return self.reply(200, {"text": text, "path": fp})
        if path == "/wait":
            b = by_name(q.get("board"))
            if not b:
                return self.reply(404, {"error": "unknown board"})
            try:
                since = int(q.get("seq", "-1"))
            except ValueError:
                since = -1
            # the page tells us which view it was rendered against. If the
            # files it needs moved since then it answers now, not in 25s —
            # there is no board change to wait for, the page has to re-import.
            cur_view = view_stamp()
            if q.get("view") is not None and q.get("view") != cur_view:
                return self.reply(200, {"seq": b.seq, "view": cur_view,
                                        "last_error": b.last_error})
            with b.cond:
                if b.seq == since:
                    b.cond.wait(WAIT_MAX_S)
                if b.seq == since:
                    return self.reply(204, b"")
                return self.reply(200, {"seq": b.seq, "view": view_stamp(),
                                        "last_error": b.last_error})
        ROUTES = ("/", "/status", "/data", "/wait", "/prd", "/memos",
                  "/answers", "/view.js", "/view.css")
        want = None
        if path.startswith("/board/") or path.startswith("/timeline/"):
            want = path.split("/", 2)[2].strip("/")
        elif self.base and path not in ROUTES and path.count("/") == 1:
            # behind the proxy the friendly form is /timeline/<board>, so a
            # single unrecognised segment under the prefix is a board name
            want = path[1:]
        if want is not None:
            b = by_name(want)
            if not b:
                return self.reply(404, "unknown board", "text/plain")
            payload = planlib.gantt_payload(
                b.path, planlib.scan(b.path), planlib.load_map(b.path)[0],
                planlib.board_settings(b.path))
            head = (f'<script>window.__BASE={json.dumps(self.base)};'
                    f'window.__BOARD={json.dumps(b.name)};</script>')
            live = "" if q.get("nolive") else (
                LIVE_JS.replace("__NAME__", b.name)
                       .replace("__SEQ__", str(b.seq))
                       .replace("__VIEW__", view_stamp()))
            # the shell links the view as files, so an open page can re-import
            # a moved `view.js` where it stands; the payload and the report's
            # mtime are baked as globals ahead of the module. The head's own
            # __BASE/__BOARD go in first — the module reads all four off window.
            html = (renderlib.render_shell(payload, b.path, self.base,
                                           view_stamp())
                    .replace("</head>", head + "</head>")
                    .replace("</body>", live + "</body>"))
            return self.reply(200, html, "text/html; charset=utf-8")
        if path == "/":
            # The board title is the switcher, so there is no index page.
            # Land on a board — the master if one is registered, since it is
            # the merged view, else the first by name. The bare list covers
            # the one case the switcher cannot: no board registered at all.
            bs = sorted(boards(), key=lambda x: x.name)
            if bs:
                first = next((b for b in bs if planlib.is_master(b.path)), bs[0])
                self.send_response(302)
                self.send_header("Location", f"{self.base}/board/{first.name}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            return self.reply(200,
                "<!doctype html><meta charset=utf-8>"
                "<title>pearde</title>"
                "<body style='font:14px system-ui;padding:2em'>"
                "<h1>no board registered</h1>"
                "<p><code>resources/board/serve.py ensure &lt;path&gt;</code> "
                "registers one.</p>",
                "text/html; charset=utf-8")
        self.reply(404, {"error": "no such route"})

    def do_POST(self):
        path, _ = self.q()
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return self.reply(400, {"error": "bad json"})
        if path == "/register":
            try:
                board = planlib.find_board(body.get("cwd") or None)
            except SystemExit:
                return self.reply(404, {"error": "no prds/ found from cwd"})
            b, new = register(board)
            if new:
                threading.Thread(target=mirror, args=(b, True),
                                 daemon=True).start()
            # Registering a master registers its members too: each member keeps
            # its own project, and a member nobody watches would mirror only
            # when its own session happens to be open.
            brought = []
            for path in member_paths(board):
                mb, mnew = register(path)
                if mnew:
                    brought.append(mb.name)
                    threading.Thread(target=mirror, args=(mb, True),
                                     daemon=True).start()
            return self.reply(200, {"board": board_json(b), "new": new,
                                    "members": brought})
        if path == "/sync":
            b = by_name(body.get("board"))
            if not b:
                return self.reply(404, {"error": "unknown board"})
            mirror(b, force=True)
            return self.reply(200, board_json(b))
        if path == "/new":
            # Filing work from the view. The template is the board's own, so a
            # PRD written here is the same shape as one written by hand — and
            # `origin: requested` because a person asked for it.
            b = by_name(body.get("board"))
            if not b:
                return self.reply(404, {"error": "unknown board"})
            # `transitions.add` is the one way a PRD is filed: the slug is
            # its gate, and the line it prints lands in serve.log.
            try:
                rel = translib.add(
                    b.path, body.get("title") or "", "view",
                    priority=int(body.get("priority") or 0),
                    body=body.get("body") or "",
                    parent=(body.get("parent") or "").strip("/") or None,
                    out=lambda line: print(line, flush=True))
            except translib.Refused as e:
                return self.reply(409, {"error": str(e)})
            except ValueError:
                return self.reply(400, {"error": "priority is an integer"})
            threading.Thread(target=mirror, args=(b,), daemon=True).start()
            return self.reply(200, {"prd": rel})
        if path == "/edit":
            # The view writes the board one structured line at a time,
            # atomically, frontmatter and body never in the same write.
            # A claim is reported, not enforced — whoever is looking at this
            # page is the authority.
            b = by_name(body.get("board"))
            if not b:
                return self.reply(404, {"error": "unknown board"})
            rel = body.get("prd") or ""
            prd = planlib.scan(b.path).get(rel)
            if not prd:
                return self.reply(404, {"error": f"no PRD at {rel}"})
            path_md = os.path.join(prd["dir"], "prd.md")
            # body first: it replaces everything under the frontmatter, so a
            # title written before it would be the first thing overwritten
            wrote = []
            if body.get("body") is not None:
                editlib.set_body(path_md, str(body["body"]))
                wrote.append("body")
            if body.get("append"):
                editlib.append_section(path_md, body.get("heading", "Notes"),
                                       str(body["append"]))
                wrote.append("append")
            if body.get("title"):
                editlib.set_title(path_md, str(body["title"])[:250])
                wrote.append("title")
            fm = dict(body.get("fm") or {})
            # `state:` has one writer — the transition. A person at the page
            # is the user talking to the board and is not gated, so the call
            # is forced, and the line in serve.log says `forced · view`.
            # It goes last: the answer flow appends the answer and sets
            # `open` in one call, and the gate reads the file as appended.
            state = fm.pop("state", None)
            for k, v in fm.items():
                if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", str(k)):
                    continue
                if v in (None, ""):
                    editlib.del_key(path_md, k)
                else:
                    editlib.set_key(path_md, k, str(v).replace("\n", " "))
                wrote.append(k)
            if state not in (None, ""):
                try:
                    translib.transition(
                        b.path, rel, str(state).strip(), "view", force=True,
                        source="view",
                        out=lambda line: print(line, flush=True))
                    wrote.append("state")
                except translib.Refused as e:
                    if wrote:
                        threading.Thread(target=mirror, args=(b,),
                                         daemon=True).start()
                    return self.reply(409, {"error": str(e), "wrote": wrote,
                                            "prd": rel})
            if wrote:
                threading.Thread(target=mirror, args=(b,), daemon=True).start()
            return self.reply(200, {"wrote": wrote, "prd": rel,
                                    "claim": prd["fm"].get("claim")})
        if path == "/report":
            # A worker's report is evidence — it belongs with the PRD it is
            # evidence about. Appended to `## Report`, nothing else.
            b = by_name(body.get("board"))
            if not b:
                return self.reply(404, {"error": "unknown board"})
            rel, text = body.get("prd", ""), body.get("text", "")
            if not rel or not text:
                return self.reply(400, {"error": "prd and text required"})
            prd = planlib.scan(b.path).get(rel)
            if not prd:
                return self.reply(404, {"error": f"no PRD at {rel}"})
            editlib.append_section(os.path.join(prd["dir"], "prd.md"),
                                   "Report", text)
            threading.Thread(target=mirror, args=(b,), daemon=True).start()
            return self.reply(200, {"wrote": f"{rel}/prd.md"})
        if path == "/run":
            # The Start button. Only `open` is offered one in the view, and
            # this is the server-side half of that same rule — a stale page,
            # or a second tab, must not launch a round on a PRD that already
            # moved on.
            b = by_name(body.get("board"))
            if not b:
                return self.reply(404, {"error": "unknown board"})
            rel = body.get("prd") or ""
            prd = planlib.scan(b.path).get(rel)
            if not prd:
                return self.reply(404, {"error": f"no PRD at {rel}"})
            if prd["state"] != "open":
                return self.reply(409, {"error":
                    f"{rel} is {prd['state']}, not open"})

            adapters = load_adapters()
            if not adapters:
                return self.reply(500, {"error":
                    "no adapter configured — add one under resources/board/adapters/"})
            adapter_id = body.get("adapter")
            if adapter_id:
                adapter = next((a for a in adapters if a["id"] == adapter_id), None)
                if not adapter:
                    return self.reply(404, {"error": f"no adapter {adapter_id!r}"})
            elif len(adapters) == 1:
                adapter = adapters[0]
            else:
                # The view only shows a picker at 2+ adapters and always
                # sends one; a caller that skips the picker (a script, an
                # older cached page) is the only way to land here.
                return self.reply(400, {"error":
                    "multiple adapters configured, specify one",
                    "adapters": [a["id"] for a in adapters]})

            key = (b.name, rel)
            with RUN_LOCK:
                cur = RUNNING.get(key)
                if cur and cur.poll() is None:
                    return self.reply(409, {"error": "already starting"})

            # Each adapter renders its own prompt template (a pearde-aware
            # agent gets "/pearde run <rel>"; one that has never heard of
            # pearde gets whatever plain-language task text its own
            # adapters/*.json spells out) and its own command argv — this
            # daemon does not assume either.
            prompt = adapter["prompt"].format(rel=rel)
            argv = [part.format(prompt=prompt, rel=rel) for part in adapter["command"]]
            resolved = adapter_bin(argv[0])
            if not resolved:
                return self.reply(500, {"error":
                    f"{argv[0]!r} not found on PATH — set PEARDE_ADAPTER_BIN "
                    f"or fix the {adapter['id']} adapter's command"})
            argv[0] = resolved

            os.makedirs(APP_DIR, exist_ok=True)
            safe = re.sub(r"[^A-Za-z0-9_-]", "_", f"{b.name}-{rel}")
            log = open(os.path.join(APP_DIR, f"run-{safe}.log"), "a")
            try:
                # Windows resolves many CLI launchers (via shutil.which) to a
                # .CMD shim — CreateProcess cannot launch that directly, only
                # cmd.exe can, so this one call needs shell=True there. POSIX
                # never does: shell=True with a list there hands the extra
                # args to the shell itself as $0/$1, not to the command, so
                # the CLI would run with none of its arguments. Not
                # adapter-specific — any adapter's Windows binary can be a
                # shim, so this stays unconditional on `os.name`.
                #
                # stdin is a PIPE, closed right after spawn, rather than left
                # to inherit: `view` starts this daemon detached on Windows,
                # so it has no stdin handle of its own to hand down, and on
                # Windows that absence — not the missing console some of its
                # symptoms suggest — is what makes the Junie CLI's own
                # console-mode probe on startup fail and exit immediately
                # with ERROR_INVALID_FUNCTION ("Unzulässige Funktion"),
                # before it ever looks at the task it was given (confirmed:
                # neither a fresh console via CREATE_NEW_CONSOLE nor
                # stdin=DEVNULL fixes it — only a real, if immediately
                # closed, pipe does). A closed PIPE reads as a clean EOF, the
                # same as any adapter expecting no stdin sees today.
                proc = subprocess.Popen(
                    argv, cwd=os.path.dirname(b.path), stdout=log, stderr=log,
                    stdin=subprocess.PIPE, start_new_session=True,
                    shell=(os.name == "nt"))
                proc.stdin.close()
            except OSError as e:
                return self.reply(500, {"error": f"could not start: {e}"})
            with RUN_LOCK:
                RUNNING[key] = proc
            return self.reply(200, {"started": True, "board": b.name,
                                    "prd": rel, "adapter": adapter["id"],
                                    "pid": proc.pid})
        if path == "/unregister":
            name = body.get("board")
            with BOARDS_LOCK:
                b = BOARDS.pop(name or "", None)
            if not b:
                return self.reply(404, {"error": "unknown board"})
            save_registry()
            return self.reply(200, {"forgot": name})
        if path == "/stop":
            self.reply(200, {"stopping": True})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        self.reply(404, {"error": "no such route"})


# ── daemon lifecycle ───────────────────────────────────────────────────────────

def call(path, payload=None, timeout=3):
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json"},
        method="POST" if payload is not None else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        return json.loads(raw) if raw else {}


def running():
    try:
        return call("/status")
    except (urllib.error.URLError, OSError):
        return None


def cmd_run():
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        print(f"serve: port {PORT} is taken — a daemon already runs "
              f"(or set PEARDE_PORT)", file=sys.stderr)
        return 1
    global REGISTRY_LOADED
    for p in load_registry():
        if os.path.isdir(p):
            register(p)
    REGISTRY_LOADED = True   # from here the in-memory set IS the registry
    threading.Thread(target=watch, daemon=True).start()
    print(f"serve: watching on http://127.0.0.1:{PORT} — "
          f"{len(boards())} board(s)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def cmd_ensure(arg):
    if not running():
        os.makedirs(APP_DIR, exist_ok=True)
        log = open(LOG_PATH, "a")
        subprocess.Popen([sys.executable, os.path.abspath(__file__), "run"],
                         stdout=log, stderr=log, start_new_session=True)
        for _ in range(50):
            if running():
                break
            time.sleep(0.1)
        else:
            print(f"serve: daemon did not come up — see {LOG_PATH}",
                  file=sys.stderr)
            return 1
        print(f"serve: started on http://127.0.0.1:{PORT}")
    board = planlib.find_board(arg)  # dies with the usual message if none
    out = call("/register", {"cwd": board})
    b = out["board"]
    print(f"serve: {'registered' if out['new'] else 'watching'} {b['name']} "
          f"· {b['path']} · live view http://127.0.0.1:{PORT}/board/{b['name']}")
    if b.get("members"):
        print(f"serve: master of {len(b['members'])} board(s) — "
              + ", ".join(b["members"])
              + (f" · also registered: {', '.join(out['members'])}"
                 if out.get("members") else ""))
    return 0


def cmd_status():
    st = running()
    if not st:
        print("serve: not running")
        return 1
    print(f"serve: up on http://127.0.0.1:{st['port']} · pid {st['pid']}")
    for b in st["boards"]:
        age = (f"{int(time.time() - b['last_sync'])}s ago"
               if b["last_sync"] else "never")
        note = f" · {b['last_error']}" if b["last_error"] else ""
        mem = (f" · master of {len(b['members'])}: "
               + ", ".join(b["members"])) if b.get("members") else ""
        print(f"  {b['name']:16} synced {age}{note} · {b['path']}{mem}")
    return 0


def cmd_wait(arg, timeout):
    """Block until the board moves, then say what moved. An orchestrator with
    nothing left to dispatch parks here instead of ending the round — see
    @references/parts/loop.md.

    Exit 0 = something happened (the inbox, or any board change), 1 = the
    timeout ran out quietly, 2 = no daemon."""
    board = planlib.find_board(arg)
    st = running()
    if not st:
        print("serve: not running — nothing to wait on", file=sys.stderr)
        return 2
    name = next((b["name"] for b in st["boards"]
                 if os.path.abspath(b["path"]) == os.path.abspath(board)), None)
    if not name:
        print(f"serve: {board} is not registered — run `ensure` first",
              file=sys.stderr)
        return 2
    seq = next(b["seq"] for b in st["boards"] if b["name"] == name)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            out = call(f"/wait?board={name}&seq={seq}",
                       timeout=WAIT_MAX_S + 10)
        except (urllib.error.URLError, OSError):
            print("serve: daemon went away while waiting", file=sys.stderr)
            return 2
        if not out:
            continue                      # 25 quiet seconds; park again
        print(f"serve: {name} moved · seq {out.get('seq')}")
        return 0
    print(f"serve: {name} quiet for {timeout}s")
    return 1


def cmd_stop():
    if not running():
        print("serve: not running")
        return 0
    try:
        call("/stop", {})
    except (urllib.error.URLError, OSError):
        pass  # it died mid-reply, which is the goal
    print("serve: stopped")
    return 0


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "status"
    if cmd == "run":
        return cmd_run()
    if cmd == "ensure":
        return cmd_ensure(args[1] if len(args) > 1 else None)
    if cmd == "status":
        return cmd_status()
    if cmd == "stop":
        return cmd_stop()
    if cmd == "wait":
        rest = [a for a in args[1:] if not a.startswith("--")]
        return cmd_wait(rest[0] if rest else None,
                        next((int(a[len("--timeout="):]) for a in args
                              if a.startswith("--timeout=")), 900))
    if cmd == "forget":
        if len(args) < 2:
            print("serve: forget <board-name>", file=sys.stderr)
            return 2
        if not running():
            print("serve: not running")
            return 1
        try:
            call("/unregister", {"board": args[1]})
            print(f"serve: forgot {args[1]}")
            return 0
        except urllib.error.HTTPError:
            print(f"serve: no board named {args[1]}", file=sys.stderr)
            return 1
    print(__doc__.strip().split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
