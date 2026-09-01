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
     — the PRD's own folder is the board's record: added whole, always —
       never by hunk, never a stop
     — a dirty path outside it is inherited: listed, never added
     — a dirty path inside it that the claim predates: exit 1, `--widen`
     — a file holding both: only the hunks the claim does not predate,
       staged as the working file with the inherited hunks reversed,
       and the staged blob checked for parse and placement before 4
     — a hunk that is in neither the baseline nor the worker's diff —
       two edits on adjacent lines, merged by `-U0` — is refused:
       `two authors on one hunk: <file>:<line>`; `--widen` takes the
       file whole, or the worker leaves one untouched line between
  4  the record — `actual:` written, `claim:` cleared, `done`, the report
     posted — then one commit per repo, message per
     @references/parts/commits.md; everything collect wrote is in it
  5  `commit:` — the one key that cannot be in the commit it names — in a
     second, one-key commit `<prd> — record`, right behind
  6  `POST /report` to the daemon when it is up — before the commit, so
     `## Report` is in it
  7  the progress line, the transition row

A container — a parent whose every child is `done`, with no spec and no
open box of its own — has nothing to verify and nothing to commit but its
record. `dispatchable()` in plan.py is the one word for it (`container:
every child done — pearde collect closes it` — what `claim` refuses on and
`scan` lists under collect with), and `close_container()` here sets `done`,
`actual:` the sum of the children's, `commit:` the last child's, in one
commit `<parent> — done: every child landed`. A parent with specs or an
open box of its own is ordinary work, and its boxes decide it.

A step that stops writes nothing after it. The worker's word is never taken
for the verify: `--trust` is the orchestrator's word, said on the line.

**The baseline.** "The claim predates it" is answered by what `claim`
recorded under `.pearde/.claims/<prd>/` — the tracked diff, the untracked
list, the gate's output — through `snapshot()` here. With no record, a
file's mtime against the claim's timestamp decides for the whole file, and
the gate has no baseline to be measured against, so it has to exit 0.

**Board state written between transitions rides.** `answer` writes a
`prd.md` no collect is about to commit; `owe()` lists that path in
`.pearde/.claims/riders` and the next collect on the board adds it and names
it on the line. What collect itself writes never rides — it is in the
commit it makes.

Reads through plan.py, writes through edit.py. Python 3 stdlib only.
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan as planlib  # noqa: E402 — beside this script
import edit as editlib  # noqa: E402 — beside this script
import transitions as translib  # noqa: E402 — the one printer of the line

# collect writes done/failed transitions straight to the same log
# transitions.py record() appends to — never to .history.jsonl, the
# daemon's one-row-a-day burn-down.
TRANSITION_FILE = translib.TRANSITIONS_FILE
CLAIMS_DIR = ".claims"
RIDERS_FILE = "riders"
# The declaration — transitions.py `Args` is the parser, shared with every
# command pearde.py discovers; an undeclared flag is refused with this list,
# exit 2, before the board is read.
FLAGS = translib.Flags(("as", "board", "also", "also-note", "widen",
                        "snapshot"), ("dry", "fail", "trust"),
                       multi=("also", "widen"))
HELD = ("analyzing", "claimed", "blocked")


class Stop(Exception):
    """A step said no. The message is what the user reads; nothing after the
    step ran."""


# ── argv ──────────────────────────────────────────────────────────────────────

def parse_args(argv):
    a = translib.Args(argv, FLAGS, "collect")     # FlagRefused → exit 2
    # the persona the way every transition resolves it — `--as`, else
    # PEARDE_AS, else the one refusal transitions.py raises: collect's line
    # is the record of who acted, and a default would write it unasked
    persona = (a.opt.get("as") or os.environ.get("PEARDE_AS", "")).strip()
    opts = {"prds": [x.strip("/") for x in a.pos],
            "also": a.opt.get("also", []), "widen": a.opt.get("widen", []),
            "also_note": a.opt.get("also-note", ""),
            "as": persona or translib.persona_default("collect"),
            "board": a.opt.get("board"), "snapshot": a.opt.get("snapshot")}
    for k in ("dry", "fail", "trust"):
        if k in a.flags:
            opts[k] = True
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


def repo_of(prd, board, board_root):
    """Where the PRD's code lives. `repo:` that is a directory — absolute, or
    relative to the board's repo — is it. With no `repo:`: when the board is
    its own git repo (`board_root == board` — a nested `.pearde` with a
    `.git` of its own), the repo enclosing it, `repo_root` of the board's
    own parent — a nested board defaults to the code repo it sits in, never
    to itself. When the board is not its own repo — `board_root` was found
    walking up *past* the board, so it already is the code repo — unchanged,
    the board's own repo, exactly as before this default existed."""
    raw = str(prd["fm"].get("repo", "") or "").strip()
    if raw:
        for cand in (raw, os.path.join(board_root, raw)):
            if os.path.isdir(cand):
                root = planlib.repo_root(cand)
                if root:
                    return root
    if board_root == board:
        enclosing = planlib.repo_root(os.path.dirname(board_root))
        if enclosing:
            return enclosing
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

def _bash():
    """A bare "bash" on Windows can resolve to the WSL launcher stub under
    WindowsApps — a reparse-point shim that always re-execs into a WSL
    distro regardless of PATH order — and that stub fails with
    `execvpe(/bin/bash) failed` outside any installed distro. Prefer a real
    Git for Windows bash when one is findable; unchanged everywhere else."""
    if os.name != "nt":
        return "bash"
    override = os.environ.get("PEARDE_BASH")
    if override and os.path.isfile(override):
        return override
    clean_path = os.pathsep.join(
        p for p in os.environ.get("PATH", "").split(os.pathsep)
        if "WindowsApps" not in p)
    found = shutil.which("bash", path=clean_path)
    if found:
        return found
    for candidate in (r"C:\Program Files\Git\bin\bash.exe",
                       r"C:\Program Files\Git\usr\bin\bash.exe"):
        if os.path.isfile(candidate):
            return candidate
    return "bash"


def run(cmd, cwd, script=None):
    """(exit, output) — stdout and stderr in one stream, the order a reader
    saw them in."""
    if cmd and cmd[0] == "bash":
        cmd = [_bash(), *cmd[1:]]
    try:
        r = subprocess.run(cmd, cwd=cwd, input=script, capture_output=True,
                           text=True)
    except OSError as e:
        return 127, str(e)
    return r.returncode, r.stdout + r.stderr


# ── the private index ─────────────────────────────────────────────────────────
# The checkout's index is shared by every session in it, and `git commit`
# commits the whole index — so a landing carried whatever a sibling had
# staged. collect builds its commits in an index of its own: `read-tree HEAD`
# into a scratch file, its own `add` / `update-index` there, `write-tree`,
# `commit-tree`, and `update-ref <ref> <new> <expected-old>` — refused when a
# sibling moved HEAD in between. The one write to the shared index is
# path-scoped, after the ref moved: `reset -q -- <the paths committed>`, so
# their entries read HEAD's blob — left stale, a sibling's next plain
# `git commit` would carry the old blob and revert the landing.
INDEX = {}                      # root → the scratch index while one is open
BASE = {}                       # root → the HEAD that index was read from


def git_out(root, *args, input=None, shared=False):
    env = None
    if root in INDEX and not shared:
        env = dict(os.environ, GIT_INDEX_FILE=INDEX[root])
    # Windows' text=True decodes with the system locale's codepage (cp1252
    # here), not UTF-8 — a diff touching any of this board's German text
    # (umlauts throughout prd.md/spec files) makes the subprocess reader
    # thread's decode fail silently, leaving r.stdout None while returncode
    # stays 0 (git itself succeeded). git's own output is UTF-8 regardless
    # of platform, so decode it as that explicitly.
    r = subprocess.run(("git", "-C", root) + args, capture_output=True,
                       text=True, encoding="utf-8", input=input, env=env)
    if r.returncode != 0:
        raise Stop(f"git {args[0]} failed in {root}: "
                   f"{(r.stderr or r.stdout).strip()}")
    return r.stdout


class private_index:
    """`with private_index(roots):` — every `git_out` on those roots reads
    and writes a scratch index seeded from HEAD, dropped on exit."""

    def __init__(self, roots):
        self.roots, self.dir = list(roots), None

    def __enter__(self):
        self.dir = tempfile.mkdtemp(prefix="pearde-index-")
        for i, root in enumerate(self.roots):
            INDEX[root] = os.path.join(self.dir, f"index-{i}")
            BASE[root] = git_out(root, "rev-parse", "HEAD").strip()
            git_out(root, "read-tree", BASE[root])
        return self

    def __exit__(self, *exc):
        for root in self.roots:
            INDEX.pop(root, None)
            BASE.pop(root, None)
        shutil.rmtree(self.dir, ignore_errors=True)
        return False


def commit_private(root, message):
    """The private index as one commit on the current branch: write-tree,
    commit-tree on the HEAD the index was read from, update-ref expecting
    that same HEAD — one a sibling moved meanwhile is a Stop, nothing
    written, since the tree was built without their commit. Returns the
    short sha; the next commit in the same index follows this one."""
    old = BASE[root]
    tree = git_out(root, "write-tree").strip()
    new = git_out(root, "commit-tree", tree, "-p", old, input=message).strip()
    r = subprocess.run(["git", "-C", root, "symbolic-ref", "-q", "HEAD"],
                       capture_output=True, text=True)
    ref = r.stdout.strip() if r.returncode == 0 else "HEAD"
    r = subprocess.run(["git", "-C", root, "update-ref", ref, new, old],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise Stop(f"HEAD moved under collect in {root} — another session "
                   f"committed; nothing written, run collect again: "
                   f"{(r.stderr or r.stdout).strip()}")
    BASE[root] = new
    return new[:7]


def settle_shared(root, paths):
    """After the ref moved: the shared index's entries for the paths just
    committed now read HEAD's blob — the one path-scoped write to it."""
    if paths:
        git_out(root, "reset", "-q", "--", *paths, shared=True)


def dirty_paths(root):
    """{path: "tracked" | "untracked" | "rename-source"} for every path
    `git status` reports, relative to `root`. `-uall` so an untracked
    directory is its files, and `-z` so a space in a name is not two names.
    A rename or a copy reports two paths — the new one under its own XY,
    the original under `rename-source` — so a caller staging one side by
    side the other does not lose the deletion a rename's old path carries."""
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
            out[items[i]] = "rename-source"
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


def hunk_sides(body):
    """`([minus], [plus])` — a hunk body's two sides, marker stripped, the
    `\\ No newline` note dropped. Lists, in order: a merged hunk holds one
    author's lines and then the other's."""
    minus, plus = [], []
    for line in body.split("\n"):
        if line.startswith("-"):
            minus.append(line[1:])
        elif line.startswith("+"):
            plus.append(line[1:])
    return minus, plus


def sublist(part, whole):
    """True when `part` is a contiguous run of `whole`, `part` non-empty."""
    n = len(part)
    return bool(part) and any(whole[i:i + n] == part
                              for i in range(len(whole) - n + 1))


def two_authors(kept, old_bodies):
    """The working line of the first kept hunk that swallowed a baseline
    hunk, or None. `git diff -U0` merges two edits on adjacent lines into
    one hunk; when one of them was in the claim's baseline, that baseline
    hunk is gone from the diff and its lines sit inside a kept hunk — a
    body that matches neither the baseline nor the worker's own edit, so
    nothing here can say which lines are whose. Line-level splitting is
    not attempted: the file is refused, and `--widen` or one untouched
    line between the edits is the worker's answer."""
    gone = [hunk_sides(b) for b in old_bodies]
    for h in kept:
        minus, plus = hunk_sides(hunk_body(h))
        for om, op in gone:
            if (op and not sublist(op, plus)) or (om and not sublist(om, minus)):
                continue
            if not (op or om):
                continue
            m = HUNK_HEAD.match(h)
            return int(m.group(3)) if m else 0
    return None


HUNK_HEAD = re.compile(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
PARSERS = {".py": ["python3", "-m", "py_compile"],
           ".js": ["node", "--check"], ".mjs": ["node", "--check"],
           ".cjs": ["node", "--check"]}


def parse_hunk(h):
    """{"old": (start, len), "new": (start, len), "minus": [line], "plus":
    [line]} from one `-U0` hunk. Every line keeps its newline except one the
    file has none on (`\\ No newline at end of file`). A context line, should
    one appear, is on both sides."""
    head, _, body = h.partition("\n")
    m = HUNK_HEAD.match(head)
    if not m:
        raise Stop(f"unreadable hunk header: {head!r}")
    old = (int(m.group(1)), 1 if m.group(2) is None else int(m.group(2)))
    new = (int(m.group(3)), 1 if m.group(4) is None else int(m.group(4)))
    minus, plus, last = [], [], []
    for line in body.split("\n"):
        if not line:
            continue
        kind, text = line[0], line[1:] + "\n"
        if kind == "\\":
            for side in last:
                side[-1] = side[-1][:-1]
            continue
        last = {"-": [minus], "+": [plus], " ": [minus, plus]}.get(kind)
        if last is None:
            raise Stop(f"unreadable hunk line: {line!r}")
        for side in last:
            side.append(text)
    if len(minus) != old[1] or len(plus) != new[1]:
        raise Stop(f"hunk {head!r} says {old[1]}/{new[1]} lines and "
                   f"carries {len(minus)}/{len(plus)}")
    return {"old": old, "new": new, "minus": minus, "plus": plus}


def reverse_hunks(text, hunks):
    """`text` — the working file — with every hunk in `hunks` undone, from
    the bottom up so the line numbers above each stay true. The hunks' new
    side is `text`'s own coordinates: a `+N,0` hunk puts its `-` lines back
    after line N; any other hunk holds `text`'s lines N..N+len-1 as its `+`
    lines, checked before they are replaced by its `-` lines. Nothing here
    re-derives a position from a patch's old side."""
    lines = text.splitlines(keepends=True)
    parsed = sorted((parse_hunk(h) for h in hunks),
                    key=lambda p: p["new"][0], reverse=True)
    for a, b in zip(parsed, parsed[1:]):
        if a["new"][0] == b["new"][0]:
            raise Stop(f"two hunks start at line {a['new'][0]} of the "
                       f"working file — the diff is not one this reader "
                       f"understands")
    for p in parsed:
        start, n = p["new"]
        at = start if n == 0 else start - 1
        have = lines[at:at + n]
        if have != p["plus"]:
            raise Stop(f"line {start} of the working file is not what its "
                       f"hunk says: {have!r} against {p['plus']!r}")
        lines[at:at + n] = p["minus"]
    return "".join(lines)


def misplaced(staged, kept, foreign, working_len):
    """Where the staged blob disagrees with the working file: one line per
    kept hunk whose `+` lines are not at the working position minus the
    lines the foreign hunks above it hold, and one when the blob's length
    is not the working file's minus the foreign hunks'. [] is placement
    proven; an exit code of `git apply` never is."""
    lines = staged.splitlines(keepends=True)
    fs = [parse_hunk(h) for h in foreign]
    out = []
    want = working_len - sum(f["new"][1] - f["old"][1] for f in fs)
    if len(lines) != want:
        out.append(f"the staged blob holds {len(lines)} lines, the working "
                   f"file minus the inherited hunks holds {want}")
    for k in (parse_hunk(h) for h in kept):
        start, n = k["new"]
        shift = sum(f["new"][1] - f["old"][1] for f in fs
                    if f["new"][0] < start)
        at = start - shift
        if n == 0:
            if lines[at:at + k["old"][1]] == k["minus"]:
                out.append(f"hunk @@ +{start},0: its removed lines still "
                           f"sit after line {at} of the staged blob")
            continue
        have = lines[at - 1:at - 1 + n]
        if have != k["plus"]:
            where = [i + 1 for i in range(len(lines))
                     if lines[i:i + n] == k["plus"]]
            out.append(f"hunk @@ +{start},{n}: expected at line {at} of "
                       f"the staged blob, found at "
                       f"{', '.join(map(str, where)) or 'no line'}")
    return out


def parse_error(path, text):
    """What the parser for `path`'s suffix says of `text`, "" when it
    parses or no parser is on this machine."""
    cmd = PARSERS.get(os.path.splitext(path)[1])
    if not cmd or not shutil.which(cmd[0]):
        return ""                  # no parser here — nothing to say
    d = os.path.realpath(tempfile.mkdtemp())   # a parser prints the real path
    try:
        tmp = os.path.join(d, os.path.basename(path))
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
        code, output = run(cmd + [tmp], d)
        return output.replace(tmp, path).strip() if code else ""
    finally:
        shutil.rmtree(d, ignore_errors=True)


def stage_by_hunk(root, path, foreign):
    """Stage `path` as the working file with the inherited hunks reversed:
    hash the rebuilt text, point the index at it. Returns the text staged."""
    with open(os.path.join(root, path), encoding="utf-8") as f:
        work = f.read()
    blob = reverse_hunks(work, foreign)
    sha = git_out(root, "hash-object", "-w", "--stdin", "--path", path,
                  input=blob).strip()
    entry = git_out(root, "ls-files", "-s", "--", path).split()
    mode = entry[0] if entry else "100644"
    git_out(root, "update-index", "--cacheinfo", f"{mode},{sha},{path}")
    return work, blob


def placement_refusals(root, partial, staged):
    """Every reason not to commit what step 3 staged by hunk: a blob that
    does not parse, or a kept hunk not at its place. `staged` is
    {path: (working text, staged text)}."""
    out = []
    for path, (kept, foreign) in partial.items():
        work, _ = staged[path]
        blob = git_out(root, "show", f":{path}")
        err = parse_error(path, blob)
        if err:
            out.append(f"{path}: the staged blob does not parse — {err}")
        for m in misplaced(blob, kept, foreign,
                           len(work.splitlines(keepends=True))):
            out.append(f"{path}: {m}")
    return out


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


def dry_line(board, prds, rel, prd, persona, paths, out=print):
    """The `dry ·` line every writer prints — the progress line the real
    run would print, on the scan with this PRD moved to `done`. The commit
    shas the real line carries do not exist yet, so `commit` and `record`
    are not on it; `round file owed` is."""
    frm = prd["state"]
    prd["state"] = prd["fm"]["state"] = "done"
    prd["fm"].pop("claim", None)
    line = translib.dry_line(board, prds, rel, frm, "done", persona)
    head, _, tail = line.rpartition(" · as ")
    translib.say_dry(board, f"{head} · round file owed · as {tail}",
                     paths + [os.path.join(prd["board_path"], TRANSITION_FILE)],
                     out)


def transition_row(board, rel, frm, to, now):
    """A `{t,prd,from,to}` row appended to `.transitions.jsonl` — the same
    shape and file transitions.py record() writes for every CLI-driven
    move; this is the one collect makes on its own for done/failed."""
    row = {"t": now.strftime("%Y-%m-%d %H:%M"), "prd": rel, "from": frm,
           "to": to}
    with open(os.path.join(board, TRANSITION_FILE), "a", encoding="utf-8") as f:
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
            p = f[len(own):]
        elif not f.startswith(planlib.MEMBER_SIGIL):
            p = f
        else:
            continue
        # a footprint path `repo_of` filed under a repo that does not hold
        # it at all is the exact silent drop this replaces: `collect` must
        # not write `done` over code it never found — refused loudly here,
        # before any group's `dirty_paths` loop ever runs. "Holds it" means
        # on disk (an untracked new file) or in the index (`git ls-files` —
        # still true of a path deleted from the working tree but not yet
        # staged, so a spec whose finish is a deletion still passes); a path
        # that DOES exist but is merely clean is not this — it goes to
        # plan.add=[] further down, no bug, nothing to say.
        full = os.path.join(repo, p)
        tracked = git_out(repo, "ls-files", "-z", "--", p).strip("\0")
        if not os.path.exists(full) and not tracked:
            raise Stop(f"{rel}: footprint {p} is not under {repo} — "
                       f"repo_of matched no repo for it; nothing written")
        groups.setdefault(repo, set()).add(p)
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
    # What another held PRD's footprint already claims, relative to the repo
    # the footprints are written against — only siblings whose code lives in
    # this run's `repo` can share a dirty path with it. A dirty path the
    # union holds and a sibling's footprint holds too may carry the
    # sibling's edits: a commit here is this PRD's record, and hunks the
    # claim's baseline does not explain are attributable to no one, so the
    # file is refused — `--widen` takes it whole.
    others = {}
    for r, p in prds.items():
        if r == rel or p["state"] not in HELD:
            continue
        if repo_of(p, board, board_root) != repo:
            continue
        sig = f"{planlib.MEMBER_SIGIL}{p['board']}/" if p.get("board") else None
        claimed = []
        for f in planlib.spec_data(p)[1]:
            if sig and f.startswith(sig):
                claimed.append(f[len(sig):])
            elif not f.startswith(planlib.MEMBER_SIGIL):
                claimed.append(f)
        if claimed:
            others[r] = claimed
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
        """`(kept, inherited)` — the hunks of `p` the baseline does not
        hold and the ones it does, each a list of hunk text — or "" when
        every hunk is inherited, "all" when none is. None when there is no
        baseline — the file goes whole or not at all. Zero context on both
        sides, so two edits near each other are two hunks and not one
        merged one."""
        if base is None:
            return None
        cur = split_hunks(git_out(root, "diff", "HEAD", "-U0", "--no-color",
                                  "--", p)).get(p)
        if not cur:
            return ""
        _, hunks = cur
        old = base["hunks"].get(p, set())
        keep = [h for h in hunks if hunk_body(h) not in old]
        theirs = [h for h in hunks if hunk_body(h) in old]
        gone = old - {hunk_body(h) for h in theirs}
        line = two_authors(keep, gone) if keep and gone else None
        if line is not None:
            raise Stop(f"{rel}: two authors on one hunk: {p}:{line} — a "
                       f"baseline hunk merged with the worker's; `--widen "
                       f"{p}` takes the file whole, or leave one untouched "
                       f"line between the edits")
        return (keep, theirs) if keep and theirs else ("all" if keep else "")

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
            elif root == board_root and inside(path, [prd_rel]):
                # the PRD's own folder is the board's record — one writer,
                # committed whole: never by hunk, never a stop
                p["add"].append(path)
            elif inside(path, union):
                nh = new_hunks(root, path) if kind == "tracked" else None
                if not predates(root, path, kind):
                    share = sorted(r for r, claimed in others.items()
                                   if root == repo and inside(path, claimed))
                    if share:
                        raise Stop(f"{rel}: {path} is in "
                                   + ", ".join(share)
                                   + "'s footprint too — not only this "
                                   f"PRD's edits; `--widen {path}` takes "
                                   "it whole")
                if nh not in (None, "", "all"):
                    p["partial"][path] = nh
                elif predates(root, path, kind):
                    p["stop"].append(path)
                else:
                    p["add"].append(path)
            elif kind == "rename-source" and inside(path, union):
                # a rename's deletion half: the new path entered above (or
                # rides inherited) — staging the old path is what keeps the
                # private index from carrying HEAD's old blob forever
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
    if not ready and container(prd, prds, board):
        return close_container(board, rel, prd, prds, board_root, opts,
                               now, out)
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
    repo = repo_of(prd, board, board_root)
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
                    transition_row(board, rel, prd["state"], "failed", now)
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
            if root == board_root:
                out(f"  record:    {prd_rel}/prd.md — done, actual, the "
                    f"claim cleared, in this commit; commit: in a second, "
                    f"`{prd['name']} — record`")
        out("  message:\n    " + message.rstrip().replace("\n", "\n    "))
        dry_line(board, prds, rel, prd, opts["as"], [pmd], out)
        out(f"{rel}: dry — nothing written")
        return 0
    # stage every repo first, each in an index of its own: a refusal here
    # has written nothing anywhere
    said, staged_roots = [], []
    roots = [r_ for r_, p in plan.items() if p["add"] or p["partial"]]
    if board_root not in roots:
        roots.append(board_root)
    with private_index(roots):
      for root, p in plan.items():
        if not p["add"] and not p["partial"]:
            continue
        staged_roots.append(root)
        if p["add"]:
            git_out(root, "add", "--", *p["add"])
        # a shared file is staged as the working file with the inherited
        # hunks reversed — never as a patch with hunks left out, which
        # `git apply` places by a line number that counts the missing ones
        staged = {path: stage_by_hunk(root, path, foreign)
                  for path, (_, foreign) in p["partial"].items()}
        refusals = placement_refusals(root, p["partial"], staged)
        if refusals:
            out(f"{rel}: staged by hunk and refused — nothing committed, "
                f"nothing staged:")
            for x in refusals:
                out(f"  {x}")
            raise Stop(f"{rel}: {len(refusals)} placement refusal(s) in "
                       f"{root}")
        if p["partial"]:
            said.append("by hunk " + ", ".join(p["partial"]))
        if p["riders"]:
            said.append("rides " + ", ".join(p["riders"]))
        if p["widened"]:
            said.append("widened " + ", ".join(p["widened"]))
      if inherited:
        said.append(f"inherited {len(inherited)}")

      # the record — every key but `commit:`, and the report, BEFORE the
      # commit, so the commit carries them; put back whole if the commit fails
      with open(pmd, encoding="utf-8") as f:
        before = f.read()
      hrs = (now - since).total_seconds() / 3600.0 if since else None
      if hrs is not None:
        editlib.set_key(pmd, "actual", fmt_hours(max(hrs, 0.0)))
      editlib.del_key(pmd, "claim")
      editlib.set_key(pmd, "state", "done")
      # 6 — the report to the daemon, which appends `## Report` to prd.md
      text = ("trusted — the verify was not run by collect" if trusted
              else "\n\n".join(report) or "no `## Verify and Proof` block")
      posted = post_report(board, rel, text)
      git_out(board_root, "add", "--", prd_rel)
      if board_root not in staged_roots:
        staged_roots.append(board_root)
      committed = {r_: list(plan[r_]["add"]) + list(plan[r_]["partial"])
                   for r_ in staged_roots}
      committed[board_root].append(prd_rel)
      shas = []
      for root in staged_roots:
        try:
            shas.append(commit_private(root, message))
        except Stop as e:
            editlib.write_atomic(pmd, before)
            raise Stop(f"{rel}: git commit failed in {root} — the record "
                       f"put back, nothing written: {e}")
        settle_shared(root, committed[root])
      settle(board, [x for p in plan.values() for x in p["riders"]])

      # 5 — `commit:` — the one key that cannot be in the commit it names:
      # a second, one-key commit right behind, so nothing rides
      editlib.set_key(pmd, "commit", " ".join(shas))
      pmd_rel = os.path.relpath(pmd, board_root)
      git_out(board_root, "add", "--", pmd_rel)
      try:
        said.append("record " + commit_private(
            board_root, f"{prd['name']} — record\n\nprd: {prd_rel}\n"))
      except Stop as e:
        raise Stop(f"{rel}: the record commit failed in {board_root} — "
                   f"`commit:` is written and unstaged: {e}")
      settle_shared(board_root, [pmd_rel])

    # 7 — the line, the row
    transition_row(board, rel, prd["state"], "done", now)
    extra = " · ".join(x for x in [
        "trusted" if trusted else "", "gate red, known" if known else "",
        f"commit {' '.join(shas)}", *said, posted, "round file owed"] if x)
    out(progress_line(board, rel, prd["state"], "done", opts["as"], extra))
    return 0


# ── a container ───────────────────────────────────────────────────────────────

def container(prd, prds, board):
    """`dispatchable`'s word for it — plan.py's one predicate, the same one
    `claim` refuses on and `scan` lists under collect with. An `open` PRD
    only: a held parent is a worker's, and a parked one is a person's."""
    return (prd["state"] == "open"
            and (planlib.dispatchable(prd, prds, board) or ""
                 ).startswith("container:"))


def last_child_commit(kids, board, board_root):
    """The `commit:` of the child that landed last — the newest of the
    children's shas by commit date, each read in the repo the child wrote;
    two in the same second are ordered by how deep in history they sit.
    `none` when no child's sha resolves."""
    best = None
    for c in kids:
        raw = str(c["fm"].get("commit", "") or "").split()
        if not raw or raw[0] == "none":
            continue
        root = repo_of(c, board, board_root)
        r = subprocess.run(["git", "-C", root, "log", "-1", "--format=%ct",
                            raw[0]], capture_output=True, text=True)
        if r.returncode != 0 or not r.stdout.strip():
            continue
        depth = subprocess.run(["git", "-C", root, "rev-list", "--count",
                                raw[0]], capture_output=True, text=True)
        key = (int(r.stdout.strip()), int(depth.stdout.strip() or 0))
        if best is None or key > best[0]:
            best = (key, raw[0])
    return best[1] if best else "none"


def close_container(board, rel, prd, prds, board_root, opts, now, out=print):
    """A parent whose every child is `done`, with no spec and no open box of
    its own: nothing to verify, nothing to add but its own `prd.md`. `done`,
    `actual:` the sum of the children's, `commit:` the last child's, in one
    commit `<parent> — done: every child landed`."""
    kids = [prds[c] for c in prd["children"] if c in prds]
    live = [c["rel"] for c in kids if c["state"] != "done"]
    if not kids or live:
        raise Stop(f"{rel}: standing() calls it finished, but it holds "
                   f"{'no child' if not kids else 'a child not done: ' + ', '.join(live)}"
                   f" — not a container; nothing written")
    pmd = os.path.join(prd["dir"], "prd.md")
    prd_rel = os.path.relpath(prd["dir"], board_root)
    actual = fmt_hours(sum(planlib.hours(c["fm"].get("actual"))
                           for c in kids))
    sha = last_child_commit(kids, board, board_root)
    message = f"{prd['name']} — done: every child landed\n\nprd: {prd_rel}\n"
    phrase = "container: every child done — pearde collect closes it"
    if opts.get("dry"):
        out(f"{rel}: {phrase}")
        out(f"  children:  {', '.join(c['rel'] for c in kids)}")
        out(f"  would add: {prd_rel}/prd.md")
        out(f"  record:    state: done · actual: {actual} · commit: {sha}")
        out("  message:\n    " + message.rstrip().replace("\n", "\n    "))
        dry_line(board, prds, rel, prd, opts["as"], [pmd], out)
        out(f"{rel}: dry — nothing written")
        return 0
    with open(pmd, encoding="utf-8") as f:
        before = f.read()
    editlib.set_key(pmd, "actual", actual)
    editlib.set_key(pmd, "commit", sha)
    editlib.del_key(pmd, "claim")
    editlib.set_key(pmd, "state", "done")
    posted = post_report(board, rel, f"{phrase}\n\nchildren: "
                         + ", ".join(c["rel"] for c in kids))
    pmd_rel = os.path.relpath(pmd, board_root)
    with private_index([board_root]):
        git_out(board_root, "add", "--", pmd_rel)
        try:
            own = commit_private(board_root, message)
        except Stop as e:
            editlib.write_atomic(pmd, before)
            raise Stop(f"{rel}: git commit failed in {board_root} — the "
                       f"record put back, nothing written: {e}")
        settle_shared(board_root, [pmd_rel])
    transition_row(board, rel, prd["state"], "done", now)
    extra = " · ".join([f"container, {len(kids)} children",
                        f"commit {sha}", f"record {own}", posted,
                        "round file owed"])
    out(progress_line(board, rel, prd["state"], "done", opts["as"], extra))
    return 0


def cmd_collect(argv, board=None):
    """The entry: `collect [<prd>…] [flags]`. Exit 0 when every PRD named
    was collected, 1 when any stopped, 2 on usage."""
    try:
        opts = parse_args(argv)
    except (Stop, translib.FlagRefused) as e:
        print(f"collect: {e}", file=sys.stderr)
        return 2
    except translib.Refused as e:       # no persona named — exit 1, nothing read
        print(f"collect: refused — {e}", file=sys.stderr)
        return 1
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
        # a container is finished work too — `scan`'s collect band lists it
        # beside the held-and-finished; the bare `collect` closes both
        for x in sorted(r["todo"]) if r else []:
            if x not in rels and container(r["todo"][x], r["prds"], board):
                rels.append(x)
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


cmd_collect.flags = FLAGS       # what `pearde collect --help` prints
COMMANDS = {"collect": cmd_collect}


def main():
    sys.exit(cmd_collect(sys.argv[1:]))


if __name__ == "__main__":
    main()
