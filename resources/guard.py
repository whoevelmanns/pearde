#!/usr/bin/env python3
"""The loop's guard — the rules in @references/parts/loop.md, enforced.

    guard.py pre     PreToolUse  — reads the hook payload on stdin, allows or denies
    guard.py post    PostToolUse — reminds the round to write down what it just moved
    guard.py check   prints what the guard would say about the board it is run in

A sentence in a reference file is advice. This is the same sentence as a
mechanism: the three ways the 2026-08-27 round burned 318,584 tokens are the
three things it refuses.

    a hand-walked board          → `plan.py scan` says it in one call
    the same board read twice    → nothing changed since; the answer is unchanged
    the manual read three times  → it has not moved; the round file is the note
    a state moved, nothing written → `prds/.round.md` is what survives a compaction

It denies only what is provably redundant: a repeat whose inputs have not
changed since the first run. Everything else passes through untouched, and a
board it cannot find is not its business.
"""
import hashlib
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
PEARDE = os.path.dirname(ROOT)          # the repo this guard ships in
STATE = os.path.join(ROOT, "board", "state", "guard")
ROUND_FILE = ".round.md"

# The manual does not change mid-round, so a repeat read of one of its files
# returns the bytes already in the window. These two are the exception:
# @references/parts/round.md sends a compacted round back to the steps, and
# that has to stay possible however often it happens.
REREADABLE = {"loop.md", "round.md"}
MANUAL = ("references" + os.sep, "skills" + os.sep)

SCAN = "python3 %s/board/plan.py scan" % ROOT

# A board walked by hand. `find … prd.md`, `grep -r state:`, `ls prds/*/prd.md`
# — every spelling of the sweep step 1 stopped asking for.
WALKS = (
    re.compile(r"\bfind\b[^|;&]*\bprd\.md\b"),
    re.compile(r"\bgrep\b[^|;&]*(-\w*r\w*)[^|;&]*\bstate:"),
    re.compile(r"\bls\b[^|;&]*\bprds/[^|;&]*\*"),
)

# Commands that only look. A repeat of one of these over an unchanged board
# returns the bytes it returned last time, which is the whole argument for
# refusing it.
READERS = {"find", "grep", "rg", "ls", "cat", "head", "tail", "wc", "sed",
           "awk", "stat", "file", "tree", "diff", "python3", "python"}
WRITERS = re.compile(r"(^|[|;&]\s*)(rm|mv|cp|mkdir|touch|tee|install|chmod)\b"
                     r"|>>?|\bgit\s+(add|commit|checkout|reset|rm|mv|stash)\b")


def board_of(start):
    """The nearest ancestor holding `prds/`, or None. The guard has no opinion
    about a directory that is not a board."""
    d = os.path.abspath(start or os.getcwd())
    while True:
        if os.path.isdir(os.path.join(d, "prds")):
            return os.path.join(d, "prds")
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def member_dirs(board):
    """A master board's members, read straight out of `settings.md` — the
    guard imports nothing from the planner, so a broken planner never blocks
    a tool call."""
    out, inside = [], False
    try:
        text = open(os.path.join(board, "settings.md"), encoding="utf-8").read()
    except OSError:
        return out
    for line in text.splitlines():
        if re.match(r"\s*members:\s*$", line):
            inside = True
            continue
        if inside:
            m = re.match(r"\s*-\s+(?:([\w.-]+)\s*:\s*)?(\S+)\s*$", line)
            if not m:
                break
            path = m.group(2)
            if not os.path.isabs(path):
                path = os.path.normpath(os.path.join(board, path))
            if os.path.isdir(path):
                out.append(path)
    return out


def stamp(board):
    """One number for "has anything on this board moved". The newest mtime of
    any `.md` under the board and its members — cheap enough to run on every
    tool call, exact enough that an unchanged stamp means an unchanged answer."""
    newest = 0.0
    for root_dir in [board] + member_dirs(board):
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".")
                       and d not in ("__pycache__", "node_modules")]
            for f in files:
                if not f.endswith(".md"):
                    continue
                try:
                    newest = max(newest, os.stat(os.path.join(root, f)).st_mtime)
                except OSError:
                    pass
    return round(newest, 3)


def state_path(session):
    os.makedirs(STATE, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_-]", "", session or "nosession")[:64] or "x"
    return os.path.join(STATE, safe + ".json")


def load(session):
    try:
        return json.load(open(state_path(session), encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save(session, data):
    try:
        with open(state_path(session), "w", encoding="utf-8") as fh:
            json.dump(data, fh)
    except OSError:
        pass


def clock(t):
    return time.strftime("%H:%M:%S", time.localtime(t))


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason}}))
    sys.exit(0)


def note(reason, event="PreToolUse"):
    out = {"hookSpecificOutput": {"hookEventName": event,
                                  "additionalContext": reason}}
    if event == "PreToolUse":
        out["hookSpecificOutput"]["permissionDecision"] = "allow"
        out["hookSpecificOutput"]["permissionDecisionReason"] = reason
    print(json.dumps(out))
    sys.exit(0)


def ok():
    sys.exit(0)


def reads_only(cmd):
    if WRITERS.search(cmd):
        return False
    for seg in re.split(r"[|;&]+", cmd):
        seg = seg.strip()
        if not seg:
            continue
        head = seg.split()[0]
        head = os.path.basename(head)
        if head in ("cd", "echo", "sort", "uniq", "cut", "xargs", "test", "["):
            continue
        if head not in READERS and head != "git":
            return False
        if head == "git" and not re.search(r"\bgit\s+(status|log|diff|show|"
                                           r"ls-files|rev-parse|branch)\b", seg):
            return False
    return True


def manual(path):
    """A file of this skill's own reference tree, reached through any install
    link — the links are what an install builds, so the real path is the only
    identity that holds."""
    real = os.path.realpath(path)
    if not real.startswith(PEARDE + os.sep):
        return ""
    rest = real[len(PEARDE) + 1:]
    if rest.startswith(MANUAL) or rest in ("README.md", "index.md", "SKILL.md"):
        return real
    return ""


def touches_board(cmd, board):
    return ("prds" in cmd or "prd.md" in cmd
            or os.path.basename(os.path.dirname(board)) + "/prds" in cmd)


def pre(data):
    tool = data.get("tool_name") or ""
    inp = data.get("tool_input") or {}
    board = board_of(data.get("cwd"))
    if not board:
        ok()
    session = data.get("session_id") or ""
    st = load(session)

    if tool == "Bash":
        cmd = str(inp.get("command") or "")
        if any(w.search(cmd) for w in WALKS):
            deny("The board is not walked by hand — loop step 1 is one call:\n"
                 f"    {SCAN}\n"
                 "It returns every state, gate, claim and acceptance count on "
                 "one page, including what this command was looking for.")
        # `scan` is the thing this guard sends you to. A round that lost its
        # context to a compaction has to be able to ask again, and the board
        # not having moved is exactly when the answer is cheapest.
        if "plan.py" in cmd or "guard.py" in cmd:
            ok()
        if not (touches_board(cmd, board) and reads_only(cmd)):
            ok()
        key = "b" + hashlib.sha1(cmd.encode()).hexdigest()[:16]
        now = stamp(board)
        prev = st.get(key)
        if prev and prev.get("stamp") == now:
            deny(f"You ran this at {clock(prev['at'])} and nothing on the board "
                 "has changed since — the output is byte-for-byte what you "
                 "already have.\nCite it from prds/.round.md instead, or write "
                 "it there now if it is not in it.")
        st[key] = {"at": time.time(), "stamp": now}
        save(session, st)
        ok()

    if tool == "Read":
        path = os.path.abspath(str(inp.get("file_path") or ""))
        ref = manual(path)
        if ref:
            if os.path.basename(ref) in REREADABLE:
                ok()
            path = ref
        elif not path.startswith(os.path.dirname(board)):
            ok()
        try:
            mtime = round(os.stat(path).st_mtime, 3)
        except OSError:
            ok()
        key = "r" + hashlib.sha1(path.encode()).hexdigest()[:16]
        prev = st.get(key) or {}
        n = prev.get("n", 0)
        if n >= 2 and prev.get("mtime") == mtime:
            if ref:
                deny(f"Third read of this reference, unchanged since "
                     f"{clock(prev['at'])} — the manual does not move while a "
                     "round runs.\nWhat you needed from it belongs in "
                     "prds/.round.md. The steps themselves are the exception: "
                     "references/parts/loop.md and references/parts/round.md "
                     "are always readable.")
            deny(f"Third read of this file, unchanged since {clock(prev['at'])}"
                 " — you have read it twice already and nothing has written to "
                 "it since.\nWhat you needed from it belongs in prds/.round.md; "
                 f"board state comes from `{SCAN}`.")
        st[key] = {"n": n + 1, "at": time.time(), "mtime": mtime}
        save(session, st)
        if re.search(r"/specs/[^/]+\.md$", path) and n == 0:
            note("Acceptance boxes are counted for you — `boxes c/t` in "
                 f"`{SCAN}`. Read the spec for its contract, never to count.")
        ok()
    ok()


def post(data):
    inp = data.get("tool_input") or {}
    path = str(inp.get("file_path") or "")
    if os.path.basename(path) != "prd.md":
        ok()
    board = board_of(os.path.dirname(path))
    if not board:
        ok()
    rf = os.path.join(board, ROUND_FILE)
    try:
        moved = os.stat(path).st_mtime
    except OSError:
        ok()
    try:
        written = os.stat(rf).st_mtime
    except OSError:
        written = 0
    if written >= moved:
        ok()
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext":
            f"A PRD moved and {rf} has not been rewritten since. The round "
            "file is what survives the next compaction: what was established "
            "and when, what was decided, what is out to the user, what is "
            "owed. Rewrite it whole with this transition in it."}}))
    ok()


def check():
    board = board_of(os.getcwd())
    if not board:
        print("guard: no board above " + os.getcwd())
        return
    print(f"guard: {board}\n  stamp {stamp(board)}\n  state {STATE}\n"
          f"  scan  {SCAN}")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "pre"
    if mode == "check":
        return check()
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        sys.exit(0)
    if mode == "post":
        return post(data)
    return pre(data)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # A guard that breaks a tool call is worse than the waste it prevents.
        sys.exit(0)
