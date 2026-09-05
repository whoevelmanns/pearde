#!/usr/bin/env python3
"""pearde memos — the board's decision records: read them, and check them.

    python3 memos.py check [board]      one problem per line; silent when clean
    python3 memos.py list  [board]      slug · kind · status · date · subject
    python3 memos.py add   <subject> [board]  slug it, write the memo from the template, print the path

A memo is `.pearde/memos/<slug>.md`. It is not a PRD: no state, never claimed,
never dispatched, invisible to the loop and to the progress line. It records
what was decided and what it beat. @references/memo.md is the format. This
file is its only reader, so the format has one home.

Python 3 stdlib only. @resources/board/plan.py and @resources/board/serve.py
import `scan` from here rather than growing a second frontmatter parser.
"""
import datetime
import os
import re
import sys

# win: a cp1252 console cannot encode the glyphs the board files carry
# (the "->" arrow of a workflow table, every umlaut of a German PRD), and
# the output dies on UnicodeEncodeError. Force UTF-8 out.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REQUIRED = ("memo", "kind", "status", "subject", "date")
OPTIONAL = ("updated", "prds", "supersedes", "superseded_by")
KINDS = ("decision", "note")
STATUSES = ("open", "decided", "superseded")

# The board's dialect, byte-rule for byte-rule what prd.md uses: a `---`
# fence, one `key: value` per line, `- item` for lists, `#` comments.
KEY_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_-]*):\s*(.*?)\s*$")
ITEM_RE = re.compile(r"^\s*-\s+(.*?)\s*$")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _clean(v):
    return re.sub(r"\s+#.*$", "", v).strip().strip("\"'")


def parse(path):
    """(frontmatter, title, body). frontmatter is None when the fence is
    missing or unterminated — the caller reports that, it is not a crash."""
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "", text
    fm, key, end = {}, None, None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
        if line.lstrip().startswith("#"):
            continue
        m = ITEM_RE.match(line)
        if m and key is not None:
            if not isinstance(fm.get(key), list):
                fm[key] = []
            fm[key].append(_clean(m.group(1)))
            continue
        m = KEY_RE.match(line)
        if m:
            key = m.group(1)
            v = _clean(m.group(2))
            fm[key] = v if v else []
    if end is None:
        return None, "", text
    rest = lines[end + 1:]
    title = ""
    body = []
    for line in rest:
        if not title and line.startswith("# "):
            title = line[2:].strip()
            continue
        body.append(line)
    return fm, title, "\n".join(body).strip()


def memos_dir(board):
    """(path, external). `.pearde/memos/` unless `memos:` in .pearde/settings.md
    points elsewhere — a repo whose decisions already live in another system
    mirrors that dir read-only instead of moving files another tool owns.
    External means foreign contract: the strict frontmatter gate applies only
    to the board's own memos/."""
    st = os.path.join(board, "settings.md")
    if os.path.isfile(st):
        fm, _, _ = parse(st)
        v = (fm or {}).get("memos")
        if v and not isinstance(v, list):
            return os.path.normpath(os.path.join(board, v)), True
    return os.path.join(board, "memos"), False


def scan(board):
    """{slug: memo} for every .pearde/memos/*.md. Sorted by date descending, then
    slug — newest decision first, which is the order a reader wants."""
    d, _ = memos_dir(board)
    if not os.path.isdir(d):
        return {}
    out = {}
    for f in sorted(os.listdir(d)):
        if not f.endswith(".md") or f == "README.md":
            continue
        path = os.path.join(d, f)
        fm, title, body = parse(path)
        slug = f[:-3]
        out[slug] = {
            "slug": slug, "path": path, "fm": fm or {},
            "parsed": fm is not None,
            "title": title or slug,
            "body": body,
            "kind": (fm or {}).get("kind", ""),
            "status": (fm or {}).get("status", ""),
            "subject": (fm or {}).get("subject", ""),
            "date": (fm or {}).get("date", ""),
        }
    return dict(sorted(out.items(),
                       key=lambda kv: (str(kv[1]["date"]), kv[0]), reverse=True))


def board_prds(board):
    # A memo's `prds:` reference is a PRD name relative to the board's
    # `.pearde/prds/`, not to the board — so the walk starts there. Before the board
    # moved from `<repo>/prds` to `<repo>/.pearde` the two were the same
    # directory and this distinction did not exist.
    # relpath is OS-native (`\` on Windows); every `prds:` reference in a
    # memo is written `/`, the project's own convention — normalize so the
    # comparison in `check()` is not a silent path-separator mismatch.
    root = os.path.join(board, "prds")
    if not os.path.isdir(root):
        return set()
    return {os.path.relpath(r, root).replace(os.sep, "/")
            for r, ds, fs in os.walk(root)
            if "prd.md" in fs and r != root}


def _listed(v):
    return v if isinstance(v, list) else [v] if v else []


def check(board):
    """Every problem, one string each. Empty means the memos are clean.
    An external memo dir is another system's contract: only what is universal
    is checked — the file parses, the required five are present — and its own
    vocabulary (kinds, statuses, extra keys) is left alone."""
    memos, bad = scan(board), []
    d, external = memos_dir(board)
    if external and not os.path.isdir(d):
        return [f"settings.md: `memos: …` points at {d}, which does not exist"]
    prds = board_prds(board)
    for slug in sorted(memos):
        m, at = memos[slug], f"{slug}.md"
        if not m["parsed"]:
            bad.append(f"{at}: no closed `---` frontmatter fence")
            continue
        fm = m["fm"]
        if external:
            for k in REQUIRED:
                if not fm.get(k):
                    bad.append(f"{at}: missing `{k}:`")
            continue
        for k in REQUIRED:
            if not fm.get(k):
                bad.append(f"{at}: missing `{k}:`")
        for k in fm:
            if k not in REQUIRED + OPTIONAL:
                bad.append(f"{at}: `{k}:` is not a memo key — "
                           "a misspelled key reads as present")
        if fm.get("memo") and fm["memo"] != slug:
            bad.append(f"{at}: `memo: {fm['memo']}` disagrees with the filename")
        if fm.get("kind") and fm["kind"] not in KINDS:
            bad.append(f"{at}: kind `{fm['kind']}` — the set is {'|'.join(KINDS)}")
        st = fm.get("status")
        if st and st not in STATUSES:
            bad.append(f"{at}: status `{st}` — the set is {'|'.join(STATUSES)}")
        date, upd = str(fm.get("date") or ""), str(fm.get("updated") or "")
        if date and not ISO_RE.match(date):
            bad.append(f"{at}: date `{date}` is not ISO 8601 (YYYY-MM-DD)")
        if upd and not ISO_RE.match(upd):
            bad.append(f"{at}: updated `{upd}` is not ISO 8601 (YYYY-MM-DD)")
        elif upd and ISO_RE.match(date or "") and upd < date:
            bad.append(f"{at}: updated {upd} precedes date {date}")
        sb = _listed(fm.get("superseded_by"))
        if st == "superseded" and not sb:
            bad.append(f"{at}: status superseded, naming nothing in its place")
        if sb and st != "superseded":
            bad.append(f"{at}: superseded_by is set, status is `{st}`")
        for k in ("supersedes", "superseded_by"):
            for name in _listed(fm.get(k)):
                if name not in memos:
                    bad.append(f"{at}: `{k}: {name}` names no memo")
        for name in _listed(fm.get("prds")):
            if name not in prds:
                bad.append(f"{at}: `prds: {name}` is not a PRD on this board")
    return bad


def slug(subject):
    """The rule of @references/parts/handles.md: lowercase, spaces to
    hyphens — every run of anything else collapses to one hyphen."""
    return re.sub(r"[^a-z0-9]+", "-", subject.lower()).strip("-")


def add(board, subject):
    """Write `<memos>/<slug>.md` from @references/templates/memo.md and
    return its path. Line-based: `memo:`, `subject:`, `date:` and the title
    line are filled in; every other template line, comments included, is
    kept — the reader fills the sections. Exits 2 on a subject that slugs to
    nothing, 1 on a path that exists or a `memos:` dir that is another
    system's — that dir is mirrored read-only, nothing is written there."""
    subject = subject.strip()
    sl = slug(subject)
    if not sl:
        print(f"memos: `{subject}` slugs to nothing", file=sys.stderr)
        sys.exit(2)
    d, external = memos_dir(board)
    if external:
        print(f"memos: settings.md points `memos:` at {d} — another system's "
              "records, mirrored read-only; write the memo there",
              file=sys.stderr)
        sys.exit(1)
    path = os.path.join(d, sl + ".md")
    if os.path.exists(path):
        print(f"memos: {path} exists", file=sys.stderr)
        sys.exit(1)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tpl = open(os.path.join(root, "references", "templates", "memo.md"),
               encoding="utf-8").read()
    today = datetime.date.today().isoformat()
    out = []
    for line in tpl.splitlines():
        if line.startswith("memo: <slug>"):
            line = f"memo: {sl}"
        elif line.startswith("subject: "):
            line = f"subject: {subject}"
        elif line.startswith("date: "):
            line = f"date: {today}"
        elif line.startswith("# <slug> — "):
            line = f"# {sl} — {subject}"
        out.append(line)
    os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    os.replace(tmp, path)
    return path


# Duplicated from @resources/board/plan.py's own BOARD_DIR rather than
# imported — same reason @resources/guard.py gives: this reader keeps its
# own error prefix and does not depend on the planner to resolve a board.
BOARD_DIR = ".pearde"


def find_board(arg):
    if arg:
        p = os.path.abspath(arg)
        if os.path.basename(p) == BOARD_DIR and os.path.isdir(p):
            return p
        if os.path.isdir(os.path.join(p, BOARD_DIR)):
            return os.path.join(p, BOARD_DIR)
        sys.exit(f"memos: no {BOARD_DIR}/ board at {arg}")
    d = os.getcwd()
    while True:
        if os.path.isdir(os.path.join(d, BOARD_DIR)):
            return os.path.join(d, BOARD_DIR)
        nxt = os.path.dirname(d)
        if nxt == d:
            sys.exit(f"memos: no {BOARD_DIR}/ board found walking up from the cwd")
        d = nxt


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "check"
    if cmd == "add":
        if len(argv) < 3 or not argv[2].strip():
            print("memos: add <subject> [board]", file=sys.stderr)
            return 2
        board = find_board(argv[3] if len(argv) > 3 else None)
        print(add(board, argv[2]))
        return 0
    board = find_board(argv[2] if len(argv) > 2 else None)
    if cmd == "check":
        bad = check(board)
        if bad:
            print("\n".join(bad))
        return 1 if bad else 0
    if cmd == "list":
        for m in scan(board).values():
            print(f"{m['slug']:24} {m['kind']:9} {m['status']:11} "
                  f"{m['date']:11} {m['subject']}")
        return 0
    print(__doc__.strip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
