#!/usr/bin/env python3
"""pearde init — a board exists after one command, and it asked nothing.

    init.py init [<dir>] [--language <l>] [--name <n>] [--example] [--dry]
    init.py settings <key>=<value> [--board <path>] [--dry]

`init` leaves `<dir>/prds/` (default: the working directory) on the
contract: a `settings.md` naming the five knobs by name, a `vision.md` from
@references/templates/vision.md with `terminals:` commented out, the four
machine-local names in `.gitignore` when `<dir>` is inside a git repo, the
daemon up and watching the board when the port can be bound — it says so and
goes on when it cannot — and one `doctor` report, every line printed. Then
four lines: `pearde guard on — optional, …` for the hook doctor's guard row
names, the URL, `pearde add "<title>"`, `pearde`. Its first line says
the language it defaulted and the command that changes it. `--example`
copies the example board instead of writing an empty one — the quickstart's.

Idempotent: on a board that already has `settings.md` nothing is written and
the same four lines close the output. `memos/` and `workflows/` are not
made — a folder appears when its first file does.

`settings` writes one key of `prds/settings.md` through edit.py — one
frontmatter line, every other line byte for byte — and is how any key is
set, `workers=N` and `pipeline=N` included.

Both declare their flags in `FLAGS` and parse through transitions.py `Args`:
an undeclared flag is refused with the list, exit 2, before anything is
read. `--dry` prints the first line the run would print, `dry ·` in front,
and the paths it would write — and starts no daemon, runs no doctor.

`COMMANDS` is what the dispatcher discovers. Each entry takes the argument
list after the command name and returns the exit code. Python 3 stdlib only.
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)                          # the skill's resources/
SKILL = os.path.dirname(RES)
sys.path.insert(0, HERE)
import edit as editlib          # noqa: E402 — the one writer of bytes
import plan as planlib          # noqa: E402 — every read
import transitions as trlib     # noqa: E402 — the flag parser

EXAMPLE = os.path.join(HERE, "example", "prds")
VISION_TEMPLATE = os.path.join(SKILL, "references", "templates", "vision.md")
SERVE = os.path.join(HERE, "serve.py")
DOCTOR = os.path.join(RES, "doctor.sh")

# The five knobs of @references/settings.md, in the order the file shows
# them, every one written by name so a reader sees the choice on disk.
DEFAULTS = (("language", "English"), ("workers", "3"), ("pipeline", "3"),
            ("weight-default", "50"), ("gantt-day", "8h"))

# Machine-local per board — regenerable. What this repo's own .gitignore
# holds for the same names.
IGNORED = ("prds/.plan.json", "prds/.round.md", "prds/.history.jsonl",
           "prds/.view.html")

KEY_RE = re.compile(r"^[a-z][a-z0-9-]*$")


class Refused(Exception):
    """An argument the command cannot act on. Nothing was written."""


# The declaration — transitions.py `Args` is the parser.
FLAGS = {
    "init":     trlib.Flags(("language", "name"), ("example",) + trlib.DRY),
    "settings": trlib.Flags(("board",), trlib.DRY),
}


# ── init ──────────────────────────────────────────────────────────────────────

def settings_text(language, name):
    lines = ["---"]
    if name:
        lines.append(f"name: {name}")
    for k, v in DEFAULTS:
        lines.append(f"{k}: {language if k == 'language' else v}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def write_board(board, args):
    """Steps 1–3: the board directory, `settings.md` and `vision.md`. Each
    file is written only when it is not there, so a hand-made `prds/` keeps
    what it has and gains what it lacks."""
    settings = os.path.join(board, "settings.md")
    if "example" in args.flags:
        if os.path.isdir(board) and os.listdir(board):
            raise Refused(f"{board} exists and holds no settings.md — "
                          "--example copies into an empty or missing prds/")
        shutil.copytree(EXAMPLE, board, dirs_exist_ok=True)
        for key in ("language", "name"):
            if args.opt.get(key, "").strip():
                editlib.set_key(settings, key, args.opt[key].strip())
    else:
        os.makedirs(board, exist_ok=True)
        editlib.write_atomic(settings, settings_text(
            args.opt.get("language", "").strip() or "English",
            args.opt.get("name", "").strip()))
    vision = os.path.join(board, "vision.md")
    if not os.path.exists(vision):
        shutil.copyfile(VISION_TEMPLATE, vision)


def in_git(d):
    try:
        p = subprocess.run(["git", "-C", d, "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True)
    except OSError:
        return False
    return p.returncode == 0


def write_gitignore(d):
    """Step 4: the four names, appended to `<dir>/.gitignore` — the board's
    parent, where `prds/…` is the right spelling — when they are not already
    there. Returns the names it added."""
    path = os.path.join(d, ".gitignore")
    text = open(path, encoding="utf-8").read() if os.path.isfile(path) else ""
    have = {l.strip() for l in text.splitlines()}
    add = [n for n in IGNORED if n not in have]
    if not add:
        return []
    if text and not text.endswith("\n"):
        text += "\n"
    if text:
        text += "\n"
    text += "# machine-local per board — regenerable\n"
    text += "".join(n + "\n" for n in add)
    editlib.write_atomic(path, text)
    return add


def ensure(board):
    """Step 5: `serve.py ensure <board>`. Returns the URL — the daemon's own
    when it came up, the one it would have been when it did not."""
    p = subprocess.run([sys.executable, SERVE, "ensure", board],
                       capture_output=True, text=True)
    sys.stdout.write(p.stdout)
    m = re.search(r"https?://\S+/board/\S+", p.stdout)
    if p.returncode == 0 and m:
        return m.group(0)
    why = (p.stderr.strip().splitlines() or ["no daemon"])[-1]
    print(f"view: not watching — {why} · the board reads and plans "
          "without it; `pearde view` when the port is free")
    return planlib.serve_url(board)


def doctor(d):
    """Step 6: one report, every line printed. Its exit code is its own —
    a broken row is a line the reader now has, not a reason to stop."""
    sys.stdout.flush()
    subprocess.call(["bash", DOCTOR, d])


def cmd_init(argv):
    """a board that asked nothing — [<dir>] [--language <l>] [--name <n>]
    [--example]: settings, vision, .gitignore, the daemon, doctor, next."""
    args = trlib.Args(argv, FLAGS["init"], "init")
    if len(args.pos) > 1:
        raise Refused("init [<dir>] [--language <l>] [--name <n>] [--example]")
    d = os.path.abspath(args.pos[0] if args.pos else os.getcwd())
    board = os.path.join(d, "prds")
    existing = os.path.isfile(os.path.join(board, "settings.md"))
    if args.dry:
        if existing:
            language = str(planlib.board_settings(board).get(
                "language", "")).strip() or "English"
            print(f"dry · board {planlib.board_name(board)} · language "
                  f"{language} — pearde settings language=<l> changes it")
            print(f"  would write: nothing — {board}/settings.md exists")
            return 0
        language = args.opt.get("language", "").strip() or "English"
        name = args.opt.get("name", "").strip() or os.path.basename(d)
        paths = [os.path.join(board, "settings.md"),
                 os.path.join(board, "vision.md")]
        if in_git(d):
            paths.append(os.path.join(d, ".gitignore"))
        print(f"dry · board {name} · language {language} — pearde settings "
              "language=<l> changes it")
        print("  would write: " + " · ".join(paths)
              + (" from the example board" if "example" in args.flags
                 else ""))
        return 0
    if not existing:
        write_board(board, args)
    language = str(planlib.board_settings(board).get("language", "")).strip() \
        or "English"
    print(f"board {planlib.board_name(board)} · language {language} — "
          "pearde settings language=<l> changes it")
    if not existing:
        print(f"init: wrote {board}/settings.md and vision.md"
              + (" from the example board" if "example" in args.flags else ""))
        if in_git(d):
            added = write_gitignore(d)
            if added:
                print(f"init: .gitignore += {' '.join(added)}")
    url = ensure(board)
    if not existing:
        doctor(d)
    print("pearde guard on — optional, refuses the waste the loop's rules name")
    print(url)
    print('pearde add "<title>"')
    print("pearde")
    return 0


# ── settings ──────────────────────────────────────────────────────────────────

def cmd_settings(argv):
    """<key>=<value> [--board <path>] — write one key of prds/settings.md,
    every other line kept byte for byte."""
    args = trlib.Args(argv, FLAGS["settings"], "settings")
    if len(args.pos) != 1 or "=" not in args.pos[0]:
        raise Refused("settings <key>=<value>")
    key, _, value = args.pos[0].partition("=")
    key, value = key.strip(), value.strip()
    if not KEY_RE.match(key):
        raise Refused(f"`{key}` is not a key — lowercase, digits and `-`")
    if not value:
        raise Refused(f"{key}= names no value — to drop a key, edit the file")
    board = planlib.find_board(args.opt.get("board"))
    path = os.path.join(board, "settings.md")
    if not os.path.isfile(path):
        raise Refused(f"no settings.md at {board} — `pearde init` writes it")
    old = planlib.board_settings(board).get(key)
    was = f"{old} → " if old not in (None, "", []) else ""
    if args.dry:
        trlib.say_dry(board, f"settings: {key} {was}{value}", [path])
        return 0
    editlib.set_key(path, key, value)
    print(f"settings: {key} {was}{value}")
    return 0


# ── the surface ───────────────────────────────────────────────────────────────

def _command(name, fn):
    def call(argv):
        try:
            return fn(argv)
        except trlib.FlagRefused as e:
            print(f"pearde {name}: {e}", file=sys.stderr)
            return 2
        except Refused as e:
            print(f"pearde {name}: refused — {e}", file=sys.stderr)
            return 1
    call.__doc__ = fn.__doc__
    call.__name__ = name
    call.flags = FLAGS[name]        # what `pearde <name> --help` prints
    return call


COMMANDS = {"init": _command("init", cmd_init),
            "settings": _command("settings", cmd_settings)}


def main(argv):
    if len(argv) < 2 or argv[1] not in COMMANDS:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    return COMMANDS[argv[1]](argv[2:])


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main(sys.argv))
