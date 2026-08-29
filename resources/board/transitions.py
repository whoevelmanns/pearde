#!/usr/bin/env python3
"""pearde transitions — the orchestrator chooses, the tool moves the state.

    transitions.py add <title> [--priority N] [--body -] [--parent <prd>]
    transitions.py claim <prd> <worker>
    transitions.py release <prd> <state>
    transitions.py answer <prd> Q<n> "<text>"
    transitions.py defer <prd>
    transitions.py retry <prd>
    transitions.py unblock <prd>
    transitions.py set <prd> <state> [--force] [--worker <worker>]
    transitions.py sweep [--apply]

Every command: `--board <path>` names the board (default: walk up from the
cwd). `--as <id>` is the persona on the progress line, else `PEARDE_AS` from
the environment, else the command refuses — the line is the only record of
the persona, and a default would rewrite it. `add` is the one exception: a
new PRD has no earlier line to rewrite, so with neither it files the PRD
`· as engineer (default)` and says so on the line.

Every command checks the gate @references/parts/states.md names, writes
through edit.py — one frontmatter line at a time, atomically — prints the
progress line of @references/parts/progress.md with every term computed here,
appends `{"t","prd","from","to"}` to `prds/.transitions.jsonl` — never to
`.history.jsonl`, the daemon's burn-down — and exits 1 with the gate named
when refused, writing nothing.

`claim` also records the claim's baseline — `prds/.claims/<prd>/`, through
collect.py `snapshot()` — and `answer` lists the `prd.md` it wrote in
`prds/.claims/riders`, through `owe()`: board state written between
transitions rides the next collect. A line printed from a shell ends
`round file owed`: the round file is rewritten at every transition, and
no hook sees a command.

`sweep` lists every held claim `plan.py` `silent_of` calls silent — no
file of the PRD's has moved for `claim-ttl` — and `--apply` moves
`analyzing → open` and `claimed → failed`, never one `prds/.round.md`
names, never an analyst whose specs are on disk.

`COMMANDS` is what the dispatcher discovers. Each entry takes the argument
list after the command name and returns the exit code.

Python 3 stdlib only.
"""
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # the skill's resources/
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import edit as editlib          # noqa: E402 — the only writer of bytes
import plan as planlib          # noqa: E402 — every read
import questions as qlib        # noqa: E402 — the round check `release … question` runs

TEMPLATE = os.path.join(os.path.dirname(ROOT), "references", "templates",
                        "prd.md")
TRANSITIONS_FILE = ".transitions.jsonl"

# The states of @references/parts/states.md, and the one parked state a
# handle writes. Anything else is the user's own and only `--force` writes it.
STATES = ("open", "analyzing", "refine", "question", "specced", "claimed",
          "blocked", "done", "failed")
PARKED = "deferred"

# The one command that runs with no persona named: a new PRD has no earlier
# `· as <id>` line a default could rewrite. Every other command refuses,
# naming the line `install --apply` prints beside the alias.
DEFAULT_PERSONA = "engineer"
DEFAULTS_FOR = ("add",)
INSTALL_LINE = "export PEARDE_AS=engineer"


class Refused(Exception):
    """A transition the table forbids. The message names the gate and what
    would clear it. Nothing was written."""


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


# ── reads ─────────────────────────────────────────────────────────────────────

def resolve(prds, name):
    """The rel one argument names — exact, else a unique dir name. A name
    matching nothing refuses with the near-misses, so a typo never moves a
    neighbour."""
    name = str(name).strip().strip("/")
    if name in prds:
        return name
    same = [r for r in prds if os.path.basename(r) == name]
    if len(same) == 1:
        return same[0]
    if len(same) > 1:
        raise Refused(f"`{name}` names {len(same)} PRDs — "
                      + ", ".join(same) + "; give the full path")
    near = [r for r in prds if name.lower() in r.lower()][:5]
    raise Refused(f"no PRD named `{name}`"
                  + (" — near: " + ", ".join(near) if near else ""))


def own_footprint(prd):
    _, feet = planlib.spec_data(prd)
    return feet


def section(body, name):
    """The text under the first `## <name>` heading, or None."""
    secs = planlib._h2_sections(body, name)
    return secs[0] if secs else None


def questions_of(prd):
    """Every `### Qn` id under `## Questions`, in file order."""
    ids = []
    for sec in planlib._h2_sections(prd["body"], "Questions"):
        for m in planlib.QUESTION_HEAD_RE.finditer(sec):
            q = planlib._qid(m.group(1))
            if q not in ids:
                ids.append(q)
    return ids


def answered_of(prd):
    return {a["id"] for a in planlib.answers_of(prd)}


# ── gates ─────────────────────────────────────────────────────────────────────
# One function per gate, each raising Refused with the gate named and what
# would clear it. `transition` picks the gate off the (from, to) edge.

def gate_claim(board, prds, prd):
    """`plan.dispatchable` is the gate — the one predicate the scan's ready
    band reads too, so what `scan` offers is what `claim` takes. The reason
    arrives with its gate word in front (`unclaimed:`, `leaf:`, `container:`,
    `needs:`, `footprint:`, `workflow:`) and is raised as it stands."""
    why = planlib.dispatchable(prd, prds, board)
    if why:
        raise Refused(why)


def gate_release(board, prds, prd, to):
    if to == "question":
        qs = section(prd["body"], "Questions")
        if not qs or not qs.strip():
            raise Refused("question: no `## Questions` round in the body")
        local = prd["local"]
        bad = [b for b in qlib.check(prd["board_path"])
               if b.startswith(local + ":")]
        if bad:
            raise Refused("question: questions.py check refuses the round — "
                          + "; ".join(bad))
    elif to == "blocked":
        deps = prd["fm"].get("needs", [])
        if not deps:
            raise Refused("blocked: no `needs:` naming the event it waits on")
    elif to == "failed":
        f = section(prd["body"], "Failure")
        if not f or not f.strip():
            raise Refused("failed: no `## Failure` in the body")


def gate_answered(board, prds, prd):
    qs = questions_of(prd)
    if not qs:
        raise Refused("answer: no `### Q<n>` in `## Questions`")
    left = [q for q in qs if q not in answered_of(prd)]
    if left:
        raise Refused("answer: unanswered — " + ", ".join(left))


def gate_defer(board, prds, prd):
    if planlib.claim_of(prd["fm"]):
        raise Refused(f"defer: {prd['rel']} is held — `claim: "
                      f"{prd['fm']['claim']}`; release it first")


def gate_unblock(board, prds, prd):
    deps = prd["fm"].get("needs", [])
    for d in (deps if isinstance(deps, list) else [deps]):
        t = planlib.resolve_need(prds, prd, d)
        if t is None:
            raise Refused(f"unblock: needs `{d}` names no PRD on this board")
        if prds[t]["state"] != "done":
            raise Refused(f"unblock: needs {t} is `{prds[t]['state']}` — "
                          "the event has not landed")


# The table: (from, to) → the command that owns the edge. `defer` owns every
# live state's edge to `deferred`. A parked state that names a person answers
# like `question` — it is the same claim without the obligation.
EDGES = {
    ("open", "analyzing"): "claim",
    ("specced", "claimed"): "claim",
    ("analyzing", "refine"): "release",
    ("analyzing", "question"): "release",
    ("analyzing", "open"): "release",
    ("claimed", "blocked"): "release",
    ("claimed", "failed"): "release",
    ("question", "open"): "answer",
    ("failed", "open"): "retry",
    ("blocked", "specced"): "unblock",
}
for _s in STATES:
    if _s != "done":
        EDGES[(_s, PARKED)] = "defer"


def edge_of(frm, to):
    key = ("question" if frm.lower() in qlib.WAITING else frm, to)
    return EDGES.get(key)


# ── the one writer ────────────────────────────────────────────────────────────

def transition(board, name, to, persona, worker=None, force=False,
               source=None, out=print):
    """Move one PRD. Returns the progress line it printed.

    Every command below calls this, and so does the view's `/edit` — with
    `force` and `source="view"`, because a person at the page is the user
    talking to the board and is not gated. `force` skips the gate and says so
    on the line; from a shell it is the escape hatch, never the path."""
    prds = planlib.scan(board)
    rel = resolve(prds, name)
    prd = prds[rel]
    frm = prd["state"]
    if frm == to:
        raise Refused(f"{rel} is already `{to}`")
    cmd = edge_of(frm, to)
    if not force:
        if cmd is None:
            raise Refused(f"no command moves `{frm}` → `{to}` — the table is "
                          "@references/parts/states.md; `set --force` is the "
                          "escape hatch")
        if cmd == "claim":
            if not worker:
                raise Refused("claim: a worker is named — "
                              f"`claim {rel} <worker>`")
            gate_claim(board, prds, prd)
        elif cmd == "release":
            gate_release(board, prds, prd, to)
        elif cmd == "answer":
            gate_answered(board, prds, prd)
        elif cmd == "defer":
            gate_defer(board, prds, prd)
        elif cmd == "unblock":
            gate_unblock(board, prds, prd)
        elif cmd == "retry" and frm != "failed":
            raise Refused(f"retry: {rel} is `{frm}`, not failed")
    # the gate passed, or was forced: now the writes, one line each
    path = os.path.join(prd["dir"], "prd.md")
    editlib.set_key(path, "state", to)
    if cmd == "claim" and worker and not force:
        editlib.set_key(path, "claim", f"{worker} {now()}")
    elif cmd in ("release", "retry") and not force:
        editlib.del_key(path, "claim")
    record(prd, frm, to)
    if cmd == "claim" and not force:
        snapshot_claim(board, rel)
    line = progress_line(board, rel, frm, to, persona, forced=force,
                         source=source)
    if source is None:
        line = owed_line(line)
    out(line)
    return line


def owed_line(line):
    """`round file owed` before `as`: a shell command moved a PRD, and the
    guard's reminder fires on a tool edit, never on a command — so the line
    says it. The view's own lines do not: a person at the page is not a
    round."""
    head, _, tail = line.rpartition(" · as ")
    return f"{head} · round file owed · as {tail}" if tail else line


def snapshot_claim(board, rel):
    """The claim's baseline — what is dirty, what the gate says — under
    `prds/.claims/<rel>/`, the record `collect` measures against. collect.py
    imports this module, so the import is here, not at the top. A board
    outside a git repo has nothing to snapshot and says so once."""
    import collect as collectlib
    try:
        collectlib.snapshot(board, rel)
    except collectlib.Stop as e:
        print(f"claim: no baseline — {e}", file=sys.stderr)


def owe_path(board, path):
    """List a board-repo path a command wrote between transitions in
    `prds/.claims/riders` — it rides the next collect."""
    import collect as collectlib
    root = planlib.repo_root(board)
    if root:
        collectlib.owe(board, os.path.relpath(path, root))


def record(prd, frm, to):
    """One row in the PRD's own board's `.transitions.jsonl` — the only memory
    of when a state moved. Appended, never rewritten, and never
    `.history.jsonl`: that one is the daemon's burn-down, one row a day,
    truncated to 400 rows on every write."""
    row = {"t": datetime.datetime.now().isoformat(timespec="seconds"),
           "prd": prd["local"], "from": frm, "to": to}
    row.update(hand_over(prd["board_path"]))
    path = os.path.join(prd["board_path"], TRANSITIONS_FILE)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")


def transcript_tokens(path):
    """The output-token sum of a session transcript on disk — one JSON object
    a line, an assistant line carrying `message.usage.output_tokens`; a
    message streamed in several lines is counted once, by its id. None when
    the file cannot be read: tokens are unmeasured, never zero."""
    seen = {}
    try:
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                m = d.get("message") if isinstance(d, dict) else None
                if not isinstance(m, dict):
                    continue
                u = m.get("usage") or {}
                if "output_tokens" in u:
                    seen[m.get("id") or i] = int(u["output_tokens"] or 0)
    except (OSError, TypeError, ValueError):
        return None
    return sum(seen.values())


def hand_over(board):
    """The guard's count for the window that ends with this transition —
    `calls`, `reads`, `refused` and `tokens` off the live session's block for
    this board, counter minus the last mark; the mark then moves to now, and
    so does `since`. Every value is None
    when no guard counted: a session with the guard off records nothing.
    Whatever is wrong with the file is not this command's to refuse on."""
    out = {"calls": None, "reads": None, "refused": None, "tokens": None}
    sessions = planlib.guard_sessions()
    if not sessions:
        return out
    sid, _, data = sessions[-1]
    b = planlib.guard_block(board, data)
    if b is None:
        return out
    mark = b.get("mark") or {}
    for k in ("calls", "reads", "refused"):
        out[k] = max(int(b.get(k, 0)) - int(mark.get(k, 0)), 0)
    total = transcript_tokens(data["transcript"]) \
        if data.get("transcript") else None
    if total is not None:
        out["tokens"] = max(total - int(mark.get("tokens", 0)), 0)
    b["mark"] = {k: int(b.get(k, 0))
                 for k in ("calls", "reads", "bash", "edits", "refused")}
    if total is not None:
        b["mark"]["tokens"] = total
    b["transitions"] = int(b.get("transitions", 0)) + 1
    b["since"] = datetime.datetime.now().timestamp()
    try:
        path = os.path.join(planlib.GUARD_DIR, sid + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        pass
    return out


# ── the progress line ─────────────────────────────────────────────────────────

def sections(board, prds, r):
    """(collect, ready, blocked) counted the way `plan.py scan` groups its
    sections, so the line and the scan agree."""
    if not r:
        return 0, 0, 0
    collect = list(r["collect"])
    order = [x for x in r["order"] if x not in collect]
    yours = {x for x in order if prds[x]["state"] in (
        "question", "blocked", "refine", "failed")}
    flight = {x for x in order if prds[x]["state"] in ("analyzing", "claimed")}
    ready = [x for x in order if x not in yours and x not in flight
             and not r["needs"].get(x) and not r["after"].get(x)]
    live = len(r["todo"])
    return len(collect), len(ready), live - len(ready)


def progress_line(board, rel, frm, to, persona, forced=False, source=None):
    t = planlib.progress_terms(board)
    r = planlib.compute_plan(board, None, warn=False)
    c, ready, blocked = sections(board, t["prds"], r)
    ad, an = t["asked"]
    dd, dn = t["derived"]
    o, n = t["open"]
    live = t["live"]
    live_der = sum(1 for p in live.values()
                   if str(p["fm"].get("origin", "")).strip() == "derived")
    tripwire = live_der and live_der >= len(live) - live_der
    workers = r["workers"] if r else planlib.plan_workers(board, None)
    bits = [f"▸ {rel}: {frm} → {to}"]
    if forced:
        bits.append("forced")
    if source:
        bits.append(source)
    bits += [f"asked {ad}/{an}", f"{t['pct']}%"]
    if dn:
        bits.append(f"derived {dd}/{dn}")
    bits += [f"open {o}/{n}", f"{t['openpct']}%", f"ready {ready}",
             f"blocked {blocked}"]
    if c:
        bits.append(f"collect {c}")
    if tripwire:
        bits.append("tripwire")
    bits[-1] += f" @{workers} workers"
    bits.append(f"as {persona}")
    return " · ".join(bits)


# ── the commands ──────────────────────────────────────────────────────────────

# A body this long, or holding a second "When this is done", is more than
# one sitting — `add` says so on its first line and creates the PRD anyway;
# the split is the analyst's, through `pearde refine`.
BIG_LINES = 60


def add(board, title, persona, priority=0, body="", parent=None, out=print):
    """A directory and `prd.md` from the template, `open`, `origin:
    requested`. The gate: the slug is free. Returns the new rel. The view's
    `/new` calls this; `cmd_add` is the shell's way in."""
    title = str(title).strip()
    if not title:
        raise Refused("add: a title is named")
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]
    if not slug:
        raise Refused("add: the title has no letters to slug")
    base = board
    if parent:
        prds = planlib.scan(board)
        base = prds[resolve(prds, parent)]["dir"]
    d = os.path.join(base, slug)
    if os.path.exists(d):
        raise Refused(f"add: the slug `{slug}` is taken — "
                      f"{os.path.relpath(d, board)} exists")
    text = from_template(title, int(priority or 0), body or "")
    if len(body.strip().splitlines()) > BIG_LINES or \
            body.lower().count("when this is done") > 1:
        out("big — expect a split")     # a warning; it gates nothing
    os.makedirs(d)
    editlib.write_atomic(os.path.join(d, "prd.md"), text)
    rel = os.path.relpath(d, board)
    record({"local": rel, "board_path": board}, None, "open")
    out(progress_line(board, rel, "—", "open", persona))
    return rel


def cmd_add(board, args, persona):
    try:
        priority = int(args.opt.get("priority") or 0)
    except ValueError:
        raise Refused("add: --priority takes an integer")
    body = sys.stdin.read() if args.opt.get("body") == "-" else ""
    add(board, " ".join(args.pos), persona, priority, body,
        args.opt.get("parent"))
    return 0


PLACEHOLDER_RE = re.compile(r"<The request, for an analyst.*?refine\.>\n?",
                            re.S)


def from_template(title, priority, body):
    """The template with the three values set and the title line written.
    Comments and every other key stay as the template has them."""
    text = open(TEMPLATE, encoding="utf-8").read()
    head, fm, tail = editlib.split_fm(text)
    if fm is None:
        raise Refused(f"add: {TEMPLATE} has no frontmatter")
    out = []
    for line in fm:
        m = re.match(r"^(state|origin|priority):\s*(.*?)(\s+#.*)?$",
                     line.rstrip("\n"))
        if m:
            v = {"state": "open", "origin": "requested",
                 "priority": str(priority)}[m.group(1)]
            line = f"{m.group(1)}: {v}{m.group(3) or ''}\n"
        out.append(line)
    tail = re.sub(r"(?m)^# <Title[^\n]*$", "# " + title, tail, count=1)
    if body.strip():
        tail = PLACEHOLDER_RE.sub(body.strip() + "\n", tail, count=1)
    return head + "".join(out) + tail


def cmd_claim(board, args, persona):
    if len(args.pos) != 2:
        raise Refused("claim <prd> <worker>")
    prds = planlib.scan(board)
    rel = resolve(prds, args.pos[0])
    frm = prds[rel]["state"]
    to = {"open": "analyzing", "specced": "claimed"}.get(frm)
    if to is None:
        raise Refused(f"claim: {rel} is `{frm}` — open → analyzing or "
                      "specced → claimed")
    transition(board, rel, to, persona, worker=args.pos[1])
    return 0


def cmd_release(board, args, persona):
    if len(args.pos) != 2:
        raise Refused("release <prd> <state>")
    rel, to = args.pos
    prds = planlib.scan(board)
    rel = resolve(prds, rel)
    frm = prds[rel]["state"]
    allowed = {"analyzing": ("refine", "question", "open"),
               "claimed": ("blocked", "failed")}
    if frm not in allowed or to not in allowed[frm]:
        raise Refused(f"release: {rel} is `{frm}` — analyzing → "
                      "refine|question|open, claimed → blocked|failed")
    transition(board, rel, to, persona)
    return 0


def cmd_answer(board, args, persona):
    if len(args.pos) != 3:
        raise Refused('answer <prd> Q<n> "<text>"')
    name, qid, text = args.pos
    qid = planlib._qid(qid.strip())
    text = text.strip()
    if not text:
        raise Refused("answer: the decision is the text, and it is empty")
    prds = planlib.scan(board)
    rel = resolve(prds, name)
    prd = prds[rel]
    if qid not in questions_of(prd):
        qs = questions_of(prd)
        raise Refused(f"answer: {qid} is not in `## Questions`"
                      + (" — " + ", ".join(qs) if qs else " — no round"))
    if qid in answered_of(prd):
        raise Refused(f"answer: {qid} is already answered")
    path = os.path.join(prd["dir"], "prd.md")
    editlib.append_section(path, "Answers",
                           f"**{qid}** *(answered {now()})* — {text}")
    owe_path(board, path)
    prds = planlib.scan(board)
    prd = prds[rel]
    left = [q for q in questions_of(prd) if q not in answered_of(prd)]
    if left:
        print(f"{rel}: {qid} answered · {len(left)} left — "
              + ", ".join(left))
        return 0
    if prd["state"] == "question" or prd["state"].lower() in qlib.WAITING:
        transition(board, rel, "open", persona)
    else:
        print(f"{rel}: {qid} answered · every question answered · "
              f"state `{prd['state']}` left as it is")
    return 0


def cmd_defer(board, args, persona):
    if len(args.pos) != 1:
        raise Refused("defer <prd>")
    transition(board, args.pos[0], PARKED, persona)
    return 0


def cmd_retry(board, args, persona):
    """`## Failure` becomes history in the body, then `failed → open`."""
    if len(args.pos) != 1:
        raise Refused("retry <prd>")
    prds = planlib.scan(board)
    rel = resolve(prds, args.pos[0])
    prd = prds[rel]
    if prd["state"] != "failed":
        raise Refused(f"retry: {rel} is `{prd['state']}`, not failed")
    path = os.path.join(prd["dir"], "prd.md")
    text = open(path, encoding="utf-8").read()
    _, _, tail = editlib.split_fm(text)
    m = re.search(r"(?ms)^## Failure\b[^\n]*\n(.*?)(?=^## |\Z)", tail)
    if m:
        failure = m.group(1).strip()
        rest = (tail[:m.start()] + tail[m.end():]).rstrip("\n")
        rest = rest[len("---\n"):] if rest.startswith("---\n") else rest
        rest += (f"\n\n## History\n\n**failed, retried {now()}**\n\n"
                 f"{failure}\n") if failure else ""
        editlib.set_body(path, rest)
    transition(board, rel, "open", persona)
    return 0


def cmd_unblock(board, args, persona):
    if len(args.pos) != 1:
        raise Refused("unblock <prd>")
    prds = planlib.scan(board)
    rel = resolve(prds, args.pos[0])
    if prds[rel]["state"] != "blocked":
        raise Refused(f"unblock: {rel} is `{prds[rel]['state']}`, not blocked")
    transition(board, rel, "specced", persona)
    return 0


def cmd_set(board, args, persona):
    if len(args.pos) != 2:
        raise Refused("set <prd> <state> [--force]")
    rel, to = args.pos
    transition(board, rel, to, persona, worker=args.opt.get("worker"),
               force="force" in args.flags)
    return 0


# ── sweep ─────────────────────────────────────────────────────────────────────
# The board cannot see a worker; `plan.py` `silent_of` is the one rule for a
# claim whose files have stopped moving, and this is the command that acts on
# its word. What it lists is the orchestrator's to read first — a swept
# worker's report and its `## Workflow` rows count whatever the verdict did.

def round_names(board, rel, who):
    """True when `prds/.round.md` names this claim — the PRD's path, its
    basename or its worker. A claim the round file names is a session's
    live work, and `--apply` leaves it."""
    try:
        text = open(os.path.join(board, planlib.ROUND_FILE),
                    encoding="utf-8").read()
    except OSError:
        return False
    for word in (rel, os.path.basename(rel), who):
        if word and re.search(r"(?<![\w/-])" + re.escape(word) + r"(?![\w/-])",
                              text):
            return True
    return False


def sweep_rows(board):
    """One row per silent claim: (rel, state, claim, age, to, why). `to` is
    the state `--apply` writes, or None with `why` saying what holds it."""
    prds = planlib.scan(board)
    settings = planlib.board_settings(board)
    rows = []
    for rel in sorted(prds):
        p = prds[rel]
        age = planlib.silent_of(p, settings)
        if age is None:
            continue
        cl = planlib.claim_of(p["fm"]) or {"who": "", "since": ""}
        specs = [f for f in os.listdir(os.path.join(p["dir"], "specs"))
                 if f.endswith(".md")] \
            if os.path.isdir(os.path.join(p["dir"], "specs")) else []
        if p["state"] == "analyzing" and specs:
            to, why = None, (f"specs on disk — an analyst that finished: "
                             f"`pearde specced {rel}`")
        elif round_names(board, rel, cl["who"]):
            to, why = None, "named in prds/.round.md — a session's live work"
        elif p["state"] == "analyzing":
            to, why = "open", "no specs — `--apply` sets open"
        else:
            to, why = "failed", ("`--apply` sets failed; partial code may "
                                 "stand in the tree")
        rows.append((rel, p["state"], cl, age, to, why))
    return rows


def cmd_sweep(board, args, persona):
    """every claim silent past `claim-ttl`; `--apply` moves analyzing → open, claimed → failed"""
    if args.pos:
        raise Refused("sweep [--apply]")
    apply = "apply" in args.flags
    ttl = planlib.claim_ttl(planlib.board_settings(board))
    rows = sweep_rows(board)
    if not rows:
        print(f"sweep: no claim silent past claim-ttl {planlib.fmt_age(ttl)}")
        return 0
    for rel, state, cl, age, to, why in rows:
        held = f"claim {cl['who']} {cl['since']}".rstrip()
        print(f"{rel} · {state} · {held} · silent {planlib.fmt_age(age)} · "
              f"{why}")
        if not apply or to is None:
            continue
        if to == "failed":
            path = os.path.join(planlib.scan(board)[rel]["dir"], "prd.md")
            editlib.append_section(
                path, "Failure",
                f"swept {now()} — {held}, silent {planlib.fmt_age(age)}: "
                "no file of this PRD's moved past `claim-ttl`. Read the "
                "worker's output before a retry; partial code may stand in "
                "the tree.")
        transition(board, rel, to, persona)
    return 0


# ── the surface ───────────────────────────────────────────────────────────────

class Args:
    """`--key value` options, `--flag` switches, the rest positional."""
    VALUED = ("board", "as", "priority", "body", "parent", "worker")

    def __init__(self, argv):
        self.pos, self.opt, self.flags = [], {}, set()
        it = iter(argv)
        for a in it:
            if a.startswith("--") and len(a) > 2:
                k, eq, v = a[2:].partition("=")
                if k in self.VALUED:
                    self.opt[k] = v if eq else next(it, "")
                else:
                    self.flags.add(k)
            else:
                self.pos.append(a)


def persona_default(name):
    """What a command runs as when neither `--as` nor `PEARDE_AS` named a
    persona: `engineer (default)` for a command in DEFAULTS_FOR, said on the
    line so the record shows nobody chose it; a refusal for every other one,
    which would rewrite what an earlier persona's line recorded."""
    if name in DEFAULTS_FOR:
        return f"{DEFAULT_PERSONA} (default)"
    raise Refused("persona: `--as <id>` on the line, or PEARDE_AS in the "
                  f"environment — `{INSTALL_LINE}` is the line `install "
                  "--apply` prints beside the alias; add it to your shell")


def run(name, fn, argv):
    args = Args(argv)
    try:
        persona = (args.opt.get("as")
                   or os.environ.get("PEARDE_AS", "")).strip()
        if not persona:
            persona = persona_default(name)
        board = planlib.find_board(args.opt.get("board"))
        return fn(board, args, persona)
    except Refused as e:
        print(f"pearde {name}: refused — {e}", file=sys.stderr)
        return 1


def _command(name, fn):
    def call(argv):
        return run(name, fn, argv)
    call.__doc__ = fn.__doc__
    call.__name__ = name
    return call


COMMANDS = {name: _command(name, fn) for name, fn in (
    ("add", cmd_add), ("claim", cmd_claim), ("release", cmd_release),
    ("answer", cmd_answer), ("defer", cmd_defer), ("retry", cmd_retry),
    ("unblock", cmd_unblock), ("set", cmd_set),
    ("sweep", cmd_sweep))}


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
