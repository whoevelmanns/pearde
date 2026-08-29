---
complexity: 14
footprint:
  - resources/questions.py
  - prds/the-board-asks-for-itself/a-question-in-plain-words/probe/
---

# spec01 — the plain-words rule, as a mechanism

`resources/questions.py check` reports every row of the PRD's table, per
question, naming the word it caught. The round's technical anchor is an HTML
comment and is never checked and never reported. Scope is the fork, the answer
labels and the answer text; the `### Qn:` head is the round's index and is left
alone.

**What already stands** (built during the analysis, uncommitted in the tree):
`plain()`, `split_question()`, `words()`, `bare()` and `slugs_of()` in
`resources/questions.py`, wired into `check()` one line after the
recommended-answer test. The harness at `probe/verify.sh` and the fixture
generator at `probe/fixture.sh` pass whole. Nothing in this spec is unstarted —
it is here so the boxes are run again against the tree the implementer lands.

**One decision is pinned and must not be widened.** The PRD's table says a
question may never say "one of the nine state names", and the PRD's own worked
example says *when they open the board*. Five of the nine — `open`, `question`,
`blocked`, `done`, `failed` — are ordinary English about one's own work, and
catching them bare refuses the example the PRD ships as correct. The build
therefore catches bare only the board-only spellings (`analyzing`, `specced`,
`claimed`, `refine`, `deferred`); the other five are caught in their board
spelling, which is the backtick row 1 already refuses. Do not extend
`STATE_WORDS` to the full nine without an answer from the user — see the report.

Likewise row 5: "a fact a build can find" is not mechanisable. The build
catches the `should we also…` hedge family and nothing more; the rest stays a
rule for the analyst, held by reading. Do not add a check that cannot fail.

## Acceptance

- [x] `python3 resources/questions.py check` on this repo exits 0.
- [x] The fixture board of "## Done when" — one question naming a PRD name of
      that board, one saying `specced`, one naming a file, one with a 71-word
      fork, one clean — reports exactly four lines.
- [x] Each of the four lines names what it caught: the PRD name, `specced`, the
      file, and the word count against the limit.
- [x] The clean question is not reported, and the technical anchor under its
      third answer is never named in any line.
- [x] `STATE_WORDS` still holds five board-only spellings, not the nine.

## Verify and Proof

```sh
python3 -m py_compile resources/questions.py
python3 resources/questions.py check ; echo "board exit=$?"
bash prds/the-board-asks-for-itself/a-question-in-plain-words/probe/verify.sh
```
