#!/usr/bin/env python3
"""PROBE — uncommitted. The break-it proof, end to end, driving the shipped
`plan` command over a real board.

The proof this PRD specifies could not be run as written: its fixture,
`@realm/done-means-done/realm-classify`, no longer carries an open `prd.md`
box to tick, and both PRDs the memo predicts in `collect:` are now
`state: done` — not a HOLDING_STATE, so neither can reach `collect` under any
matcher. This runs the same propositions against a fixture that exists.

Creates and removes `prds/__probe/` around each run. Changes no board file
that was there before it, and no code.
"""
import os, shutil, subprocess, sys, textwrap

# the repo root, three levels up: probe/ -> the PRD folder -> prds/ -> the repo.
# The probes live inside the PRD they were written for, where `index.py check`
# does not see them: `prds/` is outside the manifest scan.
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
BOARD = os.path.join(REPO, "prds")
PROBE = os.path.join(BOARD, "__probe")
PLAN = os.path.join(REPO, "resources", "board", "plan.py")


def write(rel, text):
    p = os.path.join(PROBE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(textwrap.dedent(text).lstrip())


def make_fixture(body_box):
    """A held PRD whose every spec box is closed. `body_box` is the extra line
    dropped into its `prd.md` — the only thing that varies between runs."""
    shutil.rmtree(PROBE, ignore_errors=True)
    write("prd.md", f"""
        ---
        state: claimed
        priority: 9
        complexity: 1
        claim: probe 2026-08-28 00:00
        ---

        # __probe — a held PRD whose specs are closed

        Every acceptance box in its spec is `[x]`, so `collect` turns entirely
        on what `body_has_open_box` reads in this file.

        {body_box}
    """)
    write("specs/spec01.md", """
        ---
        complexity: 1
        footprint:
          - probe/nothing
        ---

        # spec01 — nothing

        ## Acceptance

        - [x] the only box, closed

        ## Verify

        `true`
    """)


def in_collect(plan_py):
    """Whether the shipped `plan` command offers __probe for collection."""
    r = subprocess.run([sys.executable, plan_py, "plan", BOARD],
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"{plan_py} failed:\n{r.stderr}")
    lines = r.stdout.splitlines()
    for i, l in enumerate(lines):
        if l.startswith("collect:"):
            block = []
            for x in lines[i + 1:]:
                if not x.startswith("  "):
                    break
                block.append(x)
            return any("__probe" in x for x in block), l
    return False, "(no collect line — 0 finished)"


# HEAD's plan.py has to run from its own directory: it imports `memos` and
# `questions` from one level up, relative to __file__.
HEAD_PLAN = os.path.join(REPO, "resources", "board", "_plan_at_HEAD.py")
subprocess.run(f"git -C {REPO} show HEAD:resources/board/plan.py > {HEAD_PLAN}",
               shell=True, check=True)

# The label is backtick-quoted so a line of this table is not itself a
# rendered open box. The output of this probe gets pasted into an acceptance
# box, and `body_has_open_box` reads a `prd.md` line by line with no idea
# what a code fence is — an unquoted `- [ ] the literal spelling` in the
# evidence would suppress the very PRD the evidence closes. The planted text
# in the second column is the real thing and is not quoted.
CASES = [
    ("clean prd.md, no box at all", ""),
    ("`- [ ]` the literal spelling", "- [ ] an open box, literally spelled"),
    ("`* [ ]` a star bullet", "* [ ] an open box, star-bulleted"),
    ("`+ [ ]` a plus bullet", "+ [ ] an open box, plus-bulleted"),
    ("`-  [ ]` two spaces", "-  [ ] an open box, two spaces after the bullet"),
    ("`- []` no inner space", "- [] an open box, no space inside the brackets"),
    ("`1. [ ]` ordered", "1. [ ] an open box, ordered marker"),
    ("`- [x]` ticked", "- [x] a closure"),
    ("`- [~]` struck", "- [~] a closure, struck with a reason"),
]

print(f"board: {BOARD}")
print(f"{'fixture prd.md carries':34} {'HEAD 6cd1edf':>14} {'working tree':>14}")
print("-" * 66)
lines_seen = []
try:
    for label, box in CASES:
        make_fixture(box)
        hb, hline = in_collect(HEAD_PLAN)
        nb, nline = in_collect(PLAN)
        h = "IN collect" if hb else "suppressed"
        n = "IN collect" if nb else "suppressed"
        flag = "  <-- HOLE at HEAD" if (hb and not nb) else ""
        print(f"{label:34} {h:>14} {n:>14}{flag}")
        lines_seen.append((label, hline, nline))
finally:
    shutil.rmtree(PROBE, ignore_errors=True)
    if os.path.exists(HEAD_PLAN):
        os.remove(HEAD_PLAN)

print("\n'IN collect' on a row carrying an open box is the hole: the gates call")
print("that PRD red and the board offers it for collection.")

print("\nthe collect: lines themselves, verbatim")
for label, h, n in lines_seen:
    print(f"  {label}")
    print(f"    HEAD          {h}")
    print(f"    working tree  {n}")
