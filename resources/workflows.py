#!/usr/bin/env python3
"""pearde workflows — the library of how a kind of job is done: read it, check it.

    python3 workflows.py list  [board]        slug · kind · runs · updated · subject
    python3 workflows.py show  <slug> [board] the file
    python3 workflows.py brief <slug> [board] the workflow as one page, atomics inlined
    python3 workflows.py check [board]        one problem per line; silent when clean
    python3 workflows.py add <slug> <atomic|workflow> <subject> [board]
                                               write <slug>.md from the template, body on
                                               stdin — refused when the slug is taken

A workflow is `.pearde/workflows/<slug>.md`. It is not a PRD: no state, never
claimed, never dispatched, invisible to the loop and to the progress line. It
records how a job is done and gets better every time it is followed.
@references/workflow.md is the format. This file is its only reader, so the
format has one home.

Python 3 stdlib only. `parse` comes from @resources/memos.py — one frontmatter
parser on the board, not two that drift.
"""
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import memos  # noqa: E402
from memos import ISO_RE, parse  # noqa: E402

# The closed set, per @references/workflow.md. Exactly one slug key, and the
# slug key says the kind — there is no `kind:`, because two fields that must
# agree are one field that can disagree.
# A member's PRD is addressed `@<member>/<rel>`, the address `plan.py scan`
# prints. Kept spelled the same in both readers — one address, two readers.
MEMBER_SIGIL = "@"

SLUG_KEYS = ("atomic", "workflow")
REQUIRED = ("subject", "date")
OPTIONAL = ("updated", "runs")

# `| 1 | `slug` | why | `stop` |` — cells are read with backticks stripped, so
# the template's `` `stop` `` and the format's bare `stop` are one grammar.
ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
SEP_RE = re.compile(r"^[\s|:-]+$")
JUMP_RE = re.compile(r"^→\s*(\d+)$")


def _cells(line):
    m = ROW_RE.match(line)
    if not m:
        return None
    return [c.strip().strip("`").strip() for c in m.group(1).split("|")]


def section(body, name):
    """The lines under `## <name>`, up to the next `##`. None when absent."""
    out, on = [], False
    for line in body.splitlines():
        if line.startswith("## "):
            if on:
                break
            on = line[3:].strip() == name
            continue
        if on:
            out.append(line)
    return out if on else None


def steps(body):
    """[{n, atomic, why, onfail, raw}] from the `## Steps` table, in file order.
    `n` is the `#` cell verbatim — contiguity is the check's to judge."""
    lines = section(body, "Steps")
    if lines is None:
        return None
    rows = []
    for line in lines:
        if line.lstrip().startswith("<!--"):
            continue
        cells = _cells(line)
        if not cells or SEP_RE.match(line.strip()):
            continue
        if len(cells) < 4:
            continue
        if cells[0] == "#" and cells[1] == "atomic":
            continue
        rows.append({"n": cells[0], "atomic": cells[1], "why": cells[2],
                     "onfail": cells[3], "raw": line.rstrip()})
    return rows


def find_board(arg):
    """@resources/memos.py resolves the board; only the prefix on the failure
    is ours, so the error names the command that was run."""
    try:
        return memos.find_board(arg)
    except SystemExit as e:
        sys.exit(str(e).replace("memos:", "workflows:", 1))


def workflows_dir(board):
    """(path, external). `.pearde/workflows/` unless `workflows:` in
    .pearde/settings.md points elsewhere. Unlike `memos:`, elsewhere is not a
    mirror of a foreign system — it is the library itself, shared by several
    boards, so it gets the whole check wherever it lives."""
    st = os.path.join(board, "settings.md")
    if os.path.isfile(st):
        fm, _, _ = parse(st)
        v = (fm or {}).get("workflows")
        if v and not isinstance(v, list):
            return os.path.normpath(os.path.join(board, v)), True
    return os.path.join(board, "workflows"), False


def scan(board):
    """{slug: entry} for every file in the library. Workflows first, then
    atomics, each by slug — the order `list` and a reader want."""
    d, _ = workflows_dir(board)
    if not os.path.isdir(d):
        return {}
    out = {}
    for f in sorted(os.listdir(d)):
        if not f.endswith(".md") or f == "README.md":
            continue
        path = os.path.join(d, f)
        fm, title, body = parse(path)
        slug, ok = f[:-3], fm is not None
        fm = fm or {}
        kind = ""
        if "workflow" in fm and "atomic" not in fm:
            kind = "workflow"
        elif "atomic" in fm and "workflow" not in fm:
            kind = "atomic"
        out[slug] = {
            "slug": slug, "path": path, "fm": fm,
            "parsed": ok,
            "title": title or slug,
            "body": body,
            "kind": kind,
            "subject": fm.get("subject", ""),
            "date": fm.get("date", ""),
            "updated": fm.get("updated", ""),
            "runs": fm.get("runs", ""),
        }
    return dict(sorted(out.items(),
                       key=lambda kv: (kv[1]["kind"] != "workflow", kv[0])))


TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "references", "templates")


def add(board, slug, kind, subject, body, date):
    """Write `<slug>.md` to the library, shaped like `<kind>.md` in
    @references/templates — the slug key, `subject`, `date` and `runs: 0`
    filled, `body` (already `# <slug> — <phrase>` on down) as everything
    under the frontmatter. Refused when the slug is already taken, by either
    kind — one namespace, one file per slug. Raises `ValueError`; the caller
    turns that into whatever refusal its own contract uses."""
    if slug in scan(board):
        raise ValueError(f"`{slug}` is already in the library")
    if kind not in ("workflow", "atomic"):
        raise ValueError(f"add: kind `{kind}` is neither workflow nor atomic")
    if not os.path.isfile(os.path.join(TEMPLATES_DIR, f"{kind}.md")):
        raise ValueError(f"add: no {kind}.md in {TEMPLATES_DIR}")
    d, _ = workflows_dir(board)
    if not os.path.isdir(d):
        os.makedirs(d)
    path = os.path.join(d, f"{slug}.md")
    fm = (f"---\n{kind}: {slug}\nsubject: {subject}\ndate: {date}\n"
          f"runs: 0\n---\n\n")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(fm + body.strip("\n") + "\n")
    os.replace(tmp, path)
    return path


def members(board):
    """[(name, path)] — the member boards a master board merges.

    `members:` has exactly one reader on this board and it lives in the
    planner; this borrows it rather than parsing the key a second time, so
    the two never drift. The import is deferred on purpose: `plan.py` imports
    this module at its top, and a module-level import here would close that
    circle while both are still loading."""
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "board")
    if d not in sys.path:
        sys.path.insert(0, d)
    import plan  # noqa: E402 — deferred: plan.py imports this module
    return plan.members(board)


def _refs_one(board, prefix=""):
    """[(rel, value, board)] — every `workflow:` in a prd.md or a spec on one
    board, the value as written. A non-scalar shape is carried out rather
    than dropped: the reader that finds it is the reader that reports it.

    Walks `<board>/prds`, not `board` itself: a PRD tree lives one level
    under the board root, same as `memos.py board_prds` — walking `board`
    would still find every ref (the tree is a subtree either way) but would
    label each one `prds/<rel>`, one level off from what a reader expects."""
    refs = []
    lib, _ = workflows_dir(board)
    lib = os.path.abspath(lib)
    prds_root = os.path.join(board, "prds")
    if not os.path.isdir(prds_root):
        return refs
    for root, dirs, names in os.walk(prds_root):
        if os.path.abspath(root) == lib:
            dirs[:] = []
            continue
        for n in sorted(names):
            if n != "prd.md" and os.path.basename(root) != "specs":
                continue
            if not n.endswith(".md"):
                continue
            path = os.path.join(root, n)
            fm, _, _ = parse(path)
            v = (fm or {}).get("workflow")
            if v:
                refs.append((prefix + os.path.relpath(path, prds_root), v, board))
    return refs


def board_workflow_refs(board):
    """[(rel, value, board)] — every `workflow:` on this board and, when this
    is a master, on every member board too, addressed `@<member>/<rel>` the
    way `plan.py scan` addresses it.

    The board half of the check: a PRD routed to a workflow nobody wrote is a
    worker sent nowhere, and a member's PRD is no less routed for living on
    another path. The board each ref came from travels with it — resolution
    is per-PRD, never against one flattened set, because the library does not
    merge and only the refs do."""
    refs = _refs_one(board)
    for name, path in members(board):
        if os.path.isdir(path):
            refs += _refs_one(path, f"{MEMBER_SIGIL}{name}/")
    return refs


def check(board):
    """Every problem, one string each. Empty means the library is clean."""
    d, external = workflows_dir(board)
    if external and not os.path.isdir(d):
        return [f"settings.md: `workflows: …` points at {d}, "
                "which does not exist"]
    lib, bad = scan(board), []
    for slug in sorted(lib):
        e, at = lib[slug], f"{slug}.md"
        if not e["parsed"]:
            bad.append(f"{at}: no closed `---` frontmatter fence")
            continue
        fm = e["fm"]
        keys = [k for k in SLUG_KEYS if k in fm]
        if not keys:
            bad.append(f"{at}: neither `atomic:` nor `workflow:` — "
                       "the slug key says the kind")
            continue
        if len(keys) > 1:
            bad.append(f"{at}: both `atomic:` and `workflow:` — "
                       "exactly one slug key says the kind")
            continue
        key = keys[0]
        if fm.get(key) != slug:
            bad.append(f"{at}: `{key}: {fm[key] or ''}` disagrees with "
                       "the filename")
        for k in REQUIRED:
            if not fm.get(k):
                bad.append(f"{at}: missing `{k}:`")
        for k in fm:
            if k not in SLUG_KEYS + REQUIRED + OPTIONAL:
                bad.append(f"{at}: `{k}:` is not a workflow key — "
                           "a misspelled key reads as present")
        date, upd = str(fm.get("date") or ""), str(fm.get("updated") or "")
        if date and not ISO_RE.match(date):
            bad.append(f"{at}: date `{date}` is not ISO 8601 (YYYY-MM-DD)")
        if upd and not ISO_RE.match(upd):
            bad.append(f"{at}: updated `{upd}` is not ISO 8601 (YYYY-MM-DD)")
        elif upd and ISO_RE.match(date or "") and upd < date:
            bad.append(f"{at}: updated {upd} precedes date {date}")
        runs = fm.get("runs")
        if runs not in (None, "", []):
            s = str(runs)
            if not (s.isdigit() and int(s) >= 0):
                bad.append(f"{at}: runs `{s}` is not an integer >= 0")
        body = e["body"]
        if key == "atomic":
            for s in ("Do", "Done when"):
                if not section(body, s):
                    bad.append(f"{at}: an atomic with no `## {s}`")
        else:
            rows = steps(body)
            if not rows:
                bad.append(f"{at}: a workflow with no `## Steps` table")
                continue
            for i, r in enumerate(rows, start=1):
                if r["n"] != str(i):
                    bad.append(f"{at}: step `{r['n']}` is not {i} — "
                               "`#` counts from 1, contiguous")
                if r["atomic"] not in lib:
                    bad.append(f"{at}: step {r['n']} names `{r['atomic']}`, "
                               "no file in the library")
                f = r["onfail"]
                m = JUMP_RE.match(f)
                if f == "stop":
                    pass
                elif m and r["n"].isdigit() and int(m.group(1)) < int(r["n"]) \
                        and int(m.group(1)) >= 1:
                    pass
                else:
                    bad.append(f"{at}: step {r['n']} on failure `{f}` — "
                               "neither `stop` nor `→ N` with N earlier")
    # A member named in `members:` and absent from disk is reported, not
    # skipped: `plan.py`'s `cmd_status` prints MISSING for one, and a check
    # that walks past it would call a board clean it never opened.
    for name, path in members(board):
        if not os.path.isdir(path):
            bad.append(f"settings.md: member `{name}` is not on disk at "
                       f"{path} — a member that cannot be read is not clean")

    # One scan per library, not one per PRD. The board's own is already in
    # hand; a member's is read the first time one of its PRDs asks.
    libs = {os.path.abspath(board): lib}

    def library(b):
        k = os.path.abspath(b)
        if k not in libs:
            libs[k] = scan(b)
        return libs[k]

    for rel, val, home in board_workflow_refs(board):
        if isinstance(val, list):
            # Neither a slug nor absence. @references/workflow.md says the key
            # holds one slug and anything else is a break, so the shape error
            # joins the dangling slug instead of passing as silence.
            bad.append(f"{rel}: `workflow:` is a list of "
                       f"{len(val)} — the key holds one slug, and any other "
                       "shape is a break, not an absence")
            continue
        if not isinstance(val, str):
            bad.append(f"{rel}: `workflow:` is not a slug — the key holds "
                       "one slug, and any other shape is a break, not an "
                       "absence")
            continue
        slug = val.strip()
        if not slug:
            continue
        # Its own board's library first, then the master's — the order
        # @references/parts/workers.md sets, and the order `needs:` resolves
        # in. The libraries are asked in turn; they are never merged.
        seen, order = set(), []
        for b in (home, board):
            k = os.path.abspath(b)
            if k not in seen:
                seen.add(k)
                order.append(b)
        found = [library(b)[slug] for b in order if slug in library(b)]
        where = ("its library or the master's" if len(order) > 1
                 else "the library")
        if not found:
            bad.append(f"{rel}: `workflow: {slug}` names no workflow "
                       f"in {where}")
        elif not any(e["kind"] == "workflow" for e in found):
            # The file is right there. Saying it "names no workflow" about a
            # slug the reader can open costs the checker its credibility, so
            # this branch names the file and says what it is instead.
            bad.append(f"{rel}: `workflow: {slug}` names `{slug}.md`, not a "
                       "workflow — a route was asked for and a single step "
                       "was found")
    return bad


def _under(body):
    """An atomic's `##` sections demoted to `####`, so an inlined body sits
    UNDER its `### N — <atomic>` heading instead of closing it. Fenced blocks
    are left alone — a `## ` inside one is text, not a heading."""
    out, fence = [], False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
        elif not fence and line.startswith("## "):
            line = "##" + line
        out.append(line)
    return "\n".join(out)


def brief(board, slug):
    """The workflow as one page: `## Use when`, then per step its row and the
    atomic's body. What a worker reads once before starting."""
    lib = scan(board)
    e = lib.get(slug)
    if e is None:
        print(f"workflows: no `{slug}` in the library", file=sys.stderr)
        return 1
    if e["kind"] != "workflow":
        print(f"workflows: `{slug}` is an atomic — an atomic is shown, "
              "not briefed", file=sys.stderr)
        return 1
    out = [f"# {e['title']}", ""]
    use = section(e["body"], "Use when")
    if use is not None:
        # Trim the blank lines at the ends, keep the ones in the middle:
        # dropping every blank glues a paragraph onto the last bullet, on the
        # one page a worker actually reads.
        body = list(use)
        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()
        out += ["## Use when", ""] + body + [""]
    rows = steps(e["body"]) or []
    for r in rows:
        out += [f"### {r['n']} — {r['atomic']}", "",
                "| # | atomic | why | on failure |",
                "|---|--------|-----|------------|", r["raw"], ""]
        a = lib.get(r["atomic"])
        if a is None:
            out += [f"*no `{r['atomic']}.md` in the library — this step "
                    "sends a worker nowhere*", ""]
            continue
        out += [_under(a["body"].strip()), ""]
    print("\n".join(out).rstrip())
    return 0


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "check"
    if cmd == "add":
        if len(argv) < 5:
            print("workflows: add <slug> <atomic|workflow> <subject> [board] "
                  "— the body on stdin", file=sys.stderr)
            return 2
        slug, kind, subject = argv[2], argv[3], argv[4]
        board = find_board(argv[5] if len(argv) > 5 else None)
        import datetime
        try:
            path = add(board, slug, kind, subject, sys.stdin.read(),
                       datetime.date.today().isoformat())
        except ValueError as e:
            print(f"workflows: refused — {e}", file=sys.stderr)
            return 1
        print(path)
        return 0
    if cmd in ("show", "brief"):
        if len(argv) < 3:
            print(f"workflows: {cmd} needs a slug", file=sys.stderr)
            return 2
        slug = argv[2]
        board = find_board(argv[3] if len(argv) > 3 else None)
        if cmd == "brief":
            return brief(board, slug)
        e = scan(board).get(slug)
        if e is None:
            print(f"workflows: no `{slug}` in the library", file=sys.stderr)
            return 1
        sys.stdout.write(open(e["path"], encoding="utf-8").read())
        return 0
    board = find_board(argv[2] if len(argv) > 2 else None)
    if cmd == "check":
        bad = check(board)
        if bad:
            print("\n".join(bad))
        return 1 if bad else 0
    if cmd == "list":
        for e in scan(board).values():
            print(f"{e['slug']:28} {e['kind']:9} {str(e['runs'] or 0):>4}  "
                  f"{str(e['updated'] or ''):11} {e['subject']}")
        return 0
    print(__doc__.strip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
