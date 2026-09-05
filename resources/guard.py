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
    a state moved, nothing written → `.state/round.md` is what survives a compaction
    a `state:` written by hand   → `pearde set` checks the gate; an editor checks nothing
    the skill written from another board → the install is links into this tree; file a PRD here

It denies only what is provably redundant: a repeat whose inputs have not
changed since the first run. Everything else passes through untouched, and a
board it cannot find is not its business.
"""
import hashlib
import json
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
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
PEARDE = os.path.dirname(ROOT)          # the repo this guard ships in
# One JSON file per session. `PEARDE_GUARD_STATE` moves the directory — a
# harness feeding hook JSON to a temp project must never write here.
STATE = os.environ.get("PEARDE_GUARD_STATE") or os.path.join(
    ROOT, "board", "state", "guard")
# Duplicated from @resources/board/plan.py's own BOARD_DIR/PRDS_DIR rather
# than imported — same reason member_dirs() gives for reading settings.md by
# hand: the guard imports nothing from the planner, so a broken planner
# never blocks a tool call.
BOARD_DIR = ".pearde"
PRDS_DIR = "prds"
ROUND_FILE = os.path.join(".state", "round.md")

# The context budget. A round costs its context on every turn: 1,000 turns at
# 500k is half a billion cache-read tokens for a session whose unique content
# was 500k once. The orchestrator is meant to be slim — the board is on disk
# and `.state/round.md` is what it carries — so the budget is a ceiling, not a
# window. `context-budget` in .pearde/settings.md moves it; `off` removes it.
BUDGET_DEFAULT = 100_000
BUDGET_WARN = 0.70          # note once at 70%, once at 85%
BUDGET_KEY = re.compile(r"^context-budget:[ \t]*(\S+)", re.M)
# What stays allowed at the ceiling — everything the restart itself needs.
ESCAPE = re.compile(r"\.round\.md$|/(loop|round)\.md$")

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

# A walk carried as data is not a walk. The shell never runs a heredoc body
# or the inside of a quoted string — a script piped to python, a fixture, a
# refusal quoted into a memo. It does run the string a walker itself takes
# (`grep -r 'state:'`) and the one `sh -c` is given. `data_free` returns the
# command with the data blanked, and the WALKS rules match on that.
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n(.*?)\n\2[ \t]*(?=\n|$)",
                     re.S)
RUNS_ITS_STRING = {"find", "grep", "rg", "ls", "sh", "bash", "zsh", "eval"}


def data_free(cmd):
    """`cmd` with heredoc bodies and quoted strings blanked, except a string
    given to a command that runs it."""
    cmd = HEREDOC.sub(lambda m: m.group(0)[:m.start(3) - m.start(0)]
                      + "\n" + m.group(2), cmd)
    out, i, n, word = [], 0, len(cmd), ""
    at_start = True
    while i < n:
        c = cmd[i]
        if c in "|;&\n":
            at_start, word = True, ""
            out.append(c); i += 1
            continue
        if c in "'\"":
            j = i + 1
            while j < n and cmd[j] != c:
                j += 2 if (c == '"' and cmd[j] == "\\") else 1
            keep = word in RUNS_ITS_STRING
            out.append(cmd[i:j + 1] if keep else " ")
            i = j + 1
            continue
        if at_start and not c.isspace():
            m = re.match(r"[\w./-]+", cmd[i:])
            tok = m.group(0) if m else c
            if m and cmd[i + len(tok):i + len(tok) + 1] == "=":
                m = re.match(r"\S+", cmd[i:])      # `X=1` — a prefix, whole
                out.append(m.group(0)); i += len(m.group(0))
                continue
            word = os.path.basename(tok)
            if word in ("sudo", "env", "command", "time", "exec", "nice"):
                word = ""          # a prefix — the next word is the command
            else:
                at_start = False
            out.append(tok); i += len(tok)
            continue
        out.append(c); i += 1
    return "".join(out)


# Commands that only look. A repeat of one of these over an unchanged board
# returns the bytes it returned last time, which is the whole argument for
# refusing it.
READERS = {"find", "grep", "rg", "ls", "cat", "head", "tail", "wc", "sed",
           "awk", "stat", "file", "tree", "diff", "python3", "python"}
WRITERS = re.compile(r"(^|[|;&]\s*)(rm|mv|cp|mkdir|touch|tee|install|chmod)\b"
                     r"|>>?|\bgit\s+(add|commit|checkout|reset|rm|mv|stash)\b")


_GITBASH_DRIVE_RE = re.compile(r"^/([A-Za-z])(/.*)?$")


def board_of(start):
    """The nearest ancestor holding `.pearde/`, or None — the same walk
    @resources/board/plan.py `find_board` does, so the guard and `scan` name
    the same board from the same cwd. The guard has no opinion about a
    directory that is not a board."""
    start = start or os.getcwd()
    if os.name == "nt":
        # Git Bash's own `cwd` (and `pwd`/`dirname` output doctor.sh builds
        # from it) is POSIX-style, `/c/Users/...` — os.path.abspath under a
        # native Windows interpreter does not read that as a drive letter,
        # it prepends the current drive instead: `/c/Users/...` becomes
        # `C:\c\Users\...`, a path that never exists, so `.pearde/` is
        # never found and the guard silently no-ops on every real Bash tool
        # call.
        m = _GITBASH_DRIVE_RE.match(start)
        if m:
            start = f"{m.group(1)}:{m.group(2) or '/'}"
    d = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(d, BOARD_DIR)):
            return os.path.join(d, BOARD_DIR)
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def prds_dir(board):
    return os.path.join(board, PRDS_DIR)


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


# ── the skill tree ────────────────────────────────────────────────────────────
# The install is links into this repo (@references/install.md), so a round on
# any board on the machine that edits the skill edits this working tree —
# .pearde/memos/the-install-is-live-symlinks.md counts what that cost. A write
# under the skill root from a session whose board is another repo's is
# refused; the same repo, or no board in scope, passes as before.
SKILL = os.path.realpath(PEARDE)
MEMO = ".pearde/memos/the-install-is-live-symlinks.md"


def skill_file(path):
    """The real path of a file in this skill's own tree, reached through any
    install link or by name — or "". The board under it is not the skill:
    its `.pearde/prds/` is where another board files a PRD, which is the way in."""
    real = os.path.realpath(path)
    if not real.startswith(SKILL + os.sep):
        return ""
    if real.startswith(os.path.join(SKILL, BOARD_DIR, PRDS_DIR) + os.sep):
        return ""
    return real


def another_boards_write(inp, cwd):
    """`Edit|Write` into the skill tree from a round on another board —
    refused, naming the real path the link resolves to, the memo, and the
    two ways out. The session's board is the nearest `.pearde/` above its
    working directory, as `find_board` reads it; none, or this repo's own,
    and the write is not this rule's business."""
    given = str(inp.get("file_path") or "")
    real = skill_file(given)
    if not real:
        return
    board = board_of(cwd)
    if not board or os.path.realpath(os.path.dirname(board)) == SKILL:
        return
    via = (f"{given} resolves to {real}" if os.path.abspath(given) != real
           else real)
    deny(f"A round on another board does not write the skill: {via} — the "
         f"pearde working tree — and this session's board is {board}. The "
         f"install is links into that tree — {MEMO} — so the edit would land "
         "uncommitted among hunks the sessions on that board are staging. "
         "Two ways out: file a PRD on the skill's own board (`pearde add "
         f"\"<title>\"` from {SKILL}), or hand the edit to a session "
         "working it.")


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
    rel = os.path.relpath(os.path.dirname(path), prds_dir(board))
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


def budget_of(board):
    """`context-budget` off .pearde/settings.md, in tokens. `off`/`0` disables
    it. A bare number is tokens; `120k` is 120,000."""
    try:
        text = open(os.path.join(board, "settings.md"), encoding="utf-8",
                    errors="replace").read()
    except OSError:
        return BUDGET_DEFAULT
    m = BUDGET_KEY.search(text)
    if not m:
        return BUDGET_DEFAULT
    v = m.group(1).strip().lower()
    if v in ("off", "none", "0"):
        return 0
    try:
        return int(float(v[:-1]) * 1000) if v.endswith("k") else int(float(v))
    except ValueError:
        return BUDGET_DEFAULT


def context_now(data):
    """The window this turn was billed for, off the transcript's last
    assistant usage. 0 when there is no transcript to read — the guard never
    guesses a number it would then refuse on."""
    path = data.get("transcript_path") or ""
    if not path or not os.path.isfile(path):
        return 0
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - 262144))
            tail = fh.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return 0
    for line in reversed(tail):
        line = line.strip()
        if not line.startswith("{") or '"usage"' not in line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") != "assistant":
            continue
        u = ((d.get("message") or {}).get("usage")) or {}
        n = (u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
             + u.get("cache_creation_input_tokens", 0))
        if n:
            return n
    return 0


def dispatched(data):
    """True when this tool call belongs to a worker the orchestrator sent
    out, not the round's own turn. session_id and transcript_path are the
    SAME file for every worker and the orchestrator alike — the hook payload
    shares one session across a whole round — so they cannot tell one from
    the other. `agent_id`/`agent_type` can: the orchestrator's own tool
    calls carry neither; a dispatched analyst, implementer or any other
    subagent carries both. Confirmed empirically, not from documentation —
    see the PRD's report."""
    return bool(data.get("agent_id") or data.get("agent_type"))


def budget(data, st, session, board, tool, inp):
    """Refuse the round that outgrew its own ceiling. Everything the restart
    needs stays open: the scan, the round file, and the two files that say
    what a restart is.

    Dispatched-only: a worker's own window is not the round's ceiling, so a
    session carrying `agent_id`/`agent_type` never reaches the cap check, the
    70%/85% notes, or the ESCAPE bypass below — which is also what keeps a
    worker from ever being told, by the ceiling's own deny text, to write
    the round file that is not its own."""
    if dispatched(data):
        return
    cap = budget_of(board)
    if not cap:
        return
    ctx = context_now(data)
    if not ctx:
        return
    if ctx < cap:
        band = 0.85 if ctx >= cap * 0.85 else (
            BUDGET_WARN if ctx >= cap * BUDGET_WARN else 0)
        if band and st.get("budget_band", 0) < band:
            st["budget_band"] = band
            save(session, st)
            note(f"Context {ctx // 1000}k of the {cap // 1000}k budget. Every "
                 "turn from here re-reads all of it. Write .state/round.md now "
                 "— what is established, decided, asked and owed — so the "
                 "restart at the ceiling costs one scan and not a re-derivation.")
        return
    path = str(inp.get("file_path") or "")
    if tool in ("Edit", "Write", "Read") and ESCAPE.search(path):
        return
    if tool == "Bash" and TOOLS.search(str(inp.get("command") or "")):
        return
    if tool in ("TodoWrite", "AskUserQuestion"):
        return
    deny(f"Context is {ctx // 1000}k, over the {cap // 1000}k budget — this "
         "round has stopped being cheap to continue.\nEvery turn now bills "
         f"{ctx // 1000}k of cache read for work the board already holds on "
         "disk.\n\nEnd the round: write .state/round.md whole — established, "
         "decided, asked, edits, owed — and say to the user that the round is "
         "at its budget and the next one resumes from that file. A fresh "
         f"session reads it, runs `{SCAN}`, and is where this one is for "
         "one percent of the window.\n\nStill allowed: the round file, "
         "references/parts/loop.md, references/parts/round.md, and the "
         "board's own commands.")


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
    budget(data, st, session, board, tool, inp)
    if tool in ("Edit", "Write"):
        another_boards_write(inp, data.get("cwd"))
        state_by_hand(tool, inp)
        ok()

    if tool == "Bash":
        cmd = str(inp.get("command") or "")
        if any(w.search(data_free(cmd)) for w in WALKS):
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
                 "already have.\nCite it from .state/round.md instead, or write "
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
                     ".state/round.md. The steps themselves are the exception: "
                     "references/parts/loop.md and references/parts/round.md "
                     "are always readable.")
            deny(f"Third read of this file, unchanged since {clock(prev['at'])}"
                 " — you have read it twice already and nothing has written to "
                 "it since.\nWhat you needed from it belongs in .state/round.md; "
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
    import tempfile
    repo = repo_of(args)
    path = settings_of(repo)
    # both probes keep their guard state in a temp dir — a probe carries no
    # session, and its block would otherwise land as nosession.json in the
    # real state dir on every status call
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "PEARDE_GUARD_STATE": os.path.join(tmp, "state")}
        probe = json.dumps({"tool_name": "Bash", "cwd": repo,
                            "tool_input": {"command": "find prds -name prd.md"}})
        out = subprocess.run([sys.executable, SELF, "pre"], input=probe,
                             capture_output=True, text=True, env=env).stdout
        if '"deny"' not in out:
            print(ROW % ("guard", "broken",
                         f"{SELF} does not refuse a hand-walked board"))
            return 2
        # the second rule, proved the same way: an Edit of this file from a
        # board that is not this repo's — a temp one holding an empty .pearde/
        os.makedirs(os.path.join(tmp, BOARD_DIR))
        probe = json.dumps({"tool_name": "Edit", "cwd": tmp,
                            "tool_input": {"file_path": SELF,
                                           "old_string": "a", "new_string": "b"}})
        out = subprocess.run([sys.executable, SELF, "pre"], input=probe,
                             capture_output=True, text=True, env=env).stdout
    if '"deny"' not in out:
        print(ROW % ("guard", "broken",
                     f"{SELF} does not refuse a write into the skill tree "
                     "from another board"))
        return 2
    _, text = read_settings(path)
    if "guard.py" in text:
        m = re.search(r'MAX_THINKING_TOKENS"\s*:\s*"(\d*)', text)
        tk = f" · MAX_THINKING_TOKENS={m.group(1)}" if m and m.group(1) else ""
        print(ROW % ("guard", "ok", f"wired in {path}{tk} · skill tree guarded"))
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
