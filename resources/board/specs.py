#!/usr/bin/env python3
"""pearde specs — the two transitions a spec set decides.

    specs.py specced <prd> [--blast high|mid|low] [--workflow <slug>] [--route -] [--check] [--dry]
    specs.py refine  <prd> [--dry] < report

`specced` reads every `specs/*.md`, refuses naming file and line, refuses a
set over `split-above` or `specs-above` (`over split-above: 58 > 40 — REFINE
it`; the two keys of `settings.md`, the PRD's own board's), else writes
`complexity:` as the sum, `blast-radius:` and `workflow:` from the flags,
clears `claim:`, sets `specced` and prints the progress line. With no
`--workflow` named and none on the PRD, one distinct `workflow:` across the
specs is written up onto the PRD instead of being read and dropped — specs
naming two different slugs write none, and the operator is told which on
stderr. `--check` runs
the gate and writes nothing. `--workflow <new-slug> --route -` drafts a
workflow the library does not hold from `## Route` on stdin — the file per
step and every new atomic's, `workflow check` over the whole library before
either is kept, refused whole on red with nothing written. `--workflow
<slug>` naming one the library already has refuses `--route` — the route
exists, follow it — and `--workflow none` is refused outright, naming
`## Route`. `refine` reads the `## Split` table off stdin,
writes one child `prd.md` per row from the template, the same table under the
parent's `## Children`, and sets the parent `open`.

Both take `--board <path>` (default: walk up from the cwd) and `--as <id>`,
the persona on the progress line, else `PEARDE_AS` from the environment —
the same rule as every transition, because the line is the only record of it.
The flags are declared in `FLAGS` and parsed by transitions.py `Args` — an
undeclared one is refused with the list, exit 2, before the board is read;
`--dry` prints the line the write would print, `dry ·` in front, and the
paths, and writes nothing.

`plan.py` does the reading, `edit.py` the writing, and `transitions.py` prints
the progress line and records the row in `.transitions.jsonl` — the same
three every other transition goes through. The model creates no directory
and sums no number.

Python 3 stdlib only.
"""
import datetime
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # the skill's resources/
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import edit  # noqa: E402
import plan  # noqa: E402
import transitions as trlib  # noqa: E402
import workflows as wflib  # noqa: E402

Refused = trlib.Refused
BLASTS = ("high", "mid", "low")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
FENCE_RE = re.compile(r"^\s*```\s*([A-Za-z0-9_-]*)\s*$")
# A box that asks the worker to commit — committing is the orchestrator's
# act. The three spellings the contract names; a box that *checks* a
# `commit:` key, or asserts prose about commit rules, is not one. (Five such
# boxes stand on this board, and a bare `\bcommit\b` refused every one.)
COMMIT_RE = re.compile(r"\bcommit the\b|\bcommit message\b|\bgit commit\b",
                       re.I)
BOX_TEXT_RE = re.compile(r"^\s*[-*]\s+\[[ xX~]\]\s*(.*)$")
NONE_NEEDS = {"", "-", "—", "–", "none"}
SPECCED_FROM = ("analyzing",)
REFINE_FROM = ("refine", "analyzing", "open", "question")
CHILD_HEADER = "| child | contract | needs |\n|---|---|---|"
# The two size limits of @references/settings.md: over either, a spec set is
# REFINE and `specced` refuses it. The brief prints the same two numbers.
LIMITS = (("split-above", 40), ("specs-above", 6))


# ── can a verify block fail? ──────────────────────────────────────────────────

# collect runs every `## Verify and Proof` block under `bash -e -o pipefail`
# and reads the exit code that comes out. Between those two rules a block goes
# red only through a command that runs unsuppressed and can exit non-zero:
# under `set -e` the first such command aborts the block, and if there is
# none, the block's exit is its last line's — an `echo`. A block with none of
# those cannot fail, and a box that cannot fail is not a check: `specced`
# refuses it, the same four shapes the collect runner surfaced today —
# everything guarded with `|| true` behind a closing `echo`, an inverted
# `!`, a whole body in `if` conditions, a bare `true`.

# Builtin commands whose exit status is 0 come what may. Anything not listed
# here counts as able to exit non-zero — over-counting only ever accepts a
# block, under-counting would refuse a live one.
ALWAYS0 = frozenset(("echo", "printf", "true", ":", "pwd", "export", "unset",
                     "set", "local", "readonly", "declare", "shift"))

# Words that open a segment whose failure is a condition or a frame, not an
# abort: `if` / `while` / `until` conditions route to a branch instead of
# tripping `set -e`, and `then` / `else` / `do` are noise before the body
# that follows them on the same line.
CONDITION_HEAD = re.compile(r"^(if|elif|while|until|for|case)([ \t]|$)")
NOISE_HEAD = ("then", "else", "do", "fi", "done", "esac", "}", ")")


def _segments(line):
    """Top-level segments of one logical line with the operator that follows
    each — split at `;`, `&`, `|`, `&&`, `||`, never inside quotes or
    unquoted parentheses (a `$( )` substitution is one argument, and its
    operators are its own). With `pipefail` both sides of a `|` count; under
    `set -e` the left of `&&` fails the whole list; only the right operand
    of `||` can abort."""
    out, cur, quote, depth = [], "", None, 0
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line):
            cur += line[i:i + 2]
            i += 2
            continue
        if quote:
            cur += ch
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in "\"'":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif depth == 0 and ch in ";|&":
            if ch in "|&" and line[i:i + 2] in ("||", "&&"):
                out.append(_Seg(cur, line[i:i + 2]))
                cur, i = "", i + 2
                continue
            out.append(_Seg(cur, ch))
            cur, i = "", i + 1
            continue
        cur += ch
        i += 1
    out.append(_Seg(cur, ""))
    return out


class _Seg:
    """One command segment and the operator that separates it from the next.
    Under `set -e` a segment's failure aborts the block unless it is
    always-0, or the operator that follows it is `||` — then its failure
    just routes to the fallback, and the fallback is the abort candidate."""

    def __init__(self, text, op):
        self.text, self.op = text, op


def _unquote_hash(line):
    """Cut an unquoted trailing comment — its words are no command."""
    quote, i = None, 0
    while i < len(line):
        ch = line[i]
        if ch == "\\":
            i += 2
            continue
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i]
        i += 1
    return line


def _plain(seg):
    """The command of a segment: environment assignments and the body
    openers `then` / `else` / `do` stripped — `VAR=x then cmd` classifies as
    `cmd`."""
    tokens = seg.split()
    while len(tokens) > 1 and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0])
                               or tokens[0] in NOISE_HEAD):
        tokens = tokens[1:]
    return tokens[0].strip("'\"") if tokens else ""


def _first_word(seg):
    w = _plain(seg.text)
    return w


def _seg_can_fail(seg):
    """True when this one segment can leave the block non-zero."""
    s = seg.text.strip()
    if not s:
        return False
    if seg.op == "||":
        return False        # its failure routes to the fallback
    if s.startswith("!") and not s.startswith("[["):
        return False        # inverted: a failure is a pass
    if CONDITION_HEAD.match(s):
        return False        # a condition routes; the body is judged alone
    if re.match(r"^exit([ \t]+0)?$", s):
        return False
    words = seg.text.split()
    if len(words) == 1 and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]):
        return False        # a bare assignment without substitution
    if _plain(seg.text) in ALWAYS0:
        return False
    return True


def _cannot_fail_why(script):
    """Why a Verify block cannot exit non-zero, or None when it can — one
    pass over the logical lines, every segment that is an abort candidate
    making the block able to fail."""
    guarded, last = 0, ""
    lines, skip, delim, body = [], False, None, 0
    raw = script.splitlines()
    i = 0
    joined = ""
    while i < len(raw):
        line = raw[i]
        i += 1
        if skip == "heredoc":
            if line.strip() == delim:
                skip = None
            continue
        if body:
            if line.strip() in ("}", "};"):
                body = 0
            continue
        # join backslash continuations
        while line.rstrip().endswith("\\") and i < len(raw):
            line = line.rstrip()[:-1] + " " + raw[i]
            i += 1
        line = _unquote_hash(line).strip()
        if not line or line.startswith("#"):
            continue
        m = re.search(r"<<-?[ 	]*([\"']?)([A-Za-z_][A-Za-z0-9_]*)\1", line)
        if m and skip is None:
            skip, delim = "heredoc", m.group(2)
        if line.strip() == delim:
            skip = "heredoc"
            continue
        if re.match(r"^function[ \t]+\w+|^\w+[ \t]*\(\)[ \t]*\{?$", line):
            body = 1
            continue
        if line.strip() in ("{", "}"):
            continue
        for seg in _segments(line):
            if _seg_can_fail(seg):
                return None     # one abort candidate is enough
            if seg.text.strip():
                guarded += 1
                last = seg.text.strip()[:80] if seg else last
        last = _segments(line)[-1].text.strip() or last
    if guarded == 0:
        return "it holds no command that runs and can exit non-zero"
    return ("every fallible command is guarded and it ends on `%s` — "
            "exit 0 come what may" % last)


def block_cannot_fail(script):
    """True when no command in the block can make the block exit non-zero —
    the shape `collect` reads from the last command's exit code under
    `bash -e -o pipefail`."""
    return _cannot_fail_why(script) is not None

def fm_lines(text):
    """{key: 1-based line} for every key in the frontmatter block — refusals
    name a line, and `parse_prd` keeps none."""
    lines, out = text.splitlines(), {}
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                break
            m = plan.KEY_RE.match(lines[i])
            if m and m.group(1) not in out:
                out[m.group(1)] = i + 1
    return out


def h2_line(text, name):
    """1-based line of `## <name>` (prefix match, case-insensitive), or 0."""
    for i, line in enumerate(text.splitlines(), start=1):
        if line.startswith("## ") and line[3:].strip().lower().startswith(name):
            return i
    return 0


def section_text(text, name):
    """The body under `## <name>` up to the next `## `, or ''."""
    for sec in re.split(r"(?m)^##\s+", text)[1:]:
        head, _, rest = sec.partition("\n")
        if head.strip().lower().startswith(name):
            return rest
    return ""


def fenced(section, langs=("sh", "bash")):
    """The fenced blocks in `section` whose info string is one of `langs`."""
    out, cur, keep = [], None, False
    for line in section.splitlines():
        m = FENCE_RE.match(line)
        if m and cur is None:
            cur, keep = [], m.group(1).lower() in langs
        elif m:
            if keep:
                out.append("\n".join(cur))
            cur = None
        elif cur is not None:
            cur.append(line)
    return out


def check_spec(path, fm, text, lib, own_feet):
    """(refusals, warnings, footprint) for one spec — every check the
    contract table lists, in its order. `own_feet` is the PRD's footprint,
    what stands for a spec that carries none."""
    bad, warn = [], []
    keys = fm_lines(text)
    name = os.path.basename(path)

    raw = fm.get("complexity")
    if raw is None or isinstance(raw, list):
        bad.append((keys.get("complexity", 1), "complexity missing"))
    else:
        try:
            c = int(str(raw))
            if not 1 <= c <= 100:
                bad.append((keys["complexity"],
                            f"complexity {c} outside 1-100"))
        except ValueError:
            bad.append((keys["complexity"],
                        f"complexity `{raw}` is not an integer"))

    fp = fm.get("footprint")
    fp = fp if isinstance(fp, list) else ([fp] if fp else [])
    fp = [str(p).strip().rstrip("/") for p in fp if str(p).strip()]
    if not fp:
        warn.append(f"{name}:{keys.get('footprint', 1)}: no footprint — the "
                    "PRD's own stands for it")
        fp = list(own_feet)

    acc_ln = h2_line(text, "acceptance")
    if not acc_ln:
        bad.append((1, "no `## Acceptance` section"))
    else:
        acc = section_text(text, "acceptance")
        closed, total = plan.acceptance_of("## Acceptance\n" + acc)
        if not total:
            bad.append((acc_ln, "`## Acceptance` holds no box"))
        elif closed:
            warn.append(f"{name}:{acc_ln}: {closed} of {total} boxes already "
                        "ticked before an implementer ran them")
        for i, line in enumerate(text.splitlines(), start=1):
            if i > acc_ln and line.startswith("## "):
                break
            m = i > acc_ln and BOX_TEXT_RE.match(line)
            if m and COMMIT_RE.search(m.group(1)):
                bad.append((i, "a box asks the worker to commit — committing "
                               "is the orchestrator's act"))

    ver_ln = h2_line(text, "verify")
    if not ver_ln:
        bad.append((1, "no `## Verify and Proof` section"))
    else:
        blocks = fenced(section_text(text, "verify"))
        if not blocks:
            bad.append((ver_ln, "`## Verify and Proof` holds no fenced `sh` "
                                "block"))
        elif fp and not any(p in b for b in blocks for p in fp):
            warn.append(f"{name}:{ver_ln}: the verify block names no path "
                        "under the footprint — the whole-workspace smell")

    wf = fm.get("workflow")
    if wf and not isinstance(wf, list):
        slug = str(wf).strip()
        kind = lib.get(slug, {}).get("kind")
        if kind != "workflow":
            what = ("an atomic, not a workflow" if kind == "atomic"
                    else "no workflow in the library")
            bad.append((keys.get("workflow", 1),
                        f"workflow `{slug}` names {what}"))
    return bad, warn, fp


def read_specs(prd, lib):
    """(sum, count, refusals, warnings, footprints, workflows) over every
    specs/*.md — the workflows in spec frontmatter too, in file order, the
    route a `specced` with no flag may write down."""
    sdir = os.path.join(prd["dir"], "specs")
    files = (sorted(f for f in os.listdir(sdir) if f.endswith(".md"))
             if os.path.isdir(sdir) else [])
    if not files:
        raise Refused(f"{prd['local']}/specs/: no spec file — `specced` "
                      "requires spec files on disk")
    own = prd["fm"].get("footprint", [])
    own = [str(p).rstrip("/") for p in (own if isinstance(own, list)
                                        else [own]) if p]
    total, bad, warn, feet, wfs = 0, [], [], [], []
    for f in files:
        path = os.path.join(sdir, f)
        text = open(path, encoding="utf-8").read()
        fm, _, _ = plan.parse_prd(path)
        b, w, fp = check_spec(path, fm, text, lib, own)
        bad += [f"{path}:{ln}: {msg}" for ln, msg in b]
        warn += w
        feet += fp
        wf = fm.get("workflow")
        if wf and not isinstance(wf, list) and str(wf).strip():
            wfs.append(str(wf).strip())
        if not b:
            total += int(str(fm.get("complexity")))
    return total, len(files), bad, warn, feet, wfs


def limits(board_path):
    """{key: int} for `split-above` and `specs-above` from one board's
    `settings.md` — the PRD's own, so a master reads each member's. A key
    missing or not an integer reads at its default."""
    fm = plan.board_settings(board_path)
    out = {}
    for k, d in LIMITS:
        v = fm.get(k)
        try:
            out[k] = int(str(v).strip()) if v not in (None, "") \
                and not isinstance(v, list) else d
        except ValueError:
            out[k] = d
    return out


def library(board, prd):
    """The workflow library a spec's `workflow:` resolves in — the PRD's own
    board first, then the master's, the order `needs:` resolves in."""
    lib = {}
    for b in (prd.get("board_path"), board):
        if b:
            for k, v in wflib.scan(b).items():
                lib.setdefault(k, v)
    return lib


def find_prd(board, name):
    prds = plan.scan(board)
    rel = trlib.resolve(prds, name)
    return prds, rel, prds[rel]



# ── route drafting ──────────────────────────────────────────────────────────
# `## Route` closes a report when no library workflow fits: the workflow body
# (`## Use when`, `## Steps`) verbatim, then one `### atomic <slug>` block per
# step whose atomic the library does not hold. Route is always the report's
# last section, so this reads raw text after the heading rather than the
# flat `section_text` splitter above — that splitter treats every `## ` line
# as a sibling, and the workflow body's own `## Use when` / `## Steps` would
# be read right off Route instead of staying nested in it.

ATOMIC_HDR_RE = re.compile(r"(?m)^###\s+atomic\s+(\S+)\s*$")


def route_text(text):
    """Everything after `## Route`, verbatim. None when the heading is
    absent."""
    m = re.search(r"(?m)^##\s+Route\s*$", text)
    return text[m.end():].lstrip("\n") if m else None


def route_parts(text):
    """(workflow_body, [(slug, body)]) — `## Route`'s raw text split on
    `### atomic <slug>` boundaries, the only split that respects nesting."""
    raw = route_text(text)
    if raw is None:
        raise Refused("no `## Route` on stdin")
    pieces = ATOMIC_HDR_RE.split(raw)
    wf_body = pieces[0].strip("\n")
    if not wf_body:
        raise Refused("`## Route` holds no workflow body before its first "
                      "`### atomic` block")
    atoms = []
    for i in range(1, len(pieces), 2):
        slug, body = pieces[i].strip(), pieces[i + 1].strip("\n")
        if not SLUG_RE.match(slug):
            raise Refused(f"`### atomic {slug}` is not a slug")
        if not body.strip():
            raise Refused(f"`### atomic {slug}` holds no body")
        atoms.append((slug, body))
    return wf_body, atoms


def draft_route(board, slug, report, subject, date):
    """Write the workflow and its new atomics from `## Route`, run `workflow
    check` over the whole library, and roll every file this call wrote back
    on red — the call refused, nothing written. A step naming an atomic
    already in the library writes no file; its `why` cell, when the block IS
    new, becomes that atomic's `subject`."""
    wf_body, atoms = route_parts(report)
    rows = wflib.steps(wf_body) or []
    why = {r["atomic"]: r["why"] for r in rows}
    written = []
    try:
        written.append(wflib.add(board, slug, "workflow", subject, wf_body,
                                 date))
        for atom_slug, body in atoms:
            written.append(wflib.add(board, atom_slug, "atomic",
                                     why.get(atom_slug, "").strip()
                                     or atom_slug, body, date))
    except ValueError as e:
        for p in written:
            os.remove(p)
        raise Refused(str(e))
    bad = wflib.check(board)
    if bad:
        for p in written:
            os.remove(p)
        raise Refused("`## Route` failed `workflow check` — nothing "
                      "written:\n" + "\n".join(bad))
    return written


# ── specced ───────────────────────────────────────────────────────────────────

def specced(board, args, persona):
    """validate the specs, sum the weight, set `specced`"""
    blast, workflow = args.opt.get("blast"), args.opt.get("workflow")
    route = args.opt.get("route")
    check = "check" in args.flags
    prds, rel, prd = find_prd(board, args.pos[0])
    if blast is not None and blast not in BLASTS:
        raise Refused(f"--blast `{blast}` is not one of {'|'.join(BLASTS)}")
    lib = library(board, prd)
    if workflow == "none" and route is None:
        raise Refused("`--workflow none` is refused — draft the route as "
                      "`## Route` on stdin with `--route -`, or follow one "
                      "already in the library")
    if route is not None:
        if not workflow or workflow == "none":
            raise Refused("`--route` needs `--workflow <new-slug>`")
        if lib.get(workflow, {}).get("kind") == "workflow":
            raise Refused(f"--workflow `{workflow}` is already in the "
                          "library — `--route` is refused, the route "
                          "exists: follow it")
    elif workflow and workflow != "none" and \
            lib.get(workflow, {}).get("kind") != "workflow":
        raise Refused(f"--workflow `{workflow}` names no workflow in the "
                      "library")
    total, count, bad, warn, feet, spec_wfs = read_specs(prd, lib)
    for w in warn:
        print(f"warn: {w}", file=sys.stderr)
    if bad:
        raise Refused("\n".join(bad))
    lim = limits(prd["board_path"])
    over = [f"over {k}: {n} > {lim[k]} — REFINE it"
            for k, n in (("split-above", total), ("specs-above", count))
            if n > lim[k]]
    if over:
        raise Refused("\n".join(over))
    # A route the analyst already wrote down survives the transition: with no
    # `--workflow` named and none on the PRD, a spec's own `workflow:` is
    # written up onto it — the way `refine` hands a parent's slug down. The
    # flag still wins every time it is present, and nothing here overwrites a
    # key the PRD already carries. Specs naming different slugs answer to no
    # one slug: the PRD key stays unset and the operator is told which.
    if workflow is None and not prd["fm"].get("workflow"):
        seen = list(dict.fromkeys(spec_wfs))
        if len(seen) == 1:
            workflow = seen[0]
        elif len(seen) > 1:
            print(f"note: {len(seen)} specs name different workflows — "
                  f"{', '.join(seen)} — none written to the PRD; pass "
                  "--workflow <slug> to set one", file=sys.stderr)
    written = []
    if route is not None:
        report = sys.stdin.read() if route == "-" else \
            open(route, encoding="utf-8").read()
        written = draft_route(board, workflow, report, prd["title"],
                              datetime.date.today().isoformat())
    if check:
        for p in written:
            os.remove(p)
        print(f"{rel}: ok · complexity {total} · footprint "
              + ", ".join(sorted(set(feet))))
        return 0
    if prd["state"] not in SPECCED_FROM:
        for p in written:
            os.remove(p)
        raise Refused(f"{rel} is `{prd['state']}` — `specced` is set from "
                      f"`{SPECCED_FROM[0]}` (@references/parts/states.md)")
    path = os.path.join(prd["dir"], "prd.md")
    if args.dry:
        for p in written:
            os.remove(p)
        frm, fm = prd["state"], prd["fm"]
        prd["state"] = fm["state"] = "specced"
        fm["complexity"] = str(total)
        if blast is not None:
            fm["blast-radius"] = blast
        if workflow == "none":
            fm.pop("workflow", None)
        elif workflow:
            fm["workflow"] = workflow
        fm.pop("claim", None)
        line = trlib.dry_line(board, prds, rel, frm, "specced", persona)
        trlib.say_dry(board, line, [path, os.path.join(
            prd["board_path"], trlib.TRANSITIONS_FILE)])
        if workflow is not None:
            print(f"dry · workflow: {workflow}")   # the key the real write sets
        return 0
    edit.set_key(path, "complexity", str(total))
    if blast is not None:
        edit.set_key(path, "blast-radius", blast)
    if workflow == "none":
        edit.del_key(path, "workflow")
    elif workflow:
        edit.set_key(path, "workflow", workflow)
    edit.del_key(path, "claim")
    edit.set_key(path, "state", "specced")
    trlib.record(prd, prd["state"], "specced")
    print(trlib.progress_line(board, rel, prd["state"], "specced", persona))
    return 0


# ── refine ────────────────────────────────────────────────────────────────────

def split_table(text):
    """The rows of the `## Split` table in a report: [(child, contract,
    [needs])]. The header and its separator are skipped by shape, not by
    position, so a report that repeats the header still reads."""
    body = section_text(text, "split")
    if not body:
        raise Refused("no `## Split` table on stdin")
    rows = []
    for line in body.splitlines():
        m = wflib.ROW_RE.match(line)
        if not m or wflib.SEP_RE.match(line):
            continue
        cells = [c.strip().strip("`").strip() for c in m.group(1).split("|")]
        if len(cells) < 2:
            raise Refused(f"a `## Split` row with one cell: {line.strip()}")
        child, contract = cells[0], cells[1]
        if child.lower() == "child" and contract.lower() == "contract":
            continue
        needs = [n.strip().strip("`")
                 for n in re.split(r"[,·]", cells[2] if len(cells) > 2
                                   else "")]
        rows.append((child, contract,
                     [n for n in needs if n.lower() not in NONE_NEEDS]))
    if not rows:
        raise Refused("the `## Split` table is empty")
    return rows


def child_prd(parent_fm, child, contract, needs):
    """A child's prd.md: the template as `add` writes it — `open`, the
    contract as the body's first paragraph — with `origin`, `repo` and
    `workflow` the parent's, `priority` the parent's, `needs:` as given."""
    text = trlib.from_template(f"{child} — {contract}",
                               parent_fm.get("priority", 0) or 0, contract)
    head, fm, tail = edit.split_fm(text)
    inherit = {k: parent_fm[k] for k in ("origin", "from", "repo", "workflow")
               if parent_fm.get(k) and not isinstance(parent_fm[k], list)}
    out = []
    for line in fm:
        m = re.match(r"^(\w[\w-]*):\s*(.*?)(\s+#.*)?$", line.rstrip("\n"))
        if m and m.group(1) in inherit:
            line = f"{m.group(1)}: {inherit.pop(m.group(1))}{m.group(3) or ''}\n"
        out.append(line)
    out += [f"{k}: {v}\n" for k, v in inherit.items()]
    if needs:
        out.append("needs:\n")
        out += [f"  - {n}\n" for n in needs]
    return head + "".join(out) + tail


def refine(board, args, persona):
    """split a PRD into children from the analyst's `## Split` table"""
    prds, rel, prd = find_prd(board, args.pos[0])
    if prd["state"] not in REFINE_FROM:
        raise Refused(f"{rel} is `{prd['state']}` — `refine` splits a PRD "
                      f"that is {' or '.join(f'`{s}`' for s in REFINE_FROM)}")
    rows = split_table(sys.stdin.read())
    names = [c for c, _, _ in rows]
    dup = sorted({c for c in names if names.count(c) > 1})
    if dup:
        raise Refused("a child named twice in the table: " + ", ".join(dup))
    on_disk = {os.path.basename(c) for c in prd["children"]}
    for c, _, needs in rows:
        if not SLUG_RE.match(c):
            raise Refused(f"child `{c}` is not a directory name")
        for n in needs:
            if n not in names and n not in on_disk:
                raise Refused(f"child `{c}` needs `{n}`, which is no sibling "
                              "in the table")
    exists = lambda c: os.path.isdir(os.path.join(prd["dir"], c))  # noqa
    new = [(c, k, n) for c, k, n in rows if not exists(c)]
    old = [c for c, _, _ in rows if exists(c)]
    parent = os.path.join(prd["dir"], "prd.md")
    if args.dry:
        paths = []
        for c, k, n in new:
            trlib.fake_prd(board, f"{rel}/{c}", child_prd(prd["fm"], c, k, n),
                           prds)
            paths.append(os.path.join(prd["dir"], c, "prd.md"))
            print(f"dry · {rel}/{c}: open"
                  + (f" · needs {', '.join(n)}" if n else ""))
        if new:
            paths.append(parent)
            frm, fm = prd["state"], prd["fm"]
            fm.pop("claim", None)
            if frm != "open":
                prd["state"] = fm["state"] = "open"
                paths.append(os.path.join(prd["board_path"],
                                          trlib.TRANSITIONS_FILE))
                trlib.say_dry(board, trlib.dry_line(board, prds, rel, frm,
                                                    "open", persona), paths)
            else:
                trlib.say_dry(board, f"{rel}: {len(new)} children under "
                              "## Children, claim cleared", paths)
        if old:
            raise Refused(f"{len(old)} child(ren) already exist, left as "
                          f"they are: {', '.join(old)}")
        return 0
    for c, k, n in new:
        d = os.path.join(prd["dir"], c)
        os.makedirs(d)
        edit.write_atomic(os.path.join(d, "prd.md"),
                          child_prd(prd["fm"], c, k, n))
        print(f"{rel}/{c}: open" + (f" · needs {', '.join(n)}" if n else ""))
    if new:
        table = "\n".join(f"| `{c}` | {k} | {', '.join(n) or '—'} |"
                          for c, k, n in new)
        body = open(parent, encoding="utf-8").read()
        edit.append_section(parent, "Children",
                            table if "## Children" in body
                            else CHILD_HEADER + "\n" + table)
        edit.del_key(parent, "claim")
        if prd["state"] != "open":
            edit.set_key(parent, "state", "open")
            trlib.record(prd, prd["state"], "open")
            print(trlib.progress_line(board, rel, prd["state"], "open",
                                      persona))
    if old:
        raise Refused(f"{len(old)} child(ren) already exist, left as they "
                      f"are: {', '.join(old)}")
    return 0


# ── entry ─────────────────────────────────────────────────────────────────────

# The declaration — transitions.py `Args` is the parser, and `--help` prints
# the same list.
FLAGS = {
    "specced": trlib.Flags(("as", "board", "blast", "workflow", "route"),
                           ("check",) + trlib.DRY),
    "refine":  trlib.Flags(("as", "board"), trlib.DRY),
}


def _command(name, fn):
    def call(argv):
        try:
            args = trlib.Args(argv, FLAGS[name], name)   # before any read
            if not args.pos:
                raise Refused(f"which PRD? — `{name} <prd>`")
            persona = (args.opt.get("as")
                       or os.environ.get("PEARDE_AS", "")).strip()
            if not persona:
                raise Refused("persona: `--as <id>` or PEARDE_AS in the "
                              "environment — the line is the only record of it")
            board = plan.find_board(args.opt.get("board"))
            return fn(board, args, persona)
        except trlib.FlagRefused as e:
            print(f"pearde {name}: {e}", file=sys.stderr)
            return 2
        except Refused as e:
            print(f"pearde {name}: refused — {e}", file=sys.stderr)
            return 1
    call.__doc__ = fn.__doc__
    call.__name__ = name
    call.flags = FLAGS[name]
    return call


# What the dispatcher discovers: name → callable taking the argument list
# after the command name, returning the exit code.
COMMANDS = {"specced": _command("specced", specced),
            "refine": _command("refine", refine)}


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
