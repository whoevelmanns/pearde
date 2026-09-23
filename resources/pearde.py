#!/usr/bin/env python3
"""pearde — the board's one command. Every tool is a subcommand of it.

    pearde                    the board on one page — the same as `scan`
    pearde <cmd> [args…]      one command; the board argument is optional everywhere
    pearde <cmd> --help       that command's line and the flags it takes, exit 0
    pearde help               one line per command

A dispatcher, not a home. No logic lives here: each name forwards to the
script that owns it, arguments in the order that script takes them, exit
code passed through. The board is resolved by the script that reads it, the
way @resources/board/plan.py `find_board` does — the path given, or the
nearest `prds/` walking up from the working directory.

Discovery. Every `resources/board/*.py` that exposes
`COMMANDS = {"<name>": <callable>}` is imported and its names are routed. A
callable takes the argument list after the name and returns the exit code
(`None` reads as 0); its docstring's first line is the `help` line, and its
`flags` attribute — the declaration @resources/board/transitions.py `Args`
parses — is the `takes:` line under `--help`, so the two cannot drift. A
child adds a module; nothing edits this file. A name two modules claim, or a name
this file already forwards, is refused: `help` prints the clash and exits 1,
and `doctor` reports that under `skills`.

The names that arrive with later children are reserved here and answer
`not yet — <child>` until a module claims them.

Python 3 stdlib only.
"""
import glob
import importlib.util
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def skill_root():
    """The repo this file belongs to: the nearest ancestor holding
    `resources/board/plan.py`. Works from `resources/pearde.py` and from a
    probe copy alike."""
    d = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.isfile(os.path.join(d, "resources", "board", "plan.py")):
            return d
        nxt = os.path.dirname(d)
        if nxt == d:
            print("pearde: no resources/board/plan.py above this file",
                  file=sys.stderr)
            sys.exit(2)
        d = nxt


ROOT = skill_root()
RES = os.path.join(ROOT, "resources")
BOARD_PY = os.path.join(RES, "board")

# The contract table of @prds/the-board-runs-itself/one-command/prd.md, one
# row per name pearde forwards. `script` is under resources/; `verbs` are the
# words the script takes first — when the first argument is one of them the
# arguments go through untouched, otherwise `prefix` is put in front. A row
# with no verbs always gets its prefix.
FORWARD = {
    "scan":      ("board/plan.py", ["scan"], ()),
    "plan":      ("board/plan.py", ["plan"], ()),
    "reconcile": ("board/plan.py", ["reconcile"], ()),
    "gantt":     ("board/plan.py", ["gantt"], ()),
    "calibrate": ("board/plan.py", ["calibrate"], ()),
    "status":    ("board/plan.py", ["status"], ()),
    "members":   ("board/plan.py", ["members"], ()),
    "view":      ("board/serve.py", ["ensure"],
                  ("ensure", "status", "stop", "wait", "forget", "run")),
    "memo":      ("memos.py", [], ("list", "check", "add")),
    "workflow":  ("workflows.py", [], ("list", "show", "brief", "check")),
    "questions": ("questions.py", ["check"], ("check", "list")),
    "index":     ("index.py", ["check"],
                  ("check", "files", "keywords", "scope")),
    "guard":     ("guard.py", ["status"], ("on", "off", "status")),
    "doctor":    ("doctor.sh", [], ()),
    "install":   ("install.sh", [], ()),
}

# Reserved: a name a later child delivers, answering `not yet — <child>`
# until a module claims it. Empty today — every name the tree named has its
# module. Discovery wins over this table, so a row is never removed by hand
# when a module lands; it is removed when the child's PRD is `done`.
RESERVED = {}

WIDTH = 80


# ── discovery ─────────────────────────────────────────────────────────────────

COMMANDS_RE = re.compile(r"^COMMANDS\s*=", re.M)


def discover():
    """(commands, problems). commands: name -> (module basename, callable).
    Only a module whose source says `COMMANDS =` is imported — importing
    plan.py or serve.py to find out they have none would cost every call."""
    found, problems = {}, []
    for path in sorted(glob.glob(os.path.join(BOARD_PY, "*.py"))):
        try:
            src = open(path, encoding="utf-8").read()
        except OSError as e:
            problems.append(f"{os.path.basename(path)}: {e}")
            continue
        if not COMMANDS_RE.search(src):
            continue
        mod = os.path.basename(path)[:-3]
        try:
            spec = importlib.util.spec_from_file_location(f"pearde_{mod}", path)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
        except Exception as e:  # a broken child must not take the rest down
            problems.append(f"{mod}.py failed to import: {e}")
            continue
        cmds = getattr(m, "COMMANDS", None)
        if not isinstance(cmds, dict):
            problems.append(f"{mod}.py: COMMANDS is not a dict")
            continue
        for name, fn in cmds.items():
            if not callable(fn):
                problems.append(f"{mod}.py: COMMANDS[{name!r}] is not callable")
                continue
            if name in FORWARD:
                problems.append(f"`{name}` is forwarded by pearde.py and "
                                f"claimed by {mod}.py")
                continue
            if name in found:
                problems.append(f"`{name}` is claimed by both "
                                f"{found[name][0]}.py and {mod}.py")
                continue
            found[name] = (mod, fn)
    return found, problems


# ── help, from docstrings ─────────────────────────────────────────────────────

USAGE_RE = re.compile(r"^\s*(?:python3\s+|bash\s+)?(?:@?[\w./-]*/)?(\w+\.(?:py|sh))\s+(\S.*)$")


def docstring(script):
    """A .py's module docstring, or a .sh's leading `#` block."""
    path = os.path.join(RES, script)
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return ""
    if script.endswith(".sh"):
        out = []
        for line in text.splitlines()[1:]:
            if not line.startswith("#"):
                break
            out.append(line[1:])
        return "\n".join(out)
    m = re.search(r'"""(.*?)"""', text, re.S)
    return m.group(1) if m else ""


def split_usage(rest):
    """`plan  [board] [--workers N]   the frontier` → (verb, args, desc).
    The verb is a bare first word; the arguments are the `[…]`, `<…>` and
    `--flag` tokens after it, a bracket group kept whole; what follows is
    the description. Whitespace is not the separator — the docstrings do not
    agree on how many spaces sit before a description."""
    toks, depth, cur = [], 0, ""
    for ch in rest:
        if ch.isspace() and depth == 0:
            if cur:
                toks.append(cur)
            cur = ""
            continue
        depth += ch in "[<"
        depth -= ch in "]>"
        cur += ch
    if cur:
        toks.append(cur)
    verb, args, i = "", [], 0
    if toks and re.fullmatch(r"[a-z][\w-]*", toks[0]):
        verb, i = toks[0], 1
    while i < len(toks) and toks[i][:1] in "[<-":
        args.append(toks[i])
        i += 1
    return verb, " ".join(args), " ".join(toks[i:])


def usage_lines(script):
    """[(verb, args, description)] from the docstring: a usage line names
    the script, and the indented lines under it continue its description."""
    base = os.path.basename(script)
    rows = []
    for line in docstring(script).splitlines():
        m = USAGE_RE.match(line)
        if m and m.group(1) == base:
            rows.append(list(split_usage(m.group(2))))
        elif rows and line.startswith(" " * 16) and line.strip():
            rows[-1][2] += " " + line.strip()
        elif rows and not line.strip():
            break
    return [tuple(r) for r in rows]


def title_line(script):
    """`pearde plan — the board, read and ordered.` → after the dash."""
    first = docstring(script).strip().splitlines()[:1]
    if not first:
        return ""
    return re.sub(r"^.*?—\s*", "", first[0]).rstrip(".")


def fit(left, desc):
    line = f"  {left:<28} {desc}".rstrip()
    if len(line) <= WIDTH:
        return line
    cut = line[:WIDTH - 1]
    return cut[:cut.rfind(" ")] + "…"


def help_lines(name):
    """The `help` lines for one name: one per verb where the script has
    verbs, one per usage row where it has none, one for the forwarded verb
    otherwise. A verb the docstring does not list gets the script's title."""
    if name not in FORWARD:
        return []
    script, prefix, verbs = FORWARD[name]
    rows = usage_lines(script)
    title = title_line(script)
    out = []
    if verbs:
        for v in verbs:
            _, args, desc = next((r for r in rows if r[0] == v),
                                 (v, "", title))
            shown = (f"pearde {name}" if prefix and v == prefix[0]
                     else f"pearde {name} {v}")
            out.append(fit(f"{shown} {args}".rstrip(), desc))
        return out
    if prefix:
        _, args, desc = next((r for r in rows if r[0] == prefix[0]),
                             ("", "", title))
        return [fit(f"pearde {name} {args}".rstrip(), desc)]
    for _, args, desc in rows or [("", "", title)]:
        out.append(fit(f"pearde {name} {args}".rstrip(), desc))
    return out


def cmd_help(found, problems):
    print("pearde — the board's one command; every tool is a subcommand")
    print()
    print(fit("pearde", "the board on one page — `scan`"))
    for name in FORWARD:
        for line in help_lines(name):
            print(line)
    for name, (mod, fn) in sorted(found.items()):
        doc = (fn.__doc__ or "").strip().splitlines()[:1]
        print(fit(f"pearde {name}", doc[0] if doc else f"{mod}.py"))
    for name, child in RESERVED.items():
        if name not in found:
            print(fit(f"pearde {name}", f"not yet — {child}"))
    print(fit("pearde help", "this list"))
    if problems:
        for p in problems:
            print(f"pearde: {p}", file=sys.stderr)
        return 1
    return 0


# ── forwarding ────────────────────────────────────────────────────────────────

def run(script, args):
    path = os.path.join(RES, script)
    cmd = (["bash", path] if script.endswith(".sh")
           else [sys.executable, path]) + list(args)
    try:
        return subprocess.call(cmd)
    except KeyboardInterrupt:
        return 130


def forward(name, args):
    script, prefix, verbs = FORWARD[name]
    if args and verbs and args[0] in verbs:
        return run(script, args)
    return run(script, prefix + args)


def cmd_view(args):
    """`view` is `serve.py ensure`, then the URL it printed is opened. The
    other verbs pass through. `--no-open` keeps the browser shut — a harness
    wants the registration, not a window."""
    if args and args[0] in FORWARD["view"][2]:
        return run("board/serve.py", args)
    want_open = "--no-open" not in args
    rest = [a for a in args if a != "--no-open"]
    path = os.path.join(RES, "board", "serve.py")
    p = subprocess.run([sys.executable, path, "ensure"] + rest,
                       capture_output=True, text=True)
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    if p.returncode != 0:
        return p.returncode
    m = re.search(r"https?://\S+", p.stdout)
    if m and want_open:
        import webbrowser
        webbrowser.open(m.group(0))
    return 0


# ── main ──────────────────────────────────────────────────────────────────────

def main(argv):
    args = list(argv[1:])
    found, problems = discover()
    if not args:
        return forward("scan", [])
    name, rest = args[0], args[1:]
    if name in ("help", "-h", "--help"):
        return cmd_help(found, problems)
    for p in problems:
        print(f"pearde: {p}", file=sys.stderr)
    if name in found:
        if "--help" in rest or rest[:1] == ["-h"]:
            fn = found[name][1]
            print(fit(f"pearde {name}",
                      (fn.__doc__ or "").strip().split("\n")[0]))
            flags = getattr(fn, "flags", None)
            if flags:
                print(f"  takes: {flags}")
            return 0
        rc = found[name][1](rest)
        return 0 if rc is None else int(rc)
    if name in FORWARD:
        if "--help" in rest or "-h" in rest:
            for line in help_lines(name):
                print(line)
            return 0
        if name == "view":
            return cmd_view(rest)
        return forward(name, rest)
    if name in RESERVED:
        if "--help" in rest:
            print(fit(f"pearde {name}", f"not yet — {RESERVED[name]}"))
            return 0
        print(f"not yet — {RESERVED[name]}", file=sys.stderr)
        return 1
    names = list(FORWARD) + sorted(found) + [n for n in RESERVED
                                             if n not in found]
    near = [n for n in names if n.startswith(name[:2])]
    hint = f" — did you mean {', '.join(near)}?" if near else ""
    print(f"pearde: unknown command `{name}`{hint} · `pearde help` lists them",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
