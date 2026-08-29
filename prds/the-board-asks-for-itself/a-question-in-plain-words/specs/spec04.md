---
complexity: 5
footprint:
  - resources/board/transitions.py
---

# spec04 — `answer` runs the check too

**This is the one unit the analysis deliberately did not build.**
`resources/board/transitions.py` was held by another session's analyst for the
whole of this round, and two writers in one file is the failure this board has
been avoiding. Everything the change needs is written down here.

**What already stands, and is not this spec's work**: `gate_release` already
runs the check on the `question` edge. At `resources/board/transitions.py:146`
it calls `qlib.check(prd["board_path"])`, keeps the lines whose prefix is this
PRD's own name, and raises `Refused` with them joined — so
`release <prd> question` refuses a round that breaks the plain-words rule and
leaves the state untouched, with no edit at all. That half of the PRD's row for
this file is measured passing in `probe/verify.sh`. The filter was checked on a
nested PRD as well as a top-level one, and holds for both.

**What is left — the exact change.**

- The function is `cmd_answer`, at `resources/board/transitions.py:531`. It
  resolves the PRD, refuses an unknown or already-answered id, then calls
  `editlib.append_section(path, "Answers", …)`.
- Add, after the `qid in answered_of(prd)` refusal and **before**
  `append_section` writes anything, the same check `gate_release` runs: call
  `qlib.check(prd["board_path"])`, keep the lines beginning `prd["local"] + ":"`,
  and on any line raise
  `Refused("answer: questions.py check refuses the round — " + "; ".join(bad))`.
- Lift the shared three lines out of `gate_release` into one helper —
  `round_problems(prd)` — and call it from both, so the two paths cannot drift.
- **Why**: the PRD's row for this file names `release <prd> question` *and*
  `answer`. Answering a round that never should have been written records a
  decision against a question the user was shown in board words. Refusing at
  `answer` is the second gate on the same claim, and it is the last moment the
  round can still be rewritten rather than answered.
- **The one thing to watch**: a round already on disk that fails the new rule
  becomes unanswerable, not merely unwritable. Refuse with the lines, so the
  orchestrator can rewrite the round and answer it; do not add a bypass flag.

## Acceptance

- [x] `pearde answer <prd> Q1 "<text>"` on a PRD whose round breaks the rule
      exits non-zero, names the caught word, and writes no `## Answers` line.
- [x] The same command on a clean round still writes the answer and still moves
      the PRD `open` on the last one.
- [x] `gate_release` and `cmd_answer` call one shared helper, not two copies.
- [x] `bash probe/verify.sh` still exits 0.
- [x] `python3 -m py_compile resources/board/transitions.py` passes.

## Verify and Proof

```sh
python3 -m py_compile resources/board/transitions.py
bash prds/the-board-asks-for-itself/a-question-in-plain-words/probe/verify.sh
python3 resources/questions.py check ; echo "board exit=$?"
```
