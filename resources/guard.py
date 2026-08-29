#!/usr/bin/env python3
"""The loop's guard — the rules in @references/parts/loop.md, enforced.

    guard.py pre     PreToolUse  — reads the hook payload on stdin, allows or denies
    guard.py post    PostToolUse — reminds the round to write down what it just moved
    guard.py check   prints what the guard would say about the board it is run in
    guard.py on [<repo>]      writes the hooks block into <repo>/.claude/settings.json
    guard.py off [<repo>]     removes exactly what `on` wrote, nothing else
    guard.py status [<repo>]  doctor's guard row alone — exit 0 ok, 1 off, 2 broken

A sentence in a reference file is advice. This is the same sentence as a
mechanism: the three ways the 2026-08-27 round burned 318,584 tokens are the
three things it refuses.

    a hand-walked board          → `plan.py scan` says it in one call
    the same board read twice    → nothing changed since; the answer is unchanged
    the manual read three times  → it has not moved; the round file is the note
    a state moved, nothing written → `prds/.round.md` is what survives a compaction
    a `state:` written by hand   → `pearde set` checks the gate; an editor checks nothing

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
# One JSON file per session. `PEARDE_GUARD_STATE` moves the directory — a
# harness feeding hook JSON to a temp project must never write here.
STATE = os.environ.get("PEARDE_GUARD_STATE") or os.path.join(
    ROOT, "board", "state", "guard")
ROUND_FILE = ".round.md"

# The manual does not change mid-round, so a repeat read of one of its files
# returns the bytes already in the window. These two are the exception:
# @references/parts/round.md sends a compacted round back to the steps, and
# that has to stay possible however often it happens.
REREADABLE = {"loop.md", "round.md"}
MANUAL = ("references" + os.sep, "skills" + os.sep)

SCAN = "python3 %s/board/plan.py scan" % ROOT

# The board's own tools write through edit.py and are never refused — a
# transition repeated is a different board, and a refused one costs nothing.
TOOLS = re.compile(r"\b(pearde|plan|guard)\.py\b|resources/board/\w+\.py")
STATE_RE = re.compile(r"^state:[ \t]*(.*?)[ \t]*$", re.M)

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


# ── the count ─────────────────────────────────────────────────────────────────
# The guard sees every tool call a session makes on a board, so it is the one
# place the round's cost can be counted without a second hook. Per board,
# under `boards` in the session file: `calls`, `reads`, `bash`, `edits` and
# `refused` — counted since the session first saw the board — `since`, the
# time of the last transition, `transitions`, how many there were, and
# `mark`: the counters as they stood at that transition, with `tokens`, the
# transcript's output-token sum then. A row's count is counter minus mark;
# "reset" is the mark moving, so `status` still has the session's totals.
# transitions.py `hand_over` writes the row and moves the mark; plan.py
# `status` prints the block.
COUNTERS = ("calls", "reads", "bash", "edits", "refused")
KIND = {"Read": "reads", "Bash": "bash", "Edit": "edits", "Write": "edits"}
_LIVE = {}      # session, st, board — set by `count`, read by `deny`


def block_of(st, board):
    boards = st.setdefault("boards", {})
    b = boards.setdefault(os.path.realpath(board), {})
    for k in COUNTERS:
        b.setdefault(k, 0)
    b.setdefault("since", time.time())
    b.setdefault("transitions", 0)
    b.setdefault("mark", {})
    return b


def count(session, st, board, tool, data):
    """One call seen on `board`: `calls` and the tool's own counter move, and
    the transcript path is kept so a transition can price the window."""
    b = block_of(st, board)
    b["calls"] += 1
    if tool in KIND:
        b[KIND[tool]] += 1
    if data.get("transcript_path"):
        st["transcript"] = str(data["transcript_path"])
    save(session, st)
    _LIVE.update(session=session, st=st, board=board)


def deny(reason):
    if _LIVE:
        block_of(_LIVE["st"], _LIVE["board"])["refused"] += 1
        save(_LIVE["session"], _LIVE["st"])
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


def fm_state(text):
    """The `state:` value of a frontmatter block, or None."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    m = STATE_RE.search(text[3:end] if end > 0 else "")
    return m.group(1) if m else None


def after_edit(path, tool, inp):
    """(before, after): the file's text now, and as the tool would leave it.
    `after` is None when the input does not say."""
    try:
        cur = open(path, encoding="utf-8").read()
    except OSError:
        cur = ""
    if tool == "Write":
        return cur, str(inp.get("content") or "")
    old, new = inp.get("old_string"), inp.get("new_string")
    if old is None or new is None or old not in cur:
        return cur, None
    return cur, (cur.replace(old, new) if inp.get("replace_all")
                 else cur.replace(old, new, 1))


def state_by_hand(tool, inp):
    """`Edit|Write` on a `prd.md` that changes its `state:` line — refused,
    naming the command. A body edit passes; the round file reminder is
    `post`'s. `transitions.py` writes through edit.py, never through a
    tool, so it is never here."""
    path = os.path.abspath(str(inp.get("file_path") or ""))
    if os.path.basename(path) != "prd.md":
        return
    board = board_of(os.path.dirname(path))
    if not board:
        return
    before, after = after_edit(path, tool, inp)
    if after is None or fm_state(before) == fm_state(after):
        return
    rel = os.path.relpath(os.path.dirname(path), board)
    if not before:
        deny(f"A PRD is made by a command, never written by hand: "
             f"`pearde add \"<title>\"` for a new one, `pearde refine <prd> "
             f"< split` for children — each arrives `state: open` from the "
             f"template. Writing {rel}/prd.md with a `state:` of your own "
             "skips the gate every command checks.")
    deny(f"`state:` is written by the tool, never by hand — use `pearde set "
         f"{rel} {fm_state(after) or '<state>'}`: it checks the gate of "
         "@references/parts/states.md, prints the progress line and records "
         "the row; `--force` writes any transition and says so on the line. "
         "Every other transition has its own command — claim, release, "
         "answer, specced, refine, collect, sweep.")


def touches_board(cmd, board):
    return ("prds" in cmd or "prd.md" in cmd
            or os.path.basename(os.path.dirname(board)) + "/prds" in cmd)


def pre(data):
    tool = data.get("tool_name") or ""
    inp = data.get("tool_input") or {}
    session = data.get("session_id") or ""
    # an edit is counted on the board its file is in, or the cwd's when the
    # file is outside every board; everything else on the cwd's board
    board = board_of(data.get("cwd"))
    if tool in ("Edit", "Write"):
        board = board_of(os.path.dirname(os.path.abspath(
            str(inp.get("file_path") or "")))) or board
    if not board:
        ok()
    st = load(session)
    count(session, st, board, tool, data)
    if tool in ("Edit", "Write"):
        state_by_hand(tool, inp)
        ok()

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
        if TOOLS.search(cmd):
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


# ── the command ───────────────────────────────────────────────────────────────
# `pearde guard on` is the reader asking for the block below in their own
# settings file — doctor never writes one. `<repo>` defaults to the repo the
# nearest board is in. The edit keeps every other key and its order, adds
# only what is missing, and says each line it added; `off` removes exactly
# those and leaves the env key, an emptied event list dropped and `hooks`
# itself kept. A file that is not JSON is refused untouched.
SELF = os.path.realpath(__file__)
THINK = "8000"
HOOKS = (("PreToolUse", "Bash|Read", "pre"),
         ("PreToolUse", "Edit|Write", "pre"),
         ("PostToolUse", "Edit|Write", "post"))
ROW = "  %-11s %-7s %s"          # doctor.sh's row(), byte for byte


class Refused(Exception):
    pass


def repo_of(args):
    if args:
        d = os.path.abspath(args[0])
        if not os.path.isdir(d):
            raise Refused(f"{args[0]} is not a directory")
        return d
    board = board_of(os.getcwd())
    if not board:
        raise Refused("no board above " + os.getcwd()
                      + " — name the repo: pearde guard on <repo>")
    return os.path.dirname(board)


def settings_of(repo):
    return os.path.join(repo, ".claude", "settings.json")


def read_settings(path):
    """(data, text) — {} and "" when the file is absent."""
    try:
        text = open(path, encoding="utf-8").read()
    except FileNotFoundError:
        return {}, ""
    try:
        data = json.loads(text)
    except ValueError as e:
        raise Refused(f"{path} is not JSON ({e}) — nothing written")
    if not isinstance(data, dict):
        raise Refused(f"{path} is not a JSON object — nothing written")
    return data, text


def write_settings(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def hook_cmd(mode):
    return f"python3 {SELF} {mode}"


def is_guard(hook, mode):
    return (isinstance(hook, dict)
            and re.search(r"guard\.py\s+" + mode + r"\b",
                          str(hook.get("command") or "")) is not None)


def entries_of(hooks, event):
    v = hooks.get(event)
    if v is None:
        return []
    if not isinstance(v, list):
        raise Refused(f"hooks.{event} is not a list — nothing written")
    return v


def guard_on(args):
    """writes the hooks block into <repo>/.claude/settings.json, keeping every other key"""
    path = settings_of(repo_of(args))
    data, _ = read_settings(path)
    added = []
    env = data.get("env")
    if env is None:
        env = data["env"] = {}
    if not isinstance(env, dict):
        raise Refused("env is not an object — nothing written")
    if "MAX_THINKING_TOKENS" not in env:
        env["MAX_THINKING_TOKENS"] = THINK
        added.append(f'env.MAX_THINKING_TOKENS = "{THINK}"')
    hooks = data.get("hooks")
    if hooks is None:
        hooks = data["hooks"] = {}
    if not isinstance(hooks, dict):
        raise Refused("hooks is not an object — nothing written")
    for event, matcher, mode in HOOKS:
        entries = entries_of(hooks, event)
        have = [h for e in entries if isinstance(e, dict)
                and e.get("matcher") == matcher
                for h in (e.get("hooks") or []) if is_guard(h, mode)]
        if have:
            continue
        entries.append({"matcher": matcher,
                        "hooks": [{"type": "command",
                                   "command": hook_cmd(mode)}]})
        hooks[event] = entries
        added.append(f"{event} {matcher} → {hook_cmd(mode)}")
    if not added:
        print(f"guard on: {path} — already wired, nothing changed")
        return 0
    write_settings(path, data)
    print(f"guard on: {path}")
    for a in added:
        print("  + " + a)
    print("  a new settings file is read after /hooks or a restart")
    return 0


def guard_off(args):
    """removes exactly the entries `on` wrote; the env key and every other key stay"""
    path = settings_of(repo_of(args))
    data, text = read_settings(path)
    removed = []
    hooks = data.get("hooks")
    if isinstance(hooks, dict):
        for event, matcher, mode in HOOKS:
            entries = entries_of(hooks, event)
            keep = []
            for e in entries:
                own = ([h for h in e["hooks"] if is_guard(h, mode)]
                       if isinstance(e, dict) and e.get("matcher") == matcher
                       and isinstance(e.get("hooks"), list) else [])
                if not own:
                    keep.append(e)
                    continue
                removed += [f"{event} {matcher} → {h['command']}" for h in own]
                rest = [h for h in e["hooks"] if h not in own]
                if rest:
                    e["hooks"] = rest
                    keep.append(e)
            if len(keep) != len(entries):
                if keep:
                    hooks[event] = keep
                else:
                    del hooks[event]
    if not removed:
        print(f"guard off: {path} — not wired, nothing changed")
        return 0
    write_settings(path, data)
    print(f"guard off: {path}")
    for r in removed:
        print("  - " + r)
    return 0


def guard_status(args):
    """doctor's guard row, alone — ok, off or broken"""
    import subprocess
    repo = repo_of(args)
    path = settings_of(repo)
    probe = json.dumps({"tool_name": "Bash", "cwd": repo,
                        "tool_input": {"command": "find prds -name prd.md"}})
    out = subprocess.run([sys.executable, SELF, "pre"], input=probe,
                         capture_output=True, text=True).stdout
    if '"deny"' not in out:
        print(ROW % ("guard", "broken",
                     f"{SELF} does not refuse a hand-walked board"))
        return 2
    _, text = read_settings(path)
    if "guard.py" in text:
        m = re.search(r'MAX_THINKING_TOKENS"\s*:\s*"(\d*)', text)
        tk = f" · MAX_THINKING_TOKENS={m.group(1)}" if m and m.group(1) else ""
        print(ROW % ("guard", "ok", f"wired in {path}{tk}"))
        return 0
    print(ROW % ("guard", "off", f"not wired in {path}"))
    print(ROW % ("", "", "fix: pearde guard on"))
    return 1


COMMAND = {"on": guard_on, "off": guard_off, "status": guard_status}


def command(verb, args):
    try:
        return COMMAND[verb](args)
    except Refused as e:
        print(f"pearde guard {verb}: refused — {e}", file=sys.stderr)
        return 1


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
    if len(sys.argv) > 1 and sys.argv[1] in COMMAND:
        sys.exit(command(sys.argv[1], sys.argv[2:]))   # a command's error is its own
    try:
        main()
    except Exception:
        # A guard that breaks a tool call is worse than the waste it prevents.
        sys.exit(0)
