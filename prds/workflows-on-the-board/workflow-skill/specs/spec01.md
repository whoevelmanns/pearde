---
complexity: 14
workflow: implement-a-spec
footprint:
  - skills/pearde-workflow.md
  - SKILL.md
  - references/parts/handles.md
  - index.md
  - references/files.md
  - README.md
  - references/system.md
  - prds/workflows-on-the-board/workflow-skill/probe/
  - prds/the-board-runs-itself/readme-in-three-rings/probe/verify.sh
  - prds/the-board-runs-itself/readme-in-three-rings/probe/quickstart.sh
---

# spec01 — the door: one skill file, and the six pages that must name it

`pearde-workflow` becomes a skill file under `skills/`, and every place this
repo registers a skill names it. The command behind the handle already runs —
`resources/pearde.py` forwards `workflow list/show/brief/check` to
`resources/workflows.py`, and this build measured all four green — so nothing
here adds a verb, a reader or a format. What is missing is the file and the
rows: `skills/pearde-workflow.md` does not exist, and six pages enumerate the
skills without it.

**What already stands in the tree.** `prds/workflows-on-the-board/workflow-skill/probe/`
holds the finished work: `pearde-workflow.md` is the skill file, verbatim, to
be moved to `skills/`; `apply.py <root>` applies all fifteen hunks and is
idempotent; `verify.sh` proves the whole thing in a temp copy of the
skill root and prints `55 checks · 55 pass · 0 fail`. Nothing outside `probe/`
was written — the build ran entirely in a fixture, because placing the file
without the rows reddens `resources/index.py check`, and the two are therefore
one unit.

**What is left.** Move the file and apply the fifteen hunks. Leave `probe/`
where it is — the orchestrator commits it with the rest.

**Order matters.** Place `skills/pearde-workflow.md` *and* apply the rows
before running the map check. Between the two, `python3 resources/index.py check`
prints `skills/pearde-workflow.md is on disk with no row in references/files.md`;
that is the check doing its job, not a failure.

**Do not reorder `references/files.md`.** Its `@resources/board/transitions.py`
row was moved by another session before this build began (`git diff --numstat`
reads `1 1`). Add the new row where this spec says and leave that one where it
sits.

## The fifteen hunks

| file | hunk |
|---|---|
| `skills/pearde-workflow.md` | new — copied from `probe/pearde-workflow.md`, unchanged |
| `SKILL.md` | the description's skill list gains `pearde-workflow` **and `pearde-report`** — see the last box |
| `references/parts/handles.md` | the *also skills of their own* line gains `` `pearde-workflow` ``; six rows land after the `record a decision` row |
| `index.md` | `@@skills` gains `@skills/pearde-workflow.md`; `@@workflows` gains it as its **first** anchor |
| `references/files.md` | one row in the `skills/` table, after `@skills/pearde-scout.md` |
| `README.md` | `the eleven skills` → `the twelve skills`; the *doing the work* scope row gains `@@workflows`; the lookup table gains *what a worker follows, and how a run improves it* → `@references/parts/workflows.md` |
| `references/system.md` | a **Following** bullet before **Deciding**; `` `workflow [<slug>]` `` in the handles line |
| `prds/the-board-runs-itself/readme-in-three-rings/probe/verify.sh` | two literals: `"10"` → `"11"` (the lookup table gained a row) and `"11"` → `"12"` (the twelfth skill), with their labels |
| `prds/the-board-runs-itself/readme-in-three-rings/probe/quickstart.sh` | two literals: `"11"` → `"12"` folders and `"55"` → `"60"` links — five per skill folder |

`python3 prds/workflows-on-the-board/workflow-skill/probe/apply.py .` applies
all of them at once and refuses loudly if any anchor has moved.

**The last two files belong to another PRD.** `readme-in-three-rings` is
`done` at `de59bd9`, and its harness is a committed gate. Its four matchers
are honest — `README.md` claims a skill count and a lookup-table size, and
this contract moves both numbers. Only the numbers change; every rule the
harness asserts is untouched. Measured: without the bump the harness reads
`72 checks · 68 pass · 4 fail`, with it `72 checks · 72 pass · 0 fail`. If the
orchestrator would rather that file were moved by its own owner, drop the last
acceptance box and the two paths from the footprint above — the rest of this
spec still lands, and the harness stays red until someone bumps it.

## Acceptance

- [x] `skills/pearde-workflow.md` exists, its frontmatter `name:` reads exactly `pearde-workflow`, and it carries a `description:` — the two fields `resources/doctor.sh` requires of a skill.
      Ran: `test -f skills/pearde-workflow.md && sed -n '1,4p' skills/pearde-workflow.md` → exit 0, printing
      `---` / `name: pearde-workflow` / `description: How a kind of job is done, kept where the next session
      looks — …` / `---`. Both fields present; `name:` is exactly `pearde-workflow`.
- [x] The body of `skills/pearde-workflow.md` names `@references/workflow.md`, `@references/parts/workflows.md` and the scope `@@workflows`, and opens no `##` section of its own — the knowledge stays in the references.
      Ran: `grep -n '@references/workflow.md\|@references/parts/workflows.md\|@@workflows' skills/pearde-workflow.md`
      → `6:Read @references/workflow.md for the format`, `8:returns. @references/parts/workflows.md is when one is
      written`, ``9:attached, and what a run is allowed to change. The scope is `@@workflows`.``, `23:… —
      @references/parts/workflows.md is the table that decides.` And `grep -c '^##' skills/pearde-workflow.md` → `0`
      (exit 1, no match): the file opens no section of its own.
- [x] `SKILL.md`, `references/parts/handles.md`, `index.md` and `references/files.md` each contain the string `pearde-workflow`.
      Ran: `grep -c 'pearde-workflow' SKILL.md references/parts/handles.md index.md references/files.md` → exit 0:
      `SKILL.md:1`, `references/parts/handles.md:1`, `index.md:2`, `references/files.md:1`. All four ≥ 1.
- [x] `references/parts/handles.md` carries all six rows — `the workflow library`, `one, as a worker sees it`, `a new atomic`, `a new workflow`, `attach a workflow to a PRD`, `check the library` — with `pearde workflow list` and `pearde workflow check` in the Command column of the first and last, and `—` for the three that no command answers.
      Ran: `grep -nE 'the workflow library|check the library|pearde workflow (list|check)' references/parts/handles.md`
      → exit 0, lines 32 and 37. All six rows are lines 32–37; the Command column reads, in order:
      `pearde workflow list` · `pearde workflow brief <slug>` · `—` · `—` · `—` · `pearde workflow check`.
      First and last carry `pearde workflow list` / `pearde workflow check`; the three write-handles
      (`a new atomic`, `a new workflow`, `attach a workflow to a PRD`) read `—`, no command answering them.
- [x] `index.md` lists `@skills/pearde-workflow.md` in `@@skills`, and as the **first** anchor of `@@workflows`.
      Ran: `grep -n '@skills/pearde-workflow.md' index.md references/files.md` → exit 0.
      `index.md:66` — the `@@skills` row now ends `… @skills/pearde-scout.md · @skills/pearde-workflow.md ·
      @references/install.md |`. `index.md:56` — the `@@workflows` row reads `| @@workflows | how a kind of job is
      done, and improved on every run | @skills/pearde-workflow.md · @references/workflow.md · …`, the skill file
      first in the anchor list.
- [x] `README.md` reads `for the twelve skills`, and `ls skills/*.md | wc -l` prints `12` — the number and the directory agree.
      Ran: `grep -nE 'for the twelve skills|how a run improves it' README.md` → exit 0, `README.md:20`
      reading ``| `install --apply` | `✓ built <skills-dir>/<name>` for the twelve skills, …``.
      Ran: `test "$(ls skills/*.md | wc -l | tr -d ' ')" = 12 && echo "skills/ holds 12"` → `skills/ holds 12`.
      The number and the directory agree.
- [x] `README.md`'s *doing the work* row names `@@workflows`, and its lookup table has a row pointing at `@references/parts/workflows.md`.
      Ran: ``grep -nF '`@@specs` · `@@workflows`' README.md`` → exit 0, `README.md:117`:
      ``| doing the work | `@@workers` · `@@specs` · `@@workflows` · `@@personas` · `@@consult` · `@@drill` ·
      `@@language` |``. Ran: `grep -nE 'how a run improves it' README.md` → `README.md:108`:
      `| what a worker follows, and how a run improves it | @references/parts/workflows.md |`.
- [x] `references/system.md` has a `- **Following** —` bullet and `` `workflow [<slug>]` `` in its handles line.
      Ran: `grep -nE '\*\*Following\*\*|workflow \[<slug>\]' references/system.md` → exit 0.
      `43:- **Following** — a job that recurs is a `workflow`: an ordered route of` (the bullet sits before
      **Deciding**), and `55:` the handles line reads `… `memo <subject>`, `workflow [<slug>]`, `plan`, `view`, …`.
- [x] `python3 resources/index.py check` prints nothing and exits 0.
      Ran: `python3 resources/index.py check && echo "index: silent"` → printed only `index: silent`;
      the check itself emitted 0 bytes. Exit code 0 (same as the pre-edit baseline, which was also silent/exit 0).
- [x] `bash resources/install.sh <scratch-dir>` names `pearde-workflow`, and `--apply` leaves `<scratch-dir>/pearde-workflow/SKILL.md` as a link to `skills/pearde-workflow.md`.
      Ran: `bash resources/install.sh "$D"` (no `--apply`) → the listing names it:
      `  pearde-workflow missing  /var/folders/…/tmp.gb8ODuEV2o/pearde-workflow — 5 of 5 links`
      (`missing` = not yet built in that empty scratch dir; `5 of 5 links` is the per-folder link count).
      Ran: `D=$(mktemp -d); bash resources/install.sh --apply "$D" | grep -F pearde-workflow` → exit 0,
      `✓ built /var/folders/…/tmp.MUJGPACLb1/pearde-workflow`. Then `readlink "$D/pearde-workflow/SKILL.md"` →
      `/Users/feb/dev/infra/pearde/skills/pearde-workflow.md` — a link to the repo's skill file.
- [x] `bash resources/doctor.sh` reports the `skills` row `ok`, reading `12 well-formed`, with `pearde-workflow` among the names.
      Ran: `bash resources/doctor.sh </dev/null | grep -E '^ *skills'` →
      `  skills      ok      12 well-formed · pearde-doctor pearde-drill pearde-master pearde-memo
      pearde-persona-ask pearde-persona-create pearde-persona pearde-report pearde-scout pearde-view
      pearde-workflow pearde`. The row is `ok`, reads `12 well-formed` (baseline `11 well-formed`), and
      `pearde-workflow` is among the names.
- [x] `bash prds/workflows-on-the-board/workflow-skill/probe/verify.sh` still prints `0 fail`.
      Ran: `bash prds/workflows-on-the-board/workflow-skill/probe/verify.sh` → `55 checks · 55 pass · 0 fail`.
      First run after the hunks landed read `55 checks · 54 pass · 1 fail`, on
      `FAIL before the rows: the map names the unregistered file — no [skills/pearde-workflow.md is on disk with no row]`.
      Cause: the harness builds its fixture with `git ls-files --cached --others`, so once the rows are in the
      working tree the copy already carries them and the pre-registration state cannot be inherited. Repaired in
      place (the probe dir is in this spec's `footprint:`): the harness now strips the `@skills/pearde-workflow.md`
      row from the copy's `references/files.md`, measures, and puts it back. The rule it asserts did not move —
      the file alone, with no row, still reddens the map — only the way the precondition is reached.
- [x] Every harness under `prds/` that reads one of these pages prints a count no lower than its recorded baseline — `readme-in-three-rings` at `72 checks · 72 pass · 0 fail` is the one that reads `README.md`.
- [x] `prds/the-board-runs-itself/readme-in-three-rings/probe/verify.sh` prints `72 checks · 72 pass · 0 fail` — its four literals bumped, no rule changed. **This edits another PRD's committed harness; see the note above.**
      Ran: `bash prds/the-board-runs-itself/readme-in-three-rings/probe/verify.sh` → exit 0,
      `72 checks · 72 pass · 0 fail`. Baseline before the first edit was also `72 checks · 72 pass · 0 fail`.
      The four literals are bumped and no rule moved — `grep -nE 'eleven|twelve|ten rows'` over the two files reads
      `verify.sh:70: "E the one-question table has its eleven rows" … "11"`, `verify.sh:86: "F twelve skills" … "12"`,
      `quickstart.sh:47: "1 the skills dir holds twelve folders" … "12"`, and the link literal at `"60"`.
      Measured twice: with `skills/pearde-workflow.md` merely untracked the harness read `72 checks · 70 pass · 2 fail`
      (`got '11', want '12'` folders, `got '55', want '60'` links) because `quickstart.sh` builds its copy with
      `git ls-files -z`, which cannot see an untracked file; with the file in the index (`git add -N`, no content
      staged) it reads `72 checks · 72 pass · 0 fail`. The bumps were already correct — the harness *wants* 12 and 60.
- [x] `SKILL.md`'s skill list also names `pearde-report`. **This is a pre-existing omission this build found, not part of the contract** — the list named ten of the eleven files in `skills/`. Drop this box if the orchestrator would rather it were filed on its own.
      Ran: `grep -o 'pearde, pearde-drill[^—]*—' SKILL.md` → `pearde, pearde-drill, pearde-memo, pearde-view,
      pearde-report, pearde-master, pearde-doctor, pearde-persona, pearde-persona-ask, pearde-persona-create,
      pearde-scout, pearde-workflow —`. Census over the population rather than the two names expected: for every
      file in `skills/*.md`, `grep -qF "$(basename $f .md)" SKILL.md` — all twelve named, none missing.
      `pearde-report` was the pre-existing omission (the list held ten of eleven); it is added here with
      `pearde-workflow` by `apply.py` hunk 1.

## Verify and Proof

```sh
# the file itself
test -f skills/pearde-workflow.md && sed -n '1,4p' skills/pearde-workflow.md
grep -c 'pearde-workflow' SKILL.md references/parts/handles.md index.md references/files.md

# the rows, one page at a time
grep -nE 'the workflow library|check the library|pearde workflow (list|check)' references/parts/handles.md
grep -n '@skills/pearde-workflow.md' index.md references/files.md
grep -nE 'for the twelve skills|how a run improves it' README.md
grep -nF '`@@specs` · `@@workflows`' README.md   # the doing-the-work scope row
grep -nE '\*\*Following\*\*|workflow \[<slug>\]' references/system.md
test "$(ls skills/*.md | wc -l | tr -d ' ')" = 12 && echo "skills/ holds 12"

# the map check reads index.md and references/files.md; silent is the pass
python3 resources/index.py check && echo "index: silent"

# install.sh and doctor.sh both read skills/pearde-workflow.md by glob
D=$(mktemp -d); bash resources/install.sh --apply "$D" | grep -F pearde-workflow
readlink "$D/pearde-workflow/SKILL.md"; rm -rf "$D"
bash resources/doctor.sh </dev/null | grep -E '^ *skills'

# this spec's own harness, over every path in the footprint above
bash prds/workflows-on-the-board/workflow-skill/probe/verify.sh

# the one committed harness that reads README.md — baseline 72/72, and the
# two files of it this spec's footprint names
bash prds/the-board-runs-itself/readme-in-three-rings/probe/verify.sh </dev/null | tail -1
grep -nE 'eleven|twelve|ten rows' prds/the-board-runs-itself/readme-in-three-rings/probe/verify.sh \
  prds/the-board-runs-itself/readme-in-three-rings/probe/quickstart.sh
```

## Box 15, closed by the orchestrator — 2026-08-29

The implementer was killed by an API error at step 5, the harness re-run, the
seventh such kill of the night. It had already closed the other fourteen. I ran
the check this box names rather than resume an eighth time for one measurement:

```
find prds -name verify.sh | 22 harnesses, each run, last line read
red harnesses: 0 of 22
readme-in-three-rings/probe/verify.sh   72 checks · 72 pass · 0 fail
python3 resources/index.py check        silent, exit 0
bash resources/doctor.sh                exit 0, no broken row
```

Recorded here rather than ticked silently, because a box is the worker's live
view of its own run and this one is not: the evidence is mine. The condition
the box states is met and measured; who measured it is on the record.
