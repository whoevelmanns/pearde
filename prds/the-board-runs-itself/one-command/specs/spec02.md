---
complexity: 16
workflow: implement-a-spec
footprint:
  - resources/pearde.py
  - prds/the-board-runs-itself/one-command/probe
  - index.md
  - references/files.md
---

# spec02 — `resources/pearde.py` lands: the dispatcher, discovery, `help`

`python3 resources/pearde.py <cmd>` is the whole surface. The probe built the
file; this spec moves it to the path the PRD names, drops the one block that
was probe-only, and puts the file on the map. Needs spec01 first — the probe's
`memo add` block goes, and `pearde memo add` then reaches `memos.py`.

## What already stands

`@prds/the-board-runs-itself/one-command/probe/pearde.py` (436 lines) is the
dispatcher, and `@prds/the-board-runs-itself/one-command/probe/verify.sh`
proves it against a fixture root built at run time — `70 passed, 0 failed`
on 2026-08-28. What it does, and what the harness asserts:

| piece | behaviour |
|---|---|
| root | walks up from its own file to the nearest dir holding `resources/board/plan.py` — the same file works from `resources/` and from `probe/` |
| `FORWARD` | the contract table: name → (script, prefix verb, verbs). `scan plan reconcile gantt calibrate status members` → `board/plan.py`; `view` → `board/serve.py`; `memo` → `memos.py`; `workflow` → `workflows.py`; `questions` → `questions.py check`; `index` → `index.py check`; `doctor` → `doctor.sh`; `install` → `install.sh` |
| forwarding | `subprocess.call([python3\|bash, script, *args])`, exit code returned as is. The board is never resolved here — every script resolves it itself |
| `view` | `serve.py ensure [board]`, output echoed, the `http://…` it printed opened with `webbrowser` unless `--no-open`; `status stop wait forget run` pass through |
| default | no argument → `scan` |
| `RESERVED` | 16 names → the child that delivers each; prints `not yet — <child>` on stderr, exit 1. Discovery wins: a module claiming a reserved name routes there |
| discovery | every `resources/board/*.py` whose source matches `^COMMANDS\s*=` is imported; `COMMANDS = {name: callable}`; the callable takes the argument list and returns the exit code (`None` = 0). A name two modules claim, or a name in `FORWARD`, is a problem; a module that fails to import is a problem, never fatal |
| `help` | one line per command, ≤ 80 characters, from each script's docstring (`"""…"""` for `.py`, the leading `#` block for `.sh`), parsed by `split_usage` — verb, bracketed args, description — and from a discovered callable's docstring first line. Problems print on stderr and `help` exits 1 |
| `<cmd> --help` | that command's line(s), exit 0, the script never runs |
| unknown | exit 2, the near-miss named |

Live on this repo the same day: `collect.py` and `transitions.py` from sibling
PRDs were discovered and routed with no edit here.

## What is left

1. `git mv`-style move: `probe/pearde.py` → `resources/pearde.py`. One file,
   not two — delete the probe copy. In `probe/verify.sh` change the one line
   `cp "$HERE/pearde.py" "$R/resources/pearde.py"` to
   `cp "$REPO/resources/pearde.py" "$R/resources/pearde.py"`, and the two
   `"$HERE/pearde.py"` calls under `# ── the real tree` to
   `"$REPO/resources/pearde.py"`.
2. Delete the `memo add — PROBE ONLY` block (`slug_of`, `memo_add`), the
   `if name == "memo" and rest[:1] == ["add"]` branch in `main`, and the
   `# PROBE ONLY` special case in `help_lines` — spec01 put `add` and its
   usage line in `memos.py`, so `memo` forwards every verb and `help` reads
   the line from there. `grep -c "PROBE ONLY"` on the landed file is 0.
3. The map. `references/files.md`, table `## resources/ — run`, one row:
   `| @resources/pearde.py | the one command — a dispatcher over every script; discovers COMMANDS in resources/board/*.py; help from docstrings |`.
   `index.md`: `@@handles` and `@@install` each gain `@resources/pearde.py`.
   The orchestrator writes these on collect where the implementer finds them
   already written; the box below is the check either way.
4. Nothing else moves. No logic enters the file: a behaviour a check wants
   that is not in the table above belongs in the script that owns the
   command.

## Acceptance

- [x] `python3 resources/pearde.py help` exits 0, every `  pearde …` line appears once, and no line is longer than 80 characters
- [x] `bash prds/the-board-runs-itself/one-command/probe/verify.sh` prints `70 passed, 0 failed`, with the harness copying `resources/pearde.py`
- [x] `prds/the-board-runs-itself/one-command/probe/pearde.py` does not exist and `grep -c "PROBE ONLY" resources/pearde.py` prints 0
- [x] `python3 resources/pearde.py` and `python3 resources/pearde.py scan` print byte-identical output on this board
- [x] `python3 resources/pearde.py collect` on this board either runs `collect.py` or prints `not yet — collect-is-a-command` — never a traceback
- [x] `python3 resources/index.py check` prints no line naming `resources/pearde.py`, and `python3 resources/index.py scope handles` lists it

## Verify and Proof

```sh
python3 resources/pearde.py help | awk '{ if (length($0) > 80) bad++ } /^  pearde/ { n++; seen[$0]++ } END { print n " lines, " (bad+0) " over 80, " (n - length(seen)) " duplicates" }'
bash prds/the-board-runs-itself/one-command/probe/verify.sh | tail -1
grep -c 'cp "$REPO/resources/pearde.py"' prds/the-board-runs-itself/one-command/probe/verify.sh
ls prds/the-board-runs-itself/one-command/probe/; grep -c "PROBE ONLY" resources/pearde.py
python3 resources/pearde.py > /tmp/pearde-a.txt; python3 resources/pearde.py scan > /tmp/pearde-b.txt; cmp /tmp/pearde-a.txt /tmp/pearde-b.txt && echo identical
python3 resources/pearde.py collect; echo "rc=$?"
python3 resources/index.py check | grep -c "resources/pearde.py"; python3 resources/index.py scope handles | grep pearde.py
```
