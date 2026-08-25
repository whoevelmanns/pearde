#!/usr/bin/env python3
"""Read @references/targets.md — the only reader of that format.

    targets.py skills                 every skill in this repo: name<TAB>path
    targets.py agents [start]         one row per agent, resolved:
                                      agent<TAB>present<TAB>skills<TAB>context
    targets.py status [start]         one line per thing that can be wired:
                                      agent<TAB>kind<TAB>state<TAB>path<TAB>want
    targets.py statusline [start]     one line per agent that renders one:
                                      agent<TAB>file<TAB>key<TAB>command
                                      command empty means nothing configured
    targets.py block                  the context block, markers included

`kind` is a skill name, or `context`. `state` is one of:

    ok        linked, and it resolves to this repo
    missing   nothing there — install has not run, or a new skill was added
    stale     something there, pointing somewhere else
    copy      a real directory that is not this repo — `ln -s` on Windows
              without symlink rights silently copies, and a copy drifts

No agent is named in this file. Every agent-specific path comes from the
table in targets.md, so an agent is added by editing markdown.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = os.path.join(ROOT, "references", "targets.md")
SYSTEM = os.path.join(ROOT, "references", "system.md")
BEGIN, END = "<!-- pearde:begin", "<!-- pearde:end -->"

# The row shape: | agent | present | skills | context |. The prose above and
# below the table uses the same pipe characters inside code spans, so a row is
# only a row when its first cell is a bare lowercase word.
ROW = re.compile(
    r"^\|\s*([a-z][a-z0-9-]*)\s*\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|\s*$", re.M)
NONE = {"—", "-", ""}


def cell(text):
    """One cell to its alternatives, in order. Backticks are decoration."""
    text = text.strip().replace("`", "")
    if text in NONE:
        return []
    return [p.strip() for p in text.split("·") if p.strip()]


def expand(path, start):
    """One spelling to one absolute path, or None when it cannot exist.

    Scope is spelled by the path: `$`, `~` and `/` are machine-wide, anything
    else is per-project and hangs off `start`. An unset variable drops the
    alternative rather than expanding to a path rooted at `/` — that is the
    whole point of $CLAUDE_CONFIG_DIR-style rows having alternatives."""
    if path.startswith("$"):
        var = re.match(r"\$([A-Za-z_][A-Za-z0-9_]*)", path)
        if not var or not os.environ.get(var.group(1)):
            return None
        path = os.environ[var.group(1)] + path[var.end():]
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(start, path)
    return os.path.normpath(path)


def rows():
    """[(agent, present, skills, context, status)] — verbatim spellings."""
    with open(TARGETS, encoding="utf-8") as fh:
        text = fh.read()
    out = []
    for agent, present, sk, ctx, st in ROW.findall(text):
        if agent == "agent" or set(present.strip()) <= {"-", ":", " "}:
            continue
        out.append((agent, cell(present), cell(sk), cell(ctx), cell(st)))
    return out


def skills():
    """[(name, path)] — every skill folder in this repo, by folder name."""
    base = os.path.join(ROOT, "skills")
    if not os.path.isdir(base):
        return []
    out = []
    for name in sorted(os.listdir(base)):
        d = os.path.join(base, name)
        if os.path.isfile(os.path.join(d, "SKILL.md")):
            out.append((name, d))
    return out


def agents(start):
    """[(agent, present_path_or_None, skills_dir_or_None, context_or_None)].

    The first alternative that exists wins for `present`. For `skills` and
    `context` the first *expandable* one wins — they name where a thing goes,
    which is usually somewhere nothing is yet."""
    out = []
    for agent, present, sk, ctx, _st in rows():
        here = None
        for p in present:
            e = expand(p, start)
            if e and os.path.exists(e):
                here = e
                break
        pick = lambda alts: next(
            (e for e in (expand(a, start) for a in alts) if e), None)
        out.append((agent, here, pick(sk), pick(ctx)))
    return out


def statusline(start):
    """[(agent, file, key, command)] — where a continuous line is configured.

    The first spelling that already carries a command wins; when none does,
    the first that resolves is where one would go, with an empty command. The
    order in the table is the order the agent itself reads them in, so the
    file reported is the one actually in force — a line configured in a
    profile nothing loads is the false green this exists to catch."""
    out = []
    for agent, present, _sk, _ctx, st in rows():
        if not st:
            continue
        here = any(e and os.path.exists(e)
                   for e in (expand(p, start) for p in present))
        if not here:
            continue
        first = None
        for spell in st:
            path, _, key = spell.rpartition(":")
            e = expand(path, start)
            if not e:
                continue
            if first is None:
                first = (agent, e, key, "")
            cmd = read_key(e, key)
            if cmd:
                out.append((agent, e, key, cmd))
                break
        else:
            if first:
                out.append(first)
    return out


def read_key(path, dotted):
    """One dotted key out of a JSON file, as a string. Absent is empty."""
    if not os.path.isfile(path):
        return ""
    try:
        with open(path, encoding="utf-8") as fh:
            node = json.load(fh)
    except (OSError, ValueError):
        return ""
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return ""
        node = node[part]
    return node if isinstance(node, str) else ""


def block():
    """The context block, markers included — system.md, verbatim."""
    with open(SYSTEM, encoding="utf-8") as fh:
        return fh.read().strip()


def link_state(path, want):
    """What is at `path`, against the skill folder it should be."""
    if not os.path.lexists(path):
        return "missing"
    if os.path.islink(path):
        return "ok" if os.path.realpath(path) == os.path.realpath(want) else "stale"
    if os.path.isdir(path):
        if os.path.realpath(path) == os.path.realpath(want):
            return "ok"
        return "copy"
    return "stale"


def context_state(path):
    """Whether the block in `path` is there, and current."""
    if not path or not os.path.isfile(path):
        return "missing"
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    if BEGIN not in text or END not in text:
        return "missing"
    have = text[text.index(BEGIN):text.index(END) + len(END)]
    return "ok" if have.strip() == block() else "stale"


def status(start):
    """Every wireable thing, one tuple: (agent, kind, state, path, want)."""
    out = []
    ours = skills()
    for agent, here, skdir, ctx in agents(start):
        if not here:
            out.append((agent, "agent", "absent", "", ""))
            continue
        for name, path in ours:
            if not skdir:
                continue
            at = os.path.join(skdir, name)
            out.append((agent, name, link_state(at, path), at, path))
        if ctx:
            out.append((agent, "context", context_state(ctx), ctx, SYSTEM))
    return out


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    start = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.getcwd()
    if cmd == "skills":
        for name, path in skills():
            print(f"{name}\t{path}")
    elif cmd == "agents":
        for agent, here, skdir, ctx in agents(start):
            print(f"{agent}\t{here or ''}\t{skdir or ''}\t{ctx or ''}")
    elif cmd == "statusline":
        for r in statusline(start):
            print("\t".join(r))
    elif cmd == "block":
        print(block())
    elif cmd == "status":
        for r in status(start):
            print("\t".join(r))
    else:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
