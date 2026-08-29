#!/usr/bin/env python3
"""PROBE — uncommitted. `compute_plan` computes `collect` TWICE, from two
different rules, into one payload. This measures whether they can disagree.

  HEAD:plan.py:677  tasks[].collect = standing(p)[3]   — specs AND prd.md
  HEAD:plan.py:721  all[].collect   = bool(held and total and closed == total)
                                                        — specs only

The second is the pre-decision rule. `prds/memos/done-counts-which-boxes.md`
decided the first. The view reads both: `DATA.tasks` draws the timeline and
`DATA.all` (view.js:190 `ALL = DATA.all`) feeds the list and inspector.
"""
import os, shutil, subprocess, sys, textwrap, json

# the repo root, three levels up: probe/ -> the PRD folder -> prds/ -> the repo.
# The probes live inside the PRD they were written for, where `index.py check`
# does not see them: `prds/` is outside the manifest scan.
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "resources", "board"))
import plan as P

BOARD = os.path.join(REPO, "prds")
PROBE = os.path.join(BOARD, "__probe")


def write(rel, text):
    p = os.path.join(PROBE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(textwrap.dedent(text).lstrip())


def fixture(body_box):
    shutil.rmtree(PROBE, ignore_errors=True)
    write("prd.md", f"""
        ---
        state: claimed
        priority: 9
        complexity: 1
        claim: probe 2026-08-28 00:00
        ---

        # __probe

        {body_box}
    """)
    write("specs/spec01.md", """
        ---
        complexity: 1
        footprint:
          - probe/nothing
        ---

        # spec01

        ## Acceptance

        - [x] the only box, closed

        ## Verify

        `true`
    """)


# HEAD's plan.py, run from a sibling of the real one so its relative imports
# (`memos`, `questions`, one level up from __file__) still resolve. The
# working file is never reverted.
HEAD_PLAN = os.path.join(REPO, "resources", "board", "_plan_at_HEAD.py")
subprocess.run(f"git -C {REPO} show HEAD:resources/board/plan.py > {HEAD_PLAN}",
               shell=True, check=True)
import importlib.util
_s = importlib.util.spec_from_file_location("_plan_at_HEAD", HEAD_PLAN)
H = importlib.util.module_from_spec(_s)
sys.modules["_plan_at_HEAD"] = H
_s.loader.exec_module(H)

# backtick-quoted for the same reason probe_breakit.py quotes its labels:
# this output is pasted into a `prd.md`, and an unquoted box spelling at the
# head of a line is a box, code fence or no code fence.
CASES = [("clean prd.md", ""),
         ("`- [ ]` open box in prd.md", "- [ ] still owed"),
         ("`* [ ]` open box in prd.md", "* [ ] still owed")]


def measure(M, label):
    """One payload out of module `M`, and the two `collect` fields in it."""
    prds = M.scan(BOARD)
    mp = M.load_map(BOARD)[0]
    pay = M.gantt_payload(BOARD, prds, mp, M.board_settings(BOARD))
    t = next((x for x in pay["tasks"] if x["rel"] == "__probe"), None)
    a = next((x for x in pay["all"] if x["rel"] == "__probe"), None)
    tc, ac = t and t["collect"], a and a["collect"]
    flag = "   <-- TWO ANSWERS, ONE PAYLOAD" if tc != ac else ""
    print(f"  {label:14} tasks[].collect={tc!r:<6} all[].collect={ac!r:<6} "
          f"counts.collect={pay['counts']['collect']}{flag}")
    return tc == ac


try:
    agree = {"HEAD 6cd1edf..": True, "working tree": True}
    for label, box in CASES:
        fixture(box)
        # a plan first, so the fixture has a schedule row and reaches tasks[]
        # — this is what serve.py's /payload sees on every file change
        subprocess.run([sys.executable, os.path.join(REPO, "resources", "board",
                                                     "plan.py"), "plan", BOARD],
                       capture_output=True, text=True)
        print(f"{label}")
        agree["HEAD 6cd1edf.."] &= measure(H, "HEAD")
        agree["working tree"] &= measure(P, "working tree")
finally:
    shutil.rmtree(PROBE, ignore_errors=True)
    if os.path.exists(HEAD_PLAN):
        os.remove(HEAD_PLAN)

print()
for k, v in agree.items():
    print(f"{k}: the two spellings agree on every fixture: {v}")
