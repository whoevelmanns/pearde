#!/usr/bin/env python3
"""pearde brief — a worker's brief is one command's output, never composed.

    brief.py <prd> [--role analyst|implementer] [--as <id>] [--force] [--board <path>]
    brief.py --consult <id> --question "<q>" [--transcript <path>] [--board <path>]
    brief.py --check                    the brief blocks in workers.md, one problem per line

Prints, in this order: one header line the round logs, the persona line, the
workflow block with the route inlined (one per distinct slug), the role's
brief, and the block every worker gets. The text lives in
@references/parts/workers.md between `<!-- brief:<name> -->` … `<!-- /brief -->`
markers — this file reads it, fills the placeholders the table there names,
and holds no copy. The role follows the state: `open` is an analyst,
`specced` an implementer; `--role` overrides.

Dispatchable is @resources/board/transitions.py `gate_claim` — the same test
`claim` runs, imported and not re-implemented. A PRD that fails it exits 1
naming the skip: `held`, `gated`, `clash`, `workflow`, `leaf`, `state`.
`--force` prints the brief anyway and says `forced` on the header line.

`--check` is the `doctor` row `briefs`: every marker pair present and
terminated, every placeholder a block uses named in the table, every row
of the table used by a block.

Python 3 stdlib only.
"""
import contextlib
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def skill_root():
    """The nearest ancestor holding resources/board/plan.py — works from
    resources/board/brief.py and from a probe copy under prds/ alike."""
    d = HERE
    while True:
        if os.path.isfile(os.path.join(d, "resources", "board", "plan.py")):
            return d
        nxt = os.path.dirname(d)
        if nxt == d:
            print("pearde brief: no resources/board/plan.py above this file",
                  file=sys.stderr)
            sys.exit(2)
        d = nxt


ROOT = skill_root()
RES = os.path.join(ROOT, "resources")
sys.path.insert(0, RES)
sys.path.insert(0, os.path.join(RES, "board"))
import plan as planlib              # noqa: E402 — every read
import collect as collectlib        # noqa: E402 — `repo_of`, the one rule
import transitions as trlib         # noqa: E402 — the gate, and `resolve`
import workflows as wflib           # noqa: E402 — the route inlined
import specs as specslib            # noqa: E402 — `limits`, the two numbers

WORKERS = os.path.join(ROOT, "references", "parts", "workers.md")
PERSONAS = os.path.join(ROOT, "references", "personas")

OPEN_RE = re.compile(r"^<!--\s*brief:([\w-]+)\s*-->\s*$")
CLOSE_RE = re.compile(r"^<!--\s*/brief\s*-->\s*$")
# A placeholder is `<name>` — lowercase, `_` or `/` inside. `<dir-name>`,
# `<N>` and `<one line — …>` in the analyst block are the shapes the worker's
# own report takes and are not filled here.
TOKEN_RE = re.compile(r"<[a-z][a-z_/]*>")
TABLE_ROW_RE = re.compile(r"^\|\s*`(<[^`]+>)`\s*\|")
ROLES = ("analyst", "implementer")
BLOCKS = ("workflow", "every", "analyst", "implementer", "consultant")
SKIP = {"unclaimed": "held", "needs": "gated", "footprint": "clash",
        "workflow": "workflow", "leaf": "leaf", "container": "collect"}


class Refused(Exception):
    pass


# ── the one source ────────────────────────────────────────────────────────────

def read_blocks(path=WORKERS):
    """({name: [lines]}, [problems]). Lines are what sits between the
    markers, blockquote prefix still on."""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError as e:
        return {}, [f"{os.path.relpath(path, ROOT)}: {e}"]
    blocks, bad, cur, name, start = {}, [], None, None, 0
    rel = os.path.relpath(path, ROOT)
    for i, line in enumerate(text.splitlines(), start=1):
        m = OPEN_RE.match(line)
        if m:
            if cur is not None:
                bad.append(f"{rel}:{start}: `brief:{name}` is not terminated "
                           f"before `brief:{m.group(1)}` opens at line {i}")
                blocks[name] = cur      # counted once: here, not as missing
            if m.group(1) in blocks:
                bad.append(f"{rel}:{i}: `brief:{m.group(1)}` opens twice")
            cur, name, start = [], m.group(1), i
            continue
        if CLOSE_RE.match(line):
            if cur is None:
                bad.append(f"{rel}:{i}: `/brief` with no block open")
                continue
            blocks[name] = cur
            cur = None
            continue
        if cur is not None:
            cur.append(line)
    if cur is not None:
        bad.append(f"{rel}:{start}: `brief:{name}` is not terminated")
        blocks[name] = cur
    for b in BLOCKS:
        if b not in blocks:
            bad.append(f"{rel}: no `<!-- brief:{b} -->` … `<!-- /brief -->` pair")
    return blocks, bad


def table(path=WORKERS):
    """The placeholders the file names, in table order."""
    out = []
    try:
        for line in open(path, encoding="utf-8"):
            m = TABLE_ROW_RE.match(line)
            if m and m.group(1) not in out:
                out.append(m.group(1))
    except OSError:
        pass
    return out


def unquote(lines):
    """The block as a worker reads it: the blockquote prefix off."""
    out = []
    for l in lines:
        if l.startswith("> "):
            l = l[2:]
        elif l == ">":
            l = ""
        out.append(l)
    return out


def tokens_of(lines):
    """Every placeholder a block uses, outside fenced code."""
    seen, fence = [], False
    for l in unquote(lines):
        if l.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        for t in TOKEN_RE.findall(l):
            if t not in seen:
                seen.append(t)
    return seen


def check(path=WORKERS):
    """Every problem, one string each. Empty means the briefs are sound."""
    blocks, bad = read_blocks(path)
    named = table(path)
    rel = os.path.relpath(path, ROOT)
    if not named:
        bad.append(f"{rel}: no placeholder table — a row is "
                   "`| `<name>` | filled from |`")
    used = set()
    for name, lines in blocks.items():
        text = "\n".join(lines)
        for t in tokens_of(lines):
            if t not in named:
                bad.append(f"{rel}: `{t}` in brief:{name} is not in the "
                           "placeholder table")
        for t in named:
            if t in text:
                used.add(t)
    for t in named:
        if t not in used:
            bad.append(f"{rel}: the table names `{t}` and no brief block "
                       "uses it")
    return bad


def render(lines, values):
    """The block, unquoted, with the given placeholders filled."""
    out = []
    for l in unquote(lines):
        for k, v in values.items():
            l = l.replace(k, v)
        out.append(l)
    return "\n".join(out).strip("\n")


# ── what fills the placeholders ───────────────────────────────────────────────

def repo_of(prd, board):
    """`repo:` that is a directory — absolute, or relative to the board's
    repo — is it: the rule @resources/board/collect.py `repo_of` states, read
    from there and not restated. Else the PRD's own board's repo — a
    member's — else the board's."""
    board_root = planlib.repo_root(board) or os.path.dirname(board)
    found = collectlib.repo_of(prd, board_root)
    if found != board_root:
        return found
    return planlib.repo_root(prd["board_path"]) or board_root


def language_of(prd):
    v = planlib.board_settings(prd["board_path"]).get("language")
    return str(v).strip() if v and not isinstance(v, list) else "English"


def slugs_of(prd, role):
    """The distinct `workflow:` slugs a brief carries, PRD first, then each
    spec's for an implementer, in file order."""
    out = []
    v = prd["fm"].get("workflow")
    if v and not isinstance(v, list) and str(v).strip():
        out.append(str(v).strip())
    if role == "implementer":
        sdir = os.path.join(prd["dir"], "specs")
        if os.path.isdir(sdir):
            for f in sorted(os.listdir(sdir)):
                if f.endswith(".md"):
                    fm, _, _ = planlib.parse_prd(os.path.join(sdir, f))
                    s = fm.get("workflow")
                    if s and not isinstance(s, list) and str(s).strip() \
                            and str(s).strip() not in out:
                        out.append(str(s).strip())
    return out


def resolve_slug(slug, prd, board):
    """The board whose library holds `slug` as a workflow — the PRD's own
    first, then the master's — or None."""
    for b in (prd["board_path"], board):
        if wflib.scan(b).get(slug, {}).get("kind") == "workflow":
            return b
    return None


def route(board, slug):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = wflib.brief(board, slug)
    return buf.getvalue().rstrip() if rc == 0 else ""


def persona_line(pid):
    if not re.fullmatch(r"[a-z][\w-]*", pid) or \
            not os.path.isfile(os.path.join(PERSONAS, pid + ".md")):
        raise Refused(f"no persona `{pid}` — references/personas/<id>.md; "
                      "the roster is references/personas/INDEX.md")
    return f"Work as @references/personas/{pid}.md."


# ── the two briefs ────────────────────────────────────────────────────────────

def brief_prd(args, out=print):
    if len(args.pos) != 1:
        raise Refused("brief <prd> [--role analyst|implementer] [--as <id>] "
                      "[--force]")
    blocks, bad = read_blocks()
    if bad:
        raise Refused("workers.md is not sound — " + "; ".join(bad))
    board = planlib.find_board(args.opt.get("board"))
    prds = planlib.scan(board)
    try:
        rel = trlib.resolve(prds, args.pos[0])
    except trlib.Refused as e:
        raise Refused(str(e))
    prd = prds[rel]
    force = "force" in args.flags
    state = prd["state"]
    role = args.opt.get("role")
    if role and role not in ROLES:
        raise Refused(f"--role takes analyst or implementer, not `{role}`")
    if not role:
        role = {"open": "analyst", "analyzing": "analyst",
                "specced": "implementer", "claimed": "implementer"}.get(state)
    skip = None
    held = planlib.claim_of(prd["fm"])
    if state in ("analyzing", "claimed") or (held and state in ("open",
                                                                "specced")):
        skip = (f"held — {rel} is `{state}`"
                + (f", `claim: {prd['fm']['claim']}`" if held else ""))
    elif state not in ("open", "specced"):
        skip = f"state — {rel} is `{state}`, not open or specced"
    else:
        try:
            trlib.gate_claim(board, prds, prd)
        except trlib.Refused as e:
            msg = str(e)
            word = SKIP.get(msg.split(":", 1)[0], "gate")
            skip = f"{word} — {msg}"
    if skip and not force:
        raise Refused(f"skipped {rel} — {skip}")
    if skip:
        print(f"pearde brief: forced past {skip}", file=sys.stderr)
    if not role:
        raise Refused(f"no role for state `{state}` — name one with --role")
    pid = args.opt.get("as") or "engineer"
    persona = persona_line(pid)
    local = prd["local"]
    lim = specslib.limits(prd["board_path"])
    values = {"<prd>": local, "<repo>": repo_of(prd, board),
              "<language>": language_of(prd),
              "<probe>": f"prds/{local}/probe/",
              "<split_above>": str(lim["split-above"]),
              "<specs_above>": str(lim["specs-above"])}
    slugs = slugs_of(prd, role)
    wf_lines, marks = [], []
    for s in slugs:
        b = resolve_slug(s, prd, board)
        if b is None:
            marks.append(s + "?")
            continue
        marks.append(s)
        wf_lines.append(render(blocks["workflow"], {"<slug>": s, "<board>": b}))
        wf_lines.append(route(b, s))
    head = (f"# brief {local} · {role} · as {pid} · wf "
            f"{','.join(marks) if marks else 'none'} · repo {values['<repo>']}")
    if force:
        head += " · forced"
    parts = [head, persona] + wf_lines + [
        render(blocks[role], values), render(blocks["every"], values)]
    out("\n\n".join(p for p in parts if p))
    return 0


def brief_consult(args, out=print):
    pid = args.opt.get("consult", "")
    q = (args.opt.get("question") or "").strip()
    if not q:
        raise Refused('--consult <id> --question "<q>" [--transcript <path>]')
    blocks, bad = read_blocks()
    if bad:
        raise Refused("workers.md is not sound — " + "; ".join(bad))
    persona_line(pid)  # the roster check; the block carries its own line
    board = planlib.find_board(args.opt.get("board"))
    repo = planlib.repo_root(board) or os.path.dirname(board)
    values = {"<id>": pid, "<transcript_path>": args.opt.get("transcript")
              or "none — no transcript was handed over",
              "<prds/>": board, "<repo>": repo,
              "<the question, as the user put it>": q}
    out(f"# brief consult · as {pid} · repo {repo}\n\n"
        + render(blocks["consultant"], values))
    return 0


# ── the surface ───────────────────────────────────────────────────────────────

class Args:
    VALUED = ("board", "as", "role", "consult", "question", "transcript")

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


def cmd_brief(argv):
    """the worker's brief for one PRD, or a consultant's — one command's output"""
    args = Args(argv)
    if "check" in args.flags:
        bad = check()
        if bad:
            print("\n".join(bad))
        return 1 if bad else 0
    try:
        if "consult" in args.opt:
            return brief_consult(args)
        return brief_prd(args)
    except Refused as e:
        print(f"pearde brief: {e}", file=sys.stderr)
        return 1
    except SystemExit as e:      # plan.py `die` on a board that is not there
        return int(e.code) if isinstance(e.code, int) else 2


COMMANDS = {"brief": cmd_brief}


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(cmd_brief(sys.argv[1:]))
