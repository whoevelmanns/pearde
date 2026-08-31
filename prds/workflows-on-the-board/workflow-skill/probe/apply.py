#!/usr/bin/env python3
"""apply.py <root> — register `pearde-workflow` in every place a skill is
registered. Idempotent: a hunk already present is skipped, not doubled.
Every replacement asserts it matched exactly once, so a file another session
rewrote fails loudly here instead of landing half a hunk."""
import os
import sys

ROOT = os.path.abspath(sys.argv[1])
FAIL = []


def sub(rel, old, new, once=True):
    p = os.path.join(ROOT, rel)
    t = open(p, encoding="utf-8").read()
    if new in t:
        print(f"  = {rel}: already applied")
        return
    n = t.count(old)
    if n != 1:
        FAIL.append(f"{rel}: anchor matched {n} times, expected 1 — {old[:60]!r}")
        return
    open(p, "w", encoding="utf-8").write(t.replace(old, new, 1) if once else t.replace(old, new))
    print(f"  + {rel}")


# 1 — SKILL.md: the name in the description's list of skills.
#     `pearde-report` is added with it: the list named ten of the eleven files
#     in skills/, and this build is the reader that noticed.
sub("SKILL.md",
    "pearde, pearde-drill, pearde-memo, pearde-view, pearde-master, "
    "pearde-doctor, pearde-persona, pearde-persona-ask, "
    "pearde-persona-create, pearde-scout —",
    "pearde, pearde-drill, pearde-memo, pearde-view, pearde-report, "
    "pearde-master, pearde-doctor, pearde-persona, pearde-persona-ask, "
    "pearde-persona-create, pearde-scout, pearde-workflow —")

# 2 — references/parts/handles.md: the six rows, and the skills line.
sub("references/parts/handles.md",
    "`pearde-persona-ask`, `pearde-persona-create`, `pearde-scout`. "
    "Typed inside a round they are the",
    "`pearde-persona-ask`, `pearde-persona-create`, `pearde-scout`, "
    "`pearde-workflow`. Typed inside a round they are the")

MEMO_ROW = ("| record a decision            | `memo <subject>` — "
            "`prds/memos/<slug>.md` from `@references/templates/memo.md`"
            "                            | `pearde memo add <subject>` |")
WF_ROWS = "\n".join([
    MEMO_ROW,
    "| the workflow library         | `workflow` — `@resources/workflows.py list`: slug · kind · runs · updated · subject, per `@@workflows` | `pearde workflow list` |",
    "| one, as a worker sees it     | `workflow <slug>` — `@resources/workflows.py brief`: the `## Use when`, then every step with its atomic inlined. `show` when the slug is an atomic — an atomic is shown, not briefed, and `brief` exits 1 on one | `pearde workflow brief <slug>` |",
    "| a new atomic                 | `workflow add atomic <subject>` — a file from `@references/templates/atomic.md`, slugged as a memo is, at `runs: 0`. An orchestrator write, and only from a job that recurred | — |",
    "| a new workflow               | `workflow add <subject>` — a file from `@references/templates/workflow.md`; every atomic a step names exists first, or the step sends a worker nowhere | — |",
    "| attach a workflow to a PRD   | `workflow attach <prd> <slug>` — writes `workflow:` on that `prd.md`. An orchestrator write; the drill writes it on the tree it produces | — |",
    "| check the library            | `workflow check` — `@resources/workflows.py check`: one problem per line, silent when clean. The `doctor` row alone | `pearde workflow check` |",
])
sub("references/parts/handles.md", MEMO_ROW, WF_ROWS)

# 3 — index.md: `@@skills` gains the file; `@@workflows` gains it first.
sub("index.md",
    "@skills/pearde-persona-create.md · @skills/pearde-scout.md · "
    "@references/install.md |",
    "@skills/pearde-persona-create.md · @skills/pearde-scout.md · "
    "@skills/pearde-workflow.md · @references/install.md |")
sub("index.md",
    "| `@@workflows` | how a kind of job is done, and improved on every run "
    "| @references/workflow.md ·",
    "| `@@workflows` | how a kind of job is done, and improved on every run "
    "| @skills/pearde-workflow.md · @references/workflow.md ·")

# 4 — references/files.md: the row in the skills table. Appended after the
#     last row so the `@resources/board/transitions.py` reorder this tree
#     already carried is left exactly where it sits.
sub("references/files.md",
    "| @skills/pearde-scout.md | ranked discovery, the route index, and the "
    "quality gates | `@@scout` |",
    "| @skills/pearde-scout.md | ranked discovery, the route index, and the "
    "quality gates | `@@scout` |\n"
    "| @skills/pearde-workflow.md | how a kind of job is done, and improved "
    "on every run | `@@workflows` |")

# 5 — README.md: the count, the scope row, the lookup row.
sub("README.md", "for the eleven skills", "for the twelve skills")
sub("README.md",
    "| doing the work | `@@workers` · `@@specs` · `@@personas` · `@@consult` "
    "· `@@drill` · `@@language` |",
    "| doing the work | `@@workers` · `@@specs` · `@@workflows` · "
    "`@@personas` · `@@consult` · `@@drill` · `@@language` |")
sub("README.md",
    "| putting one problem to a colleague | @references/parts/consult.md |",
    "| putting one problem to a colleague | @references/parts/consult.md |\n"
    "| what a worker follows, and how a run improves it | "
    "@references/parts/workflows.md |")

# 6 — references/system.md: the bullet, and `workflow` in the handles line.
sub("references/system.md",
    "- **Deciding** — a call the code will not explain goes in",
    "- **Following** — a job that recurs is a `workflow`: an ordered route of\n"
    "  atomics a worker follows, named by `workflow:` on a PRD or a spec, and\n"
    "  handed to that worker expanded. A run returns its edits; only the\n"
    "  orchestrator writes the library, and only from a run. `@@workflows`.\n"
    "- **Deciding** — a call the code will not explain goes in")
sub("references/system.md",
    "`unblock <prd>`, `sweep`, `collect`, `run <prd>`, `memo <subject>`, "
    "`plan`, `view`,",
    "`unblock <prd>`, `sweep`, `collect`, `run <prd>`, `memo <subject>`, "
    "`workflow [<slug>]`, `plan`, `view`,")

# 7 — prds/the-board-runs-itself/readme-in-three-rings/probe/ — four literals
#     this contract moves. The matchers are honest: README claims a skill
#     count and a lookup-table size, and a twelfth skill plus one more
#     lookup row change both numbers. The rule each asserts does not move;
#     only the number it compares against does. This is outside the PRD's
#     own folder, so spec01 carries it as its own acceptance box.
sub('prds/the-board-runs-itself/readme-in-three-rings/probe/verify.sh',
    'eq  "E the one-question table has its ten rows" "$(printf \'%s\\n\' "$RINGS" | grep -c \'^| what\\|^| which\\|^| who \\|^| putting\')" "10"',
    'eq  "E the one-question table has its eleven rows" "$(printf \'%s\\n\' "$RINGS" | grep -c \'^| what\\|^| which\\|^| who \\|^| putting\')" "11"')
sub('prds/the-board-runs-itself/readme-in-three-rings/probe/verify.sh',
    'eq  "F eleven skills" "$(ls "$ROOT/skills"/*.md | wc -l | tr -d \' \')" "11"',
    'eq  "F twelve skills" "$(ls "$ROOT/skills"/*.md | wc -l | tr -d \' \')" "12"')
sub('prds/the-board-runs-itself/readme-in-three-rings/probe/quickstart.sh',
    'eq  "1 the skills dir holds eleven folders" "$(find "$SKILLS" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d \' \')" "11"',
    'eq  "1 the skills dir holds twelve folders" "$(find "$SKILLS" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d \' \')" "12"')
sub('prds/the-board-runs-itself/readme-in-three-rings/probe/quickstart.sh',
    'eq  "1 each folder holds the five links" "$(find "$SKILLS" -mindepth 2 -maxdepth 2 -type l | wc -l | tr -d \' \')" "55"',
    'eq  "1 each folder holds the five links" "$(find "$SKILLS" -mindepth 2 -maxdepth 2 -type l | wc -l | tr -d \' \')" "60"')

if FAIL:
    print("\n".join("  ! " + f for f in FAIL), file=sys.stderr)
    sys.exit(1)
print("apply: 15 hunks")
