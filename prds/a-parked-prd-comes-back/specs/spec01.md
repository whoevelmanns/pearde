---
complexity: 6
footprint:
  - resources/board/transitions.py
  - prds/a-parked-prd-comes-back/probe/verify.sh
---

# spec01 — `release <prd> open` un-parks, and every other parked transition names that way out

`transitions.py` gets one edge out of a parked state — any `state:` outside the nine, `deferred` included — and it goes to `open` only: `claim:` cleared, the row written, the line reading `<parked> → open` with no `forced`. Every other transition on a parked PRD (`release` to another target, `claim`, `set` without `--force`, `retry`, `unblock`, `defer`) refuses with one text: `<prd> is \`<state>\` (parked) — \`release <prd> open\` brings it back`. A parked PRD that `plan.dispatchable` calls a container refuses with the predicate's own words, `container: every child done — pearde collect closes it`.

## What the probe already left in the tree

Built in place, in `resources/board/transitions.py` — an edit to an existing footprint file has no meaning outside it. Nine hunks, all disjoint from the two foreign `progress_line` hunks (`asked` → `done`, ~421 and ~434) that another session owns:

- `parked(frm)` and `way_back(rel, frm)` beside `edge_of`; `edge_of` maps a parked source to `release` when the target is `open`, after the `WAITING` mapping so a state that names a person keeps `answer`'s gate.
- `gate_release`: on `to == "open"` from a parked state, `planlib.dispatchable` is asked and a `container:` answer is raised as it stands; no other gate runs.
- `cmd_release`: a parked source allows `open` only, refusing the rest with `way_back`; the live-state wording `analyzing → refine|question|open, claimed → blocked|failed` is untouched.
- `transition()`: `cmd is None` on a parked source raises `way_back` before the `no command moves` line, so `set` (unforced) and `defer` on a parked PRD name the way out.
- `cmd_claim`, `cmd_retry`, `cmd_unblock`: `way_back` before their own refusal.
- The `EDGES` comment names the parked edge and why it is in `edge_of`, not the table.

`prds/a-parked-prd-comes-back/probe/verify.sh` is the harness: 44 checks on a `mktemp` copy of the example board, sections A–H. Left to do: nothing in code; the implementer re-runs, ticks, and reconciles the harness count if a sibling moves the refusal texts.

## Decisions the build made

- A parked state that names a person (`hitl`, `waiting`, `user`) is `question`'s claim per @references/parts/states.md, so `release <prd> open` on it runs `gate_answered` and refuses `answer: unanswered — Q<n>` until the round is answered. Section G asserts it. The PRD's "any word outside the nine" is honoured — the edge exists — but the gate is `answer`'s.
- `dispatchable` answers `unclaimed:` before `container:`, so a container parked by `set --force` while it still carried a `claim:` is released to `open`, where `claim` refuses it with the container words. `defer` cannot produce that PRD (its gate needs the claim released); it is not built around.

## Acceptance

- [x] `bash prds/a-parked-prd-comes-back/probe/verify.sh` prints `44 checks · 44 pass · 0 fail` and exits 0.
- [x] On a copy of the example board, `set big/second later --force` then `release big/second open` exits 0, the line reads `big/second: later → open`, `claim:` is absent, and `.transitions.jsonl` grew by one row (section A).
- [x] `release big/second specced` on the parked copy exits 1 and stderr carries `` `release big/second open` brings it back `` (section B).
- [x] `set big/second done --force`, `set big later --force`, `release big open` exits 1 with `container: every child done — pearde collect closes it` and `big` stays `later` (section F).
- [x] `release big/second open` from `specced` (forced there) still refuses with `analyzing → refine|question|open, claimed → blocked|failed` — no `(parked)` on a live state (section D).
- [x] `prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh` prints a count no lower than its baseline beside this PRD (74 checks, 71 pass at the probe's last run: the one `the line opens with the transition` red is the foreign `progress_line` rename, the two `questions.py check` reds are `resources/questions.py`'s live edit — neither is this spec's), and no line names `parked` or `release`.
- [x] `prds/the-tool-keeps-its-word/one-predicate-for-dispatchable/probe/verify.sh` prints `53 checks · 53 pass · 0 fail` — the container words come from `plan.dispatchable`, not a second predicate.

## Verify and Proof

```sh
bash prds/a-parked-prd-comes-back/probe/verify.sh </dev/null
python3 -c "import ast; ast.parse(open('resources/board/transitions.py').read())"
env -u PEARDE_AS PEARDE_PORT=1 bash prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh </dev/null | tail -1
env -u PEARDE_AS PEARDE_PORT=1 bash prds/the-tool-keeps-its-word/one-predicate-for-dispatchable/probe/verify.sh </dev/null | tail -1
git diff -U0 resources/board/transitions.py | grep -c '^@@'
```
