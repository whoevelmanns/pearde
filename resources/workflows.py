#!/usr/bin/env python3
"""pearde workflows — the library of how a kind of job is done: read it, check it.

    python3 workflows.py list  [board]        slug · kind · runs · updated · subject
    python3 workflows.py show  <slug> [board] the file
    python3 workflows.py brief <slug> [board] the workflow as one page, atomics inlined
    python3 workflows.py check [board]        one problem per line; silent when clean

A workflow is `prds/workflows/<slug>.md`. It is not a PRD: no state, never
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import memos  # noqa: E402
from memos import ISO_RE, parse  # noqa: E402

# The closed set, per @references/workflow.md. Exactly one slug key, and the
# slug key says the kind — there is no `kind:`, because two fields that must
# agree are one field that can disagree.
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
    """(path, external). `prds/workflows/` unless `workflows:` in
    prds/settings.md points elsewhere. Unlike `memos:`, elsewhere is not a
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


def board_workflow_refs(board):
    """[(relpath, slug)] — every `workflow:` in a prd.md or a spec on this
    board. The board half of the check: a PRD routed to a workflow nobody
    wrote is a worker sent nowhere."""
    refs = []
    lib, _ = workflows_dir(board)
    lib = os.path.abspath(lib)
    for root, dirs, names in os.walk(board):
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
            if v and not isinstance(v, list):
                refs.append((os.path.relpath(path, board), v))
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
    for rel, slug in board_workflow_refs(board):
        if slug not in lib:
            bad.append(f"{rel}: `workflow: {slug}` names no workflow "
                       "in the library")
        elif lib[slug]["kind"] != "workflow":
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
        out += ["## Use when", ""] + [l for l in use if l.strip()] + [""]
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
