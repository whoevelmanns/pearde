#!/usr/bin/env python3
"""pearde serve — the live board service: one daemon per machine, watching
every registered board and mirroring each change to Plane as it lands.

    serve.py ensure [board]   start the daemon if none runs, register a board
                              (default: walk up from the cwd); safe to run on
                              every session start
    serve.py run              the daemon, foreground — what `ensure` detaches
    serve.py status           the daemon and every board it watches
    serve.py forget <name>    stop watching one board (its Plane data stays)
    serve.py stop             stop the daemon

Singleton by port bind: the daemon owns 127.0.0.1:8443 (PLANE_SERVE_PORT
overrides), and a second `run` refuses to start because the bind fails. That
is the whole locking story — no pidfile to go stale.

What it does, per registered board, within about a second of a file changing:

  - re-orders a master board's waves in place, keeping the anchor day, so a
    state written in one member re-plans the whole board (sync.py's reconcile)
  - mirrors tickets and memo pages (sync.py's own cmd_sync, unchanged)
  - rewrites the waves as cycles when the plan changed (sync_cycles)
  - serves the adaptive timeline live at /board/<name> — the page long-polls
    /wait and reloads itself on every board change
  - bumps a per-board sequence number an agent can long-poll on /wait

The view works with no Plane at all — it renders from disk. Plane pushes are
skipped, and reported in /status, when the board has no .plane.env.

A board keys by repo name plus any dot-dirs on its path (`racer/.mi/prds` →
`racer-mi`), so two boards in one repo — or one Plane project mirroring two
boards on purpose — still get distinct watch entries and /board/ URLs.

A master board (`members:` in its settings.md) is watched over its members'
files too, and registering one registers every member as a board in its own
right: the master carries the merged plan, each member keeps its own project.

Disk stays the one source of truth: the daemon reads prds/ and writes Plane,
never the reverse, and it never writes PRD state — the orchestrator stays the
only writer. The registry and log live in plane-app/ (machine-local,
gitignored): serve.json, serve.log.

HTTP API, all JSON, all 127.0.0.1-only:

  GET  /status                     daemon + boards: seq, last sync, last error
  GET  /data?board=<name>          the timeline payload + seq
  GET  /wait?board=<name>&seq=<n>  long-poll: 200 {seq} on change, 204 quiet
  GET  /board/<name>               the live timeline page
  GET  /                           board index
  POST /register {"cwd": path}     add the board found walking up from cwd
  POST /sync     {"board": name}   force a mirror pass now
  POST /report   {"board": name, "prd": rel, "text": md}
                                   the worker's report as a ticket comment
  POST /unregister {"board": name} stop watching it (nothing in Plane changes)
  POST /stop                       shut the daemon down

Python 3 stdlib only.
"""
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sync as synclib  # noqa: E402
import gantt as ganttlib  # noqa: E402
import memos as memoslib  # noqa: E402

PORT = int(os.environ.get("PLANE_SERVE_PORT", "8443"))
DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(DIR, "plane-app")
REG_PATH = os.path.join(APP_DIR, "serve.json")
LOG_PATH = os.path.join(APP_DIR, "serve.log")
POLL_S = 1.0       # how often each board is stat-swept
SETTLE_S = 0.4     # a change must hold still this long before a sync
WAIT_MAX_S = 25    # long-poll ceiling; clients just re-poll


# ── boards ─────────────────────────────────────────────────────────────────────

def serve_name(path):
    """The daemon's board key: the repo name, plus the dot-dirs between it and
    prds/ — `racer/.mi/prds` keys as `racer-mi`, `realm/.claude/prds` as
    `realm-claude`. Plane's project name (walk-up only, PLANE_PROJECT_NAME
    override) can legitimately collide — realm mirrors two boards into one
    project on purpose — but a daemon key cannot: it is the watch entry and
    the /board/ URL, and two boards must never share one.

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
    return "-".join([synclib.project_name(path)] + list(reversed(dots)))


class Board:
    def __init__(self, path):
        self.path = path  # the prds/ directory
        self.name = serve_name(path)
        self.seq = 0
        self.digest = None       # of the .md files — what "changed" means
        self.plan_digest = None  # of waves+planned_at — when to redo cycles
        self.last_sync = None
        self.last_error = None
        self.lock = threading.Lock()      # one mirror pass at a time
        self.cond = threading.Condition()  # /wait sleepers


BOARDS = {}  # name → Board
BOARDS_LOCK = threading.Lock()


def plan_digest(path):
    """Of the plan alone — waves and the day it was made. The map's ticket
    hashes churn on every push (our own writes), so watching the file's mtime
    would loop; watching this content only fires when `plan` actually ran."""
    mp, _ = synclib.load_map(path)
    return hash(json.dumps([mp.get("waves"), mp.get("planned_at")],
                           sort_keys=True))


def member_paths(path):
    """The member boards of a master, the live ones only. Read fresh on every
    pass: `members:` is a setting, and a board joins or leaves a master by one
    line in settings.md — the daemon must not need a restart for that."""
    try:
        return [p for _, p in synclib.members(path) if os.path.isdir(p)]
    except Exception:
        return []


def digest(path):
    """(rel, mtime, size) over every .md under the board — prd.md, specs,
    memos, settings — and under every member board when this is a master: the
    master's plan is a function of their states, so a change there is a change
    here. The map file and the rendered gantt are ours and excluded, or every
    sync would trigger the next."""
    rows = []
    roots = [path] + member_paths(path)
    mdir, external = memoslib.memos_dir(path)
    if external and os.path.isdir(mdir):
        roots.append(mdir)  # decisions living outside the board still mirror live
    for base in roots:
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                if f.endswith(".md"):
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
    """A board on an ephemeral filesystem registers fine — a test wants the
    live view too — but never persists: it would be a dead entry after the
    next reboot, and dead entries are exactly what the registry must not
    accumulate."""
    try:
        rows = json.load(open(REG_PATH, encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [p for p in rows if not p.startswith(EPHEMERAL)]


REGISTRY_LOADED = False   # only the daemon has the whole list — see below


def save_registry():
    """Persist the watch list, but only in a process that read it first.

    `register()` saves as a side effect, so importing this module and calling
    it — an in-process test of the naming, say — used to write the registry
    from whatever partial set that process held and drop every board it had
    not registered. The daemon sets the flag once it has loaded the file; every
    other process keeps the registry read-only by construction."""
    if not REGISTRY_LOADED:
        return
    os.makedirs(APP_DIR, exist_ok=True)
    with BOARDS_LOCK:
        paths = sorted(b.path for b in BOARDS.values()
                       if not b.path.startswith(EPHEMERAL))
    json.dump(paths, open(REG_PATH, "w", encoding="utf-8"), indent=1)


def declared_name(path):
    """What the board calls itself, or "".

    `PLANE_PROJECT_NAME` is the name a board carries in Plane, so a board that
    renamed itself should answer to that name here too — one name in the
    project, the watch entry, and the `/board/<name>` URL. A master board is
    the case that needs it: it is named for what it owns rather than for the
    directory it sits in, and a plan that reads `master` everywhere except its
    own URL is a seam the user has to be told about.

    It is only a *preference*, because unlike a daemon key a project name may
    legitimately be shared — `realm/.mi/prds` and `realm/.claude/prds` both
    declare `realm` to mirror into one project on purpose. Two boards must
    never share a watch key, so `register()` takes this name only when it is
    free and falls back to the path derivation, which is unique by
    construction. That is better than suffixing the shared name: the loser
    keeps its own meaningful `realm-claude` instead of an order-dependent
    `realm-2`."""
    declared = str(synclib.board_settings(path).get("name", "")).strip()
    if not declared:
        cfg, _ = synclib.load_cfg(path)
        declared = (cfg or {}).get("PLANE_PROJECT_NAME", "").strip()
    return re.sub(r"[^A-Za-z0-9_.-]", "-", declared) if declared else ""


def register(path):
    """Add one prds/ dir. The board's declared name keys it when that name is
    free, else the project-dir name — two boards sharing a name is already the
    collision plane.md tells the user to break with PLANE_PROJECT_NAME."""
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


def mirror(b, force=False):
    """One pass: push tickets, memo pages, and — when the plan moved — cycles.
    The view's seq bumps regardless, so the local timeline is live even when
    the push fails or the board was never bootstrapped."""
    with b.lock:
        # A master board re-orders before it mirrors: its waves span repos
        # nobody re-plans by hand, so a state written in one member has to
        # re-order the whole board. The anchor day is kept — `plan` re-anchors,
        # this only re-orders. It runs with or without Plane: the local
        # timeline is the thing most likely to be read.
        if synclib.is_master(b.path):
            try:
                synclib.reconcile(b.path)
            except SystemExit:
                b.last_error = "plan: needs cycle — reconcile skipped"
            except Exception as e:
                b.last_error = f"reconcile: {type(e).__name__}: {e}"
        bump(b)
        cfg, cfg_path = synclib.load_cfg(b.path)
        if cfg is None:
            b.last_error = f"not bootstrapped — no {cfg_path}"
            return
        try:
            synclib.cmd_sync(b.path, quiet=True)
            pd = plan_digest(b.path)
            if force or pd != b.plan_digest:
                mp, _ = synclib.load_map(b.path)
                api = synclib.Api(cfg)
                pid = cfg.get("PLANE_PROJECT_ID")
                if pid and mp.get("waves"):
                    synclib.sync_cycles(api, pid, b.path, mp, quiet=True)
                b.plan_digest = pd
            b.last_sync = time.time()
            b.last_error = None
        except SystemExit:
            b.last_error = "sync failed — see serve.log"
        except Exception as e:  # a mirror pass must never kill the watcher
            b.last_error = f"{type(e).__name__}: {e}"


def watch():
    while True:
        for b in boards():
            try:
                d = digest(b.path)
            except OSError:
                continue
            if d == b.digest:
                # no .md moved — but `plan` may have: it writes only the map
                if plan_digest(b.path) != b.plan_digest:
                    mirror(b)
                continue
            time.sleep(SETTLE_S)  # a worker mid-write settles first
            d2 = digest(b.path)
            if d2 != d:
                continue  # still moving; next tick catches it at rest
            b.digest = d2
            mirror(b)
        time.sleep(POLL_S)


# ── http ───────────────────────────────────────────────────────────────────────

LIVE_JS = """<script>
(async () => {
  for (;;) {
    try {
      const r = await fetch("/wait?board=__NAME__&seq=__SEQ__");
      if (r.status === 200) { location.reload(); return; }
    } catch (e) { await new Promise(s => setTimeout(s, 3000)); }
  }
})();
</script>"""


def board_json(b):
    return {"name": b.name, "path": b.path, "seq": b.seq,
            "last_sync": b.last_sync, "last_error": b.last_error,
            "members": [n for n, _ in synclib.members(b.path)]}


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

    def q(self):
        from urllib.parse import urlparse, parse_qs
        u = urlparse(self.path)
        return u.path, {k: v[0] for k, v in parse_qs(u.query).items()}

    def do_GET(self):
        path, q = self.q()
        if path == "/status":
            return self.reply(200, {"pid": os.getpid(), "port": PORT,
                                    "boards": [board_json(b) for b in boards()]})
        if path == "/data":
            b = by_name(q.get("board"))
            if not b:
                return self.reply(404, {"error": "unknown board"})
            payload = synclib.gantt_payload(
                b.path, synclib.scan(b.path), synclib.load_map(b.path)[0],
                synclib.board_settings(b.path))
            return self.reply(200, {"seq": b.seq, "payload": payload})
        if path == "/wait":
            b = by_name(q.get("board"))
            if not b:
                return self.reply(404, {"error": "unknown board"})
            try:
                since = int(q.get("seq", "-1"))
            except ValueError:
                since = -1
            with b.cond:
                if b.seq == since:
                    b.cond.wait(WAIT_MAX_S)
                if b.seq == since:
                    return self.reply(204, b"")
                return self.reply(200, {"seq": b.seq,
                                        "last_error": b.last_error})
        if path.startswith("/board/"):
            b = by_name(path[len("/board/"):].strip("/"))
            if not b:
                return self.reply(404, "unknown board", "text/plain")
            payload = synclib.gantt_payload(
                b.path, synclib.scan(b.path), synclib.load_map(b.path)[0],
                synclib.board_settings(b.path))
            live = (LIVE_JS.replace("__NAME__", b.name)
                    .replace("__SEQ__", str(b.seq)))
            html = ganttlib.render(payload).replace("</body>", live + "</body>")
            return self.reply(200, html, "text/html; charset=utf-8")
        if path == "/":
            rows = "".join(
                f'<li><a href="/board/{b.name}">{b.name}</a>'
                f' <small>{b.path}'
                + (f" · <em>{b.last_error}</em>" if b.last_error else "")
                + "</small></li>"
                for b in sorted(boards(), key=lambda x: x.name))
            return self.reply(200,
                "<!doctype html><meta charset=utf-8>"
                "<title>pearde — boards</title>"
                "<body style='font:14px system-ui;padding:2em'>"
                f"<h1>boards</h1><ul>{rows or '<li>none registered</li>'}</ul>",
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
                board = synclib.find_board(body.get("cwd") or None)
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
        if path == "/report":
            b = by_name(body.get("board"))
            if not b:
                return self.reply(404, {"error": "unknown board"})
            rel, text = body.get("prd", ""), body.get("text", "")
            if not rel or not text:
                return self.reply(400, {"error": "prd and text required"})
            cfg, _ = synclib.load_cfg(b.path)
            if not cfg or not cfg.get("PLANE_PROJECT_ID"):
                return self.reply(409, {"error": "board not bootstrapped"})
            mp, _ = synclib.load_map(b.path)
            iid = mp["issues"].get(rel, {}).get("id")
            if not iid:
                mirror(b)  # the ticket may simply not exist yet
                mp, _ = synclib.load_map(b.path)
                iid = mp["issues"].get(rel, {}).get("id")
            if not iid:
                return self.reply(404, {"error": f"no ticket for {rel}"})
            api = synclib.Api(cfg)
            pid = cfg["PLANE_PROJECT_ID"]
            seg = api.issues_seg(pid)
            try:
                c = api.call("POST", api.proj(pid, f"{seg}/{iid}/comments/"),
                             {"comment_html": synclib.md_html(text)})
            except synclib.ApiError as e:
                return self.reply(502, {"error": str(e)})
            return self.reply(200, {"comment": c.get("id"), "issue": iid})
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
              f"(or set PLANE_SERVE_PORT)", file=sys.stderr)
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
    board = synclib.find_board(arg)  # dies with the usual message if none
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
