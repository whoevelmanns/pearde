#!/usr/bin/env python3
"""orphans — every done PRD whose footprint never reached the branch that
holds it.

    orphans [<board>…] [--board <path>] [--json]

A board may be its own git worktree of the code repo's store — `.pearde` on
branch `pearde`, the code on `main`, one object store between them. `git log
--all` from either worktree sees every branch of that store, so "which repo
holds sha X" is a question that cannot fail. The check that can is per branch:
a footprint path must have a commit on the branch its worktree actually checks
out. A path a misdirected commit put on the board branch and never on the code
branch is what this scan is for.

Classes, per footprint path of a done PRD:

    ok             a commit on the branch that holds it
    branch-only    a commit on the OTHER worktree's branch, never its own —
                   a misdirected commit's residue, for a person to re-commit
    nowhere        no commit on either branch, the file on disk — uncommitted
    absent         no commit, not on disk — a stale footprint spelling

Boards: the ones named on the line, else every board in
@resources/board/state/serve.json. A PRD's `repo:` key names its own code
repo and wins over the board's — collect's `repo_of()` honours it the same
way. Exit 0 when the scan ran and no path is `branch-only`, 1 when any is.

Reads only. It commits nothing and writes nothing outside stdout — a person
does the re-commits the list names.

Cost: two `git log` calls per footprint path of a done PRD; no `--all`, no
index rebuild.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plan as planlib          # noqa: E402
import transitions as translib  # noqa: E402

SERVE = os.path.join(HERE, "state", "serve.json")
FLAGS = planlib.Flags(("board",), ("json",))
FLAGGED = ("branch-only", "nowhere", "absent")


def git(repo, *args):
    """stdout of one git call, "" on any failure — a missing repo, a branch
    that is not there, git itself absent. Never raises."""
    try:
        r = subprocess.run(["git", "-C", repo, *args],
                           capture_output=True, text=True, timeout=120)
        return r.stdout if r.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def branch_holds(repo, branch, rel):
    """Does `branch` carry a commit touching `rel`? One branch, never `--all`
    — the shared store makes `--all` answer yes for both worktrees."""
    if not branch:
        return False
    return bool(git(repo, "log", branch, "--oneline", "--", rel).strip())


def board_git(board):
    """(nested, code, code_branch, board_branch).

    `nested` is true when the board dir is its own worktree of the code
    repo's store — the shape a misdirected commit can bite. `code` is the
    code worktree's root, `code_branch` and `board_branch` the two branches
    (the same one when the board is a plain directory inside the repo)."""
    gd = git(board, "rev-parse", "--git-dir").strip()
    nested = bool(gd) and "worktrees" in gd
    if nested:
        common = git(board, "rev-parse", "--path-format=absolute",
                     "--git-common-dir").strip() or os.path.dirname(gd)
        code = re.sub(r"/\.git/?$", "", os.path.realpath(common))
        board_branch = git(board, "rev-parse", "--abbrev-ref", "HEAD").strip()
    else:
        code = os.path.realpath(
            git(board, "rev-parse", "--show-toplevel").strip() or board)
        board_branch = ""
    code_branch = git(code, "rev-parse", "--abbrev-ref", "HEAD").strip()
    return nested, code, code_branch, (board_branch or code_branch)


def repo_of(prd, ctx):
    """(repo, branch) a PRD's footprint is written against: its `repo:` key
    and that repo's own checked-out branch when it has one, else the board's
    code worktree and branch. A named repo is its own repo — its HEAD is the
    branch that must hold the footprint, never the board's."""
    _, code, code_branch, _ = ctx
    named = str(prd["fm"].get("repo", "") or "").strip()
    if not named:
        return code, code_branch
    cand = named if named.startswith(("/", "~")) else os.path.join(code, named)
    top = git(os.path.expanduser(cand), "rev-parse", "--show-toplevel").strip()
    if not top:
        return code, code_branch
    top = os.path.realpath(top)
    return top, git(top, "rev-parse", "--abbrev-ref", "HEAD").strip()


def absolute_class(path):
    """An absolute footprint path's class, read against the repo that path
    itself sits in — no board resolves it, so the path is its own address."""
    real = os.path.realpath(os.path.expanduser(path))
    if not os.path.exists(real):
        return "absent"
    top = git(os.path.dirname(real), "rev-parse", "--show-toplevel").strip()
    if not top:
        return "nowhere"
    top = os.path.realpath(top)
    branch = git(top, "rev-parse", "--abbrev-ref", "HEAD").strip()
    return ("ok" if branch_holds(top, branch, os.path.relpath(real, top))
            else "nowhere")


def classify(path, repo, repo_branch, ctx, broot):
    """One footprint path's class. `repo`/`repo_branch` are what the path is
    written against — `repo_of`'s pair; `ctx` is `board_git`'s tuple."""
    nested, code, code_branch, board_branch = ctx
    if path.startswith("/"):
        # an absolute footprint is left as written — that is how a deliberate
        # cross-repo overlap is spelled. It answers to its own repo's branch
        return absolute_class(path)
    real = os.path.realpath(os.path.join(repo, path))
    if nested and real.startswith(broot + os.sep):
        # a record path: written from the code worktree, committed on the
        # board branch at its board-relative spelling
        rel = os.path.relpath(real, broot)
        if branch_holds(code, board_branch, rel):
            return "ok"
    else:
        if branch_holds(repo, repo_branch, path):
            return "ok"
        if nested and board_branch != code_branch \
                and branch_holds(code, board_branch, path):
            return "branch-only"
    return "nowhere" if os.path.exists(real) else "absent"


def done_times(board):
    """{prd: done-transition row} from the board's `.state/transitions.jsonl`
    — the first `to: done` per PRD. {} where a board keeps no such file."""
    out = {}
    path = os.path.join(board, planlib.STATE_DIR, "transitions.jsonl")
    if not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("to") == "done":
                out.setdefault(row.get("prd", ""), row)
    return out


def scan_board(board):
    """[row] — one per done PRD, in PRD order. A PRD with no footprint gets a
    bare row: it is in the `done` count and in no other."""
    ctx = board_git(board)
    broot = os.path.realpath(board)
    trans = done_times(board)
    rows = []
    for rel, prd in sorted(planlib._scan_one(board).items()):
        if prd["state"] != "done":
            continue
        feet = planlib.spec_data(prd)[1]
        if not feet:
            rows.append({"prd": rel, "paths": {}})
            continue
        repo, repo_branch = repo_of(prd, ctx)
        paths = {f: classify(f, repo, repo_branch, ctx, broot) for f in feet}
        # `commit:` may be annotated prose — keep the sha-like tokens
        shas = re.findall(r"\b[0-9a-f]{7,40}\b",
                          str(prd["fm"].get("commit", "") or ""))
        t = prd["fm"].get("time")
        rows.append({
            "board": board, "prd": rel,
            "repo": repo, "repo_branch": repo_branch,
            "nested_worktree": ctx[0],
            "code_branch": ctx[2], "board_branch": ctx[3],
            "paths": paths,
            "missing": [f for f, c in paths.items() if c in FLAGGED],
            "commit": " ".join(shas) or "-",
            "actual": (t.get("actual", "") if isinstance(t, dict) else ""),
            "done_at": trans.get(rel, {}).get("t", ""),
        })
    return rows


def resolve(arg):
    """A board dir from what a person typed: the repo root holding `.pearde`,
    the `.pearde` dir itself, or a board dir under any other name."""
    p = os.path.abspath(os.path.expanduser(arg))
    inner = os.path.join(p, planlib.BOARD_DIR)
    return inner if os.path.isdir(inner) else p


def boards_from(named):
    """The boards to scan: the ones named, else serve.json's. A registered
    path that is not a directory is dropped — a board can be registered and
    gone. A named one that is not is a usage error, not a silent skip."""
    if named:
        return [resolve(b) for b in named]
    try:
        with open(SERVE, encoding="utf-8") as fh:
            regd = json.load(fh)
    except (OSError, ValueError):
        return []
    return [b for b in sorted(regd) if os.path.isdir(b)]


def cmd_orphans(argv, board=None):
    """The entry: `orphans [<board>…] [--board <path>] [--json]`. Exit 0 when
    the scan ran and no footprint path is `branch-only`, 1 when any is, 2 on
    usage."""
    try:
        a = translib.Args(argv, FLAGS, "orphans")
    except translib.FlagRefused as e:
        print(f"orphans: {e}", file=sys.stderr)
        return 2
    named = list(a.pos) + [x for x in (a.opt.get("board"), board) if x]
    rows = []
    for b in boards_from(named):
        if not os.path.isdir(b):
            print(f"orphans: no board at {b}", file=sys.stderr)
            return 2
        rows += scan_board(b)
    footed = [r for r in rows if r["paths"]]
    orphans = [r for r in footed if r["missing"]]
    residue = [r for r in orphans
               if any(c == "branch-only" for c in r["paths"].values())]
    counts = {"done": len(rows), "with_footprints": len(footed),
              "flagged": len(orphans), "branch_only": len(residue)}
    if "json" in a.flags:
        json.dump({**counts, "rows": footed}, sys.stdout, indent=1)
        print()
        return 1 if residue else 0
    for r in orphans:
        print(f"ORPHAN {r['board']} {r['prd']}")
        print(f"  commit: {r['commit']} · actual: {r['actual'] or '-'}"
              f" · done: {r['done_at'] or '-'}")
        for cls in FLAGGED:
            for f in [f for f, c in r["paths"].items() if c == cls]:
                print(f"  {cls}: {f}")
    print(f"done PRDs: {counts['done']} · with footprints: "
          f"{counts['with_footprints']} · flagged: {counts['flagged']}"
          f" · branch-only (bug residue): {counts['branch_only']}")
    return 1 if residue else 0


cmd_orphans.flags = FLAGS       # what `pearde orphans --help` prints
COMMANDS = {"orphans": cmd_orphans}


if __name__ == "__main__":
    sys.exit(cmd_orphans(sys.argv[1:]))
