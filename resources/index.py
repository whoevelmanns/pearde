#!/usr/bin/env python3
"""Read and check index.md — the only reader of that format.

    index.py files                 every anchor in the Files tables, one per line
    index.py keywords              every keyword, one per line
    index.py scope <keyword>       the anchors that keyword resolves to
    index.py check                 problems, one per line; silent and 0 when clean

index.md is the map: `@<path>` is one file, `@@<keyword>` is a scope. A
drifted map is worse than none — it answers confidently and wrongly. `check`
catches all four ways it drifts, and `doctor` runs it:

    a file on disk with no row            the map is incomplete
    a row naming no file                  the map points at nothing
    a scope naming no file                a keyword resolves to a dead path
    a keyword used and never defined      a document names a scope that does
                                          not exist
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.md")

# The fallback set, for a tree with no git. git itself is the authority.
SKIP_DIRS = {".git", ".claude", "__pycache__", "node_modules", "state"}
SKIP_NAMES = {".DS_Store"}
# Files carrying anchors and keywords worth checking. Anything else is data.
TEXT_EXT = {".md", ".sh", ".py", ".txt"}

ROW = re.compile(r"^\|\s*@([A-Za-z0-9_./-]+)\s*\|", re.M)
KEYWORD_ROW = re.compile(r"^\|\s*`@@([a-z][a-z0-9-]*)`\s*\|(.*)\|(.*)\|\s*$", re.M)
KEYWORD_USE = re.compile(r"@@([a-z][a-z0-9-]*)")


def index_text():
    with open(INDEX, encoding="utf-8") as fh:
        return fh.read()


def files():
    """Every anchor with a row in the Files tables."""
    return [a for a in ROW.findall(index_text()) if not a.startswith("@")]


def keywords():
    """{keyword: [anchor, ...]} — the scope each keyword resolves to."""
    out = {}
    for name, _is, reads in KEYWORD_ROW.findall(index_text()):
        out[name] = re.findall(r"@([A-Za-z0-9_./-]+)", reads)
    return out


def board(path):
    """A board file, not a skill file. `prds/` addresses a board — the index
    maps this skill, so a board that happens to sit at the skill root gets no
    rows and is not missing any."""
    return path == "prds" or path.startswith("prds/")


def tracked():
    """Every file on disk the index is expected to hold a row for — tracked,
    plus untracked and not ignored. git owns the answer, so a path added to
    .gitignore leaves the index the same day it leaves the repo."""
    try:
        out = subprocess.run(
            ["git", "-C", ROOT, "ls-files", "--cached", "--others",
             "--exclude-standard"],
            capture_output=True, text=True, check=True).stdout
        return [p for p in out.splitlines()
                if p and not board(p)
                and os.path.exists(os.path.join(ROOT, p))]
    except (OSError, subprocess.CalledProcessError):
        pass
    found = []
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for n in names:
            if n in SKIP_NAMES:
                continue
            rel = os.path.relpath(os.path.join(base, n), ROOT)
            if not board(rel):
                found.append(rel)
    return found


def check():
    problems = []
    rows, scopes = files(), keywords()
    listed, disk = set(rows), set(tracked())

    for path in sorted(disk - listed):
        problems.append(f"{path} is on disk with no row in index.md")
    for path in sorted(listed - disk):
        problems.append(f"index.md lists @{path} — not on disk")
    for name in sorted(scopes):
        for anchor in scopes[name]:
            if not os.path.exists(os.path.join(ROOT, anchor)):
                problems.append(f"@@{name} names @{anchor} — not on disk")

    for path in sorted(disk):
        if os.path.splitext(path)[1] not in TEXT_EXT:
            continue
        with open(os.path.join(ROOT, path), encoding="utf-8", errors="replace") as fh:
            body = fh.read()
        for name in sorted(set(KEYWORD_USE.findall(body))):
            if name not in scopes:
                problems.append(f"{path} references @@{name} — no such keyword")

    return problems


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "check"
    if cmd == "files":
        print("\n".join(files()))
    elif cmd == "keywords":
        print("\n".join(sorted(keywords())))
    elif cmd == "scope":
        if len(argv) < 3:
            print("usage: index.py scope <keyword>", file=sys.stderr)
            return 2
        scopes = keywords()
        if argv[2] not in scopes:
            print(f"no keyword @@{argv[2]}", file=sys.stderr)
            return 1
        print("\n".join(scopes[argv[2]]))
    elif cmd == "check":
        problems = check()
        if problems:
            print("\n".join(problems))
        return 1 if problems else 0
    else:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
