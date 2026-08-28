#!/usr/bin/env python3
"""pearde collect — close a finished PRD in one call: verify, commit, done.

    collect [<prd>…] [--dry] [--fail] [--trust] [--widen <path>]…
            [--also <path> --also-note <text>] [--as <id>] [--board <path>]
    collect --snapshot <prd>          what `claim` records, until it does

For each PRD named — or every PRD in `scan`'s **collect** section when none
is — the seven steps of @references/parts/loop.md step 6, in order:

  1  the finished condition off both files      `standing()` in plan.py
  2  every spec's `## Verify and Proof` block    run in `repo`, output kept
     then the board's `gate:`                    against the claim's baseline
  3  the paths: specs' footprints ∪ the PRD's ∪ the PRD dir ∪ `--also`
     — a dirty path outside it is inherited: listed, never added
     — a dirty path inside it that the claim predates: exit 1, `--widen`
     — a file holding both: only the hunks the claim does not predate
  4  one commit per repo, message per @references/parts/commits.md
  5  `commit:` `actual:` written, `claim:` cleared, `done`
  6  `POST /report` to the daemon when it is up
  7  the progress line, the transition row

A step that stops writes nothing after it. The worker's word is never taken
for the verify: `--trust` is the orchestrator's word, said on the line.

**The baseline.** "The claim predates it" is answered by what `claim`
recorded under `prds/.claims/<prd>/` — the tracked diff, the untracked
list, the gate's output — through `snapshot()` here. With no record, a
file's mtime against the claim's timestamp decides for the whole file, and
the gate has no baseline to be measured against, so it has to exit 0.

**What the tool wrote rides.** `commit:` is written after the commit it
names — it cannot be in it — so the record rides the next commit. `owe()`
lists such a path in `prds/.claims/riders`; the next collect on the board
adds it and names it on the line.

Reads through plan.py, writes through edit.py. Python 3 stdlib only.
"""
import datetime
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan as planlib  # noqa: E402 — beside this script
import edit as editlib  # noqa: E402 — beside this script
import transitions as translib  # noqa: E402 — the one printer of the line

HISTORY_FILE = translib.TRANSITIONS_FILE   # the transition log, never the daemon's burn-down
CLAIMS_DIR = ".claims"
RIDERS_FILE = "riders"
FLAGS = {"--dry", "--fail", "--trust"}
VALUED = {"--also", "--also-note", "--as", "--board", "--widen",
          "--snapshot"}
HELD = ("analyzing", "claimed", "blocked")


class Stop(Exception):
    """A step said no. The message is what the user reads; nothing after the
    step ran."""


# ── argv ──────────────────────────────────────────────────────────────────────

def parse_args(argv):
    opts = {"prds": [], "also": [], "widen": [], "also_note": "",
            "as": "engineer", "board": None, "snapshot": None}
    it = iter(argv)
    for a in it:
        if a in FLAGS:
            opts[a[2:]] = True
        elif a in VALUED:
            try:
                v = next(it)
            except StopIteration:
                raise Stop(f"{a} needs a value")
            if a in ("--also", "--widen"):
                opts[a[2:]].append(v)
            else:
                opts[a[2:].replace("-", "_")] = v
        elif a.startswith("--"):
            raise Stop(f"unknown flag {a}")
        else:
            opts["prds"].append(a.strip("/"))
    if opts["also"] and not opts["also_note"]:
        raise Stop("--also needs --also-note — the message names what the "
                   "run taught")
    return opts


# ── reads ─────────────────────────────────────────────────────────────────────

def spec_files(prd):
    sdir = os.path.join(prd["dir"], "specs")
    if not os.path.isdir(sdir):
        return []
    return [os.path.join(sdir, f) for f in sorted(os.listdir(sdir))
            if f.endswith(".md")]


def open_boxes(prd):
    """[(file, line)] — every unticked box the `done` gate would refuse:
    `prd.md` whole-file, each spec under `## Acceptance`. The verdict is
    `standing()`'s; this names what it saw."""
    out = []
    pmd = os.path.join(prd["dir"], "prd.md")
    for line in open(pmd, encoding="utf-8").read().splitlines():
        if planlib.opens_an_unticked_box(line):
            out.append((pmd, line.strip()))
    for f in spec_files(prd):
        text = open(f, encoding="utf-8").read()
        for sec in re.split(r"(?m)^##\s+", text)[1:]:
            head = sec.split("\n", 1)[0].strip().lower()
            if not head.startswith("acceptance"):
                continue
            for line in sec.splitlines()[1:]:
                if planlib.opens_an_unticked_box(line):
                    out.append((f, line.strip()))
    return out


def section(text, name):
    """The body of `## <name>` up to the next `## `, or ""."""
    m = re.search(r"(?m)^##\s+" + re.escape(name) + r"\s*$", text)
    if not m:
        return ""
    rest = text[m.end():]
    n = re.search(r"(?m)^##\s+", rest)
    return rest[:n.start()] if n else rest


def fenced(text):
    """The fenced blocks of a section, joined — the verify is the whole
    block, and a spec with two fences runs both."""
    return "\n".join(m.group(1) for m in
                     re.finditer(r"(?ms)^```[^\n]*\n(.*?)^```", text))


def verify_blocks(prd):
    """[(specNN, script)] — one per spec that carries a block."""
    out = []
    for f in spec_files(prd):
        text = open(f, encoding="utf-8").read()
        script = fenced(section(text, "Verify and Proof")).strip()
        if script:
            out.append((os.path.basename(f)[:-3], script))
    return out


def spec_goals(prd):
    """[(specNN, goal)] from each spec's `# specNN — goal` line."""
    out = []
    for f in spec_files(prd):
        _, title, _ = planlib.parse_prd(f)
        name = os.path.basename(f)[:-3]
        goal = title or name
        if " — " in goal:
            goal = goal.split(" — ", 1)[1].strip()
        out.append((name, goal))
    return out


def contract_line(prd):
    """`<prd> — <contract>`: the title's own dash, else the title whole."""
    t = prd["title"]
    if " — " in t:
        return t.split(" — ", 1)[1].strip()
    return t


def repo_of(prd, board_root):
    """Where the PRD's code lives. `repo:` that is a directory — absolute, or
    relative to the board's repo — is it; a name that is no directory, or no
    `repo:` at all, is the board's own repo."""
    raw = str(prd["fm"].get("repo", "") or "").strip()
    if raw:
        for cand in (raw, os.path.join(board_root, raw)):
            if os.path.isdir(cand):
                root = planlib.repo_root(cand)
                if root:
                    return root
    return board_root


def parse_when(s):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(s.replace("Z", ""), fmt)
        except ValueError:
            continue
    return None


def fmt_hours(h):
    s = f"{h:.2f}".rstrip("0").rstrip(".")
    return (s or "0") + "h"


# ── git ───────────────────────────────────────────────────────────────────────

def run(cmd, cwd, script=None):
    """(exit, output) — stdout and stderr in one stream, the order a reader
    saw them in."""
    try:
        r = subprocess.run(cmd, cwd=cwd, input=script, capture_output=True,
                           text=True)
    except OSError as e:
        return 127, str(e)
    return r.returncode, r.stdout + r.stderr


def git_out(root, *args, input=None):
    r = subprocess.run(("git", "-C", root) + args, capture_output=True,
                       text=True, input=input)
    if r.returncode != 0:
        raise Stop(f"git {args[0]} failed in {root}: "
                   f"{(r.stderr or r.stdout).strip()}")
    return r.stdout


def dirty_paths(root):
    """{path: "tracked" | "untracked"} for every path `git status` reports,
    relative to `root`. `-uall` so an untracked directory is its files, and
    `-z` so a space in a name is not two names."""
    raw = git_out(root, "status", "--porcelain", "-uall", "-z")
    out, items, i = {}, raw.split("\0"), 0
    while i < len(items):
        ent = items[i]
        i += 1
        if not ent:
            continue
        xy, path = ent[:2], ent[3:]
        out[path] = "untracked" if xy == "??" else "tracked"
        if xy[0] in "RC":          # the original follows as its own entry
            i += 1
    return out


def inside(path, union):
    return any(path == u or path.startswith(u + "/") for u in union)


def scratch(path, board_rel):
    """A dotfile directly under the board — `.claims/`, `.round.md`,
    `.history.jsonl`, `.plan.json` — is machine-local and never committed."""
    rest = path[len(board_rel) + 1:] if inside(path, [board_rel]) else ""
    return rest.startswith(".")


def split_hunks(diff):
    """{path: (header, [hunk])} from `git diff` output. A hunk is its text
    from `@@` to the next `@@` or file header."""
    files = {}
    for block in re.split(r"(?m)^(?=diff --git )", diff):
        if not block.strip():
            continue
        m = re.search(r"(?m)^\+\+\+ b/(.*)$", block)
        if not m:
            continue
        head, _, rest = block.partition("\n@@")
        hunks = [h for h in re.split(r"(?m)^(?=@@ )", "@@" + rest)
                 if h.strip()] if rest else []
        files[m.group(1)] = (head + "\n", hunks)
    return files


def hunk_body(h):
    """A hunk without its `@@` header — the header's line numbers move when
    another hunk lands above it, the body does not."""
    return h.split("\n", 1)[1] if "\n" in h else ""


# ── the baseline ──────────────────────────────────────────────────────────────

def claims_dir(board, rel):
    return os.path.join(board, CLAIMS_DIR, rel)


def snapshot(board, rel, gate=None):
    """Record what is dirty and what the gate says at `claim:` — the
    baseline step 3 and the gate are measured against. Called by `claim`;
    `collect --snapshot <prd>` is the same call by hand."""
    prds = planlib.scan(board)
    prd = prds.get(rel)
    if not prd:
        raise Stop(f"{rel}: no PRD at that path")
    root = planlib.repo_root(prd["dir"])
    if not root:
        raise Stop(f"{rel}: not inside a git repo")
    d = claims_dir(board, rel)
    os.makedirs(d, exist_ok=True)
    dirty = dirty_paths(root)
    with open(os.path.join(d, "diff"), "w", encoding="utf-8") as f:
        f.write(git_out(root, "diff", "HEAD", "-U0", "--no-color"))
    with open(os.path.join(d, "untracked"), "w", encoding="utf-8") as f:
        f.write("".join(p + "\n" for p, k in sorted(dirty.items())
                        if k == "untracked"))
    gate = (str(planlib.board_settings(board).get("gate", "") or "").strip()
            if gate is None else gate)
    code, output = (run(["bash", "-e", "-o", "pipefail"], root, gate)
                    if gate else (0, ""))
    with open(os.path.join(d, "gate"), "w", encoding="utf-8") as f:
        f.write(f"exit {code}\n{output}")
    with open(os.path.join(d, "at"), "w", encoding="utf-8") as f:
        f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
    return d


def baseline(board, rel):
    """What `snapshot` recorded, or None."""
    d = claims_dir(board, rel)
    if not os.path.isfile(os.path.join(d, "diff")):
        return None
    rd = lambda n: open(os.path.join(d, n), encoding="utf-8").read()  # noqa
    gate = rd("gate") if os.path.isfile(os.path.join(d, "gate")) else ""
    m = re.match(r"exit (\d+)\n", gate)
    return {"hunks": {p: {hunk_body(h) for h in hs}
                      for p, (_, hs) in split_hunks(rd("diff")).items()},
            "untracked": set(rd("untracked").split()),
            "gate_exit": int(m.group(1)) if m else 0,
            "gate_lines": set(gate.splitlines()[1:]) if m else set()}


def owe(board, path):
    """List a board-repo path the tool wrote after the commit it belongs to
    — it rides the next collect."""
    p = os.path.join(board, CLAIMS_DIR, RIDERS_FILE)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    have = set(open(p, encoding="utf-8").read().split()) \
        if os.path.isfile(p) else set()
    if path not in have:
        with open(p, "a", encoding="utf-8") as f:
            f.write(path + "\n")


def owed(board):
    p = os.path.join(board, CLAIMS_DIR, RIDERS_FILE)
    return set(open(p, encoding="utf-8").read().split()) \
        if os.path.isfile(p) else set()


def settle(board, paths):
    p = os.path.join(board, CLAIMS_DIR, RIDERS_FILE)
    keep = owed(board) - set(paths)
    if os.path.isfile(p):
        with open(p, "w", encoding="utf-8") as f:
            f.write("".join(x + "\n" for x in sorted(keep)))


# ── daemon ────────────────────────────────────────────────────────────────────

def daemon_call(path, payload=None, timeout=3):
    port = os.environ.get("PEARDE_PORT", "8443")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json"},
        method="POST" if payload is not None else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        return json.loads(raw) if raw else {}


def post_report(board, rel, text):
    """What happened, in words. Down, or the board not registered, is said
    and not an error — the verify output is in the PRD's own files too."""
    try:
        st = daemon_call("/status")
    except (urllib.error.URLError, OSError, ValueError):
        return "daemon down — report not posted"
    name = next((b["name"] for b in st.get("boards", [])
                 if os.path.abspath(b["path"]) == os.path.abspath(board)),
                None)
    if not name:
        return "board not registered with the daemon — report not posted"
    try:
        daemon_call("/report", {"board": name, "prd": rel, "text": text})
    except (urllib.error.URLError, OSError, ValueError) as e:
        return f"POST /report failed — {e}"
    return "report posted"


# ── the line ──────────────────────────────────────────────────────────────────

def progress_line(board, rel, frm, to, persona, extra=""):
    """@references/parts/progress.md — every term is transitions.py's, the one
    printer of the line. What collect has to say goes after `@<w> workers`
    and before `as <persona>`, which stays last."""
    line = translib.progress_line(board, rel, frm, to, persona)
    if not extra:
        return line
    head, _, tail = line.rpartition(" · as ")
    return f"{head} · {extra} · as {tail}"


def history_row(board, rel, frm, to, now):
    row = {"t": now.strftime("%Y-%m-%d %H:%M"), "prd": rel, "from": frm,
           "to": to}
    with open(os.path.join(board, HISTORY_FILE), "a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")


# ── step 3 ────────────────────────────────────────────────────────────────────

def sort_paths(board, rel, prd, prds, board_root, repo, feet, opts, since):
    """{root: plan} — for each repo, what to add whole, what to add by hunk,
    what is inherited, what is inherited inside the footprint (the stop),
    what rides, what was widened."""
    prd_rel = os.path.relpath(prd["dir"], board_root)
    groups = {board_root: {prd_rel}}
    # `spec_data` qualifies a member PRD's footprint with its own member
    # sigil so two members' `src/lib.rs` never compare equal. Here the
    # paths are about to be added in that member's own repo, so its own
    # sigil comes off again; a path carrying ANOTHER member's sigil is a
    # cross-repo footprint and is left out, as before.
    own = (f"{planlib.MEMBER_SIGIL}{prd['board']}/"
           if prd.get("board") else None)
    for f in feet:
        if own and f.startswith(own):
            groups.setdefault(repo, set()).add(f[len(own):])
        elif not f.startswith(planlib.MEMBER_SIGIL):
            groups.setdefault(repo, set()).add(f)
    for a in opts["also"]:
        ap = os.path.abspath(a)
        root = planlib.repo_root(ap)
        if not root:
            raise Stop(f"--also {a}: not inside a git repo")
        groups.setdefault(root, set()).add(os.path.relpath(ap, root))
    widen = set()
    for w in opts["widen"]:
        wp = os.path.abspath(w) if os.path.isabs(w) else \
            os.path.abspath(os.path.join(board_root, w))
        widen.add(wp)
    base = baseline(board, rel)
    riders = owed(board)
    board_rel = os.path.relpath(board, board_root)
    held = [os.path.relpath(p["dir"], board_root) for r, p in prds.items()
            if r != rel and p["state"] in HELD]

    def predates(root, p, kind):
        """The whole of this path's dirt is older than the claim."""
        if base is not None:
            return (p in base["untracked"] if kind == "untracked"
                    else p in base["hunks"] and not new_hunks(root, p))
        if since is None:
            return False
        try:
            return datetime.datetime.fromtimestamp(
                os.path.getmtime(os.path.join(root, p))) < since
        except OSError:
            return False

    def new_hunks(root, p):
        """The hunks of `p` the baseline does not hold, as one patch, or ""
        when every hunk is inherited. None when there is no baseline — the
        file goes whole or not at all. Zero context on both sides, so two
        edits near each other are two hunks and not one merged one."""
        if base is None:
            return None
        cur = split_hunks(git_out(root, "diff", "HEAD", "-U0", "--no-color",
                                  "--", p)).get(p)
        if not cur:
            return ""
        head, hunks = cur
        old = base["hunks"].get(p, set())
        keep = [h for h in hunks if hunk_body(h) not in old]
        return head + "".join(keep) if keep and len(keep) < len(hunks) \
            else ("all" if keep else "")

    plan = {}
    for root, union in groups.items():
        union = sorted(u.rstrip("/") for u in union if u and u != ".")
        p = {"union": union, "add": [], "partial": {}, "inherited": [],
             "stop": [], "riders": [], "widened": []}
        for path, kind in sorted(dirty_paths(root).items()):
            full = os.path.join(root, path)
            if root == board_root and scratch(path, board_rel):
                continue           # the board's own dotfiles — never anyone's
            if full in widen:
                p["add"].append(path)
                p["widened"].append(path)
            elif inside(path, union):
                nh = new_hunks(root, path) if kind == "tracked" else None
                if nh not in (None, "", "all"):
                    p["partial"][path] = nh
                elif predates(root, path, kind):
                    p["stop"].append(path)
                else:
                    p["add"].append(path)
            elif root == board_root and path in riders:
                p["add"].append(path)
                p["riders"].append(path)
            elif (root == board_root and base is not None
                  and inside(path, [board_rel]) and not inside(path, held)
                  and not predates(root, path, kind)):
                p["add"].append(path)
                p["riders"].append(path)
            else:
                p["inherited"].append(path)
        plan[root] = p
    return plan, prd_rel


# ── one PRD ───────────────────────────────────────────────────────────────────

def collect_one(board, rel, opts, out=print):
    now = datetime.datetime.now()
    prds = planlib.scan(board)
    prd = prds.get(rel)
    if not prd:
        raise Stop(f"{rel}: no PRD at that path")
    board_root = planlib.repo_root(prd["dir"])
    if not board_root:
        raise Stop(f"{rel}: {prd['dir']} is not inside a git repo")
    pmd = os.path.join(prd["dir"], "prd.md")
    cl = planlib.claim_of(prd["fm"])
    since = parse_when(cl["since"]) if cl and cl["since"] else None

    # 1 — finished, off both files
    _, closed, total, ready = planlib.standing(prd)
    if not ready:
        if prd["state"] not in planlib.HOLDING_STATES:
            raise Stop(f"{rel}: state is `{prd['state']}` — collect closes "
                       f"`claimed` or `blocked`")
        boxes = open_boxes(prd)
        if boxes:
            f, line = boxes[0]
            raise Stop(f"{rel}: open box in {os.path.relpath(f, board_root)}"
                       f": `{line}`" + (f" (+{len(boxes) - 1} more)"
                                       if len(boxes) > 1 else ""))
        raise Stop(f"{rel}: no acceptance box in specs/ — nothing says it "
                   f"is finished ({closed}/{total})")

    # 2 — the verify, then the gate — never the worker's word
    repo = repo_of(prd, board_root)
    base = baseline(board, rel)
    report, trusted, known = [], False, False
    if opts.get("trust"):
        trusted = True
    else:
        checks = [(spec, script, repo) for spec, script in verify_blocks(prd)]
        gate = str(planlib.board_settings(board).get("gate", "") or "").strip()
        if gate:
            checks.append(("gate", gate, board_root))
        for name, script, cwd in checks:
            code, output = run(["bash", "-e", "-o", "pipefail"], cwd, script)
            red = code != 0
            if red and name == "gate" and base is not None:
                # measured against the claim's baseline, not against silence
                new = [l for l in output.splitlines()
                       if l.strip() and l not in base["gate_lines"]]
                red = bool(new)
                if not red:
                    known = True
                    output += "\n(known — every line is in the claim's " \
                              "baseline)"
            report.append(f"{name}: exit {code}\n{output.rstrip()}")
            if red:
                text = "\n\n".join(report)
                out(text)
                if opts.get("fail") and not opts.get("dry"):
                    editlib.append_section(pmd, "Failure", text)
                    editlib.del_key(pmd, "claim")
                    editlib.set_key(pmd, "state", "failed")
                    history_row(board, rel, prd["state"], "failed", now)
                    out(progress_line(board, rel, prd["state"], "failed",
                                      opts["as"], "round file owed"))
                    return 1
                raise Stop(f"{rel}: {name} exit {code} — nothing written")

    # 3 — the paths
    _, feet = planlib.spec_data(prd)
    plan, prd_rel = sort_paths(board, rel, prd, prds, board_root, repo, feet,
                               opts, since)
    stops, inherited = [], []
    for root, p in plan.items():
        stops += [os.path.relpath(os.path.join(root, x), board_root)
                  for x in p["stop"]]
        inherited += [os.path.relpath(os.path.join(root, x), board_root)
                      for x in p["inherited"]]
    if inherited:
        out(f"{rel}: inherited, not added — {len(inherited)} path(s):")
        for x in inherited:
            out(f"  {x}")
    if stops:
        out(f"{rel}: inside the footprint and older than the claim — "
            f"`--widen <path>` takes it:")
        for x in stops:
            out(f"  {x}")
        raise Stop(f"{rel}: {len(stops)} path(s) in the footprint that the "
                   f"claim predates")

    # 4 — the message, one commit per repo
    slug = str(prd["fm"].get("workflow", "") or "").strip()
    lines = [f"{prd['name']} — {contract_line(prd)}", ""]
    lines += [f"{n}: {g}" for n, g in spec_goals(prd)]
    if opts["also"]:
        lines.append(f"workflow: {slug or 'none'} — {opts['also_note']}")
    for p in plan.values():
        lines += [f"widen: {x}" for x in p["widened"]]
    lines += ["", f"prd: {prd_rel}"]
    message = "\n".join(lines) + "\n"
    if opts.get("dry"):
        for root, p in plan.items():
            out(f"{rel}: repo {root}")
            out("  footprint: " + (", ".join(p["union"]) or "(none)"))
            out("  would add: " + (", ".join(p["add"]) or
                                   ("(clean — commit: none)"
                                    if not p["partial"] else "")))
            for x in p["partial"]:
                out(f"  by hunk:   {x}")
            if p["riders"]:
                out("  rides:     " + ", ".join(p["riders"]))
            if p["widened"]:
                out("  widened:   " + ", ".join(p["widened"]))
        out("  message:\n    " + message.rstrip().replace("\n", "\n    "))
        out(f"{rel}: dry — nothing written")
        return 0
    shas, said = [], []
    for root, p in plan.items():
        if not p["add"] and not p["partial"]:
            continue
        if p["add"]:
            git_out(root, "add", "--", *p["add"])
        for patch in p["partial"].values():
            # the hunks' old side is HEAD, which is what the index holds
            git_out(root, "apply", "--cached", "--unidiff-zero", "-",
                    input=patch)
        r = subprocess.run(["git", "-C", root, "commit", "-q", "-F", "-"],
                           input=message, capture_output=True, text=True)
        if r.returncode != 0:
            raise Stop(f"{rel}: git commit failed in {root}: "
                       f"{(r.stderr or r.stdout).strip()}")
        shas.append(git_out(root, "rev-parse", "--short", "HEAD").strip())
        if p["partial"]:
            said.append("by hunk " + ", ".join(p["partial"]))
        if p["riders"]:
            said.append("rides " + ", ".join(p["riders"]))
        if p["widened"]:
            said.append("widened " + ", ".join(p["widened"]))
    if inherited:
        said.append(f"inherited {len(inherited)}")
    settle(board, [x for p in plan.values() for x in p["riders"]])

    # 5 — the record — written after the commit it names, so it rides
    hrs = (now - since).total_seconds() / 3600.0 if since else None
    editlib.set_key(pmd, "commit", " ".join(shas) if shas else "none")
    if hrs is not None:
        editlib.set_key(pmd, "actual", fmt_hours(max(hrs, 0.0)))
    editlib.del_key(pmd, "claim")
    editlib.set_key(pmd, "state", "done")
    owe(board, os.path.relpath(pmd, board_root))

    # 6 — the report to the daemon
    text = ("trusted — the verify was not run by collect" if trusted
            else "\n\n".join(report) or "no `## Verify and Proof` block")
    posted = post_report(board, rel, text)

    # 7 — the line, the row
    history_row(board, rel, prd["state"], "done", now)
    extra = " · ".join(x for x in [
        "trusted" if trusted else "", "gate red, known" if known else "",
        f"commit {' '.join(shas)}" if shas else "commit none",
        *said, posted, "round file owed"] if x)
    out(progress_line(board, rel, prd["state"], "done", opts["as"], extra))
    return 0


def cmd_collect(argv, board=None):
    """The entry: `collect [<prd>…] [flags]`. Exit 0 when every PRD named
    was collected, 1 when any stopped, 2 on usage."""
    try:
        opts = parse_args(argv)
    except Stop as e:
        print(f"collect: {e}", file=sys.stderr)
        return 2
    board = planlib.find_board(opts["board"] or board)
    if opts["snapshot"]:
        try:
            print(f"snapshot: {snapshot(board, opts['snapshot'].strip('/'))}")
        except Stop as e:
            print(f"collect: {e}", file=sys.stderr)
            return 1
        return 0
    rels = opts["prds"]
    if not rels:
        r = planlib.compute_plan(board, None, warn=False)
        rels = list(r["collect"]) if r else []
        if not rels:
            print("collect: nothing finished — the scan's collect section is "
                  "empty")
            return 0
    worst = 0
    for rel in rels:
        try:
            worst = max(worst, collect_one(board, rel, opts))
        except Stop as e:
            print(f"collect: {e}", file=sys.stderr)
            worst = max(worst, 1)
    return worst


COMMANDS = {"collect": cmd_collect}


def main():
    sys.exit(cmd_collect(sys.argv[1:]))


if __name__ == "__main__":
    main()
