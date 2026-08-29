# running findings — analyst (designer), a-question-in-plain-words

Baseline, before any edit (2026-08-29):
- `find prds -name verify.sh` → 26
- `python3 resources/index.py check` → exit 0, no output
- `bash resources/doctor.sh` → exit 0; `guard off`, `harnesses off` (26, not run);
  `questions ok — no PRD carries a round`

F1. `doctor`'s `questions` row is green only because no round exists on the board.
    Per prds/memos/a-drill-round-fails-its-own-checker.md, the first real round
    turns it red. Any fixture I write under a scanned board would do the same.

F2. The memo's defect is ALREADY FIXED in HEAD and the memo is stale
    (`status: open`). resources/questions.py now has HEAD_RE and ITEM_RE as two
    regexes, and `questions_in` splits on `###` heads first, treating a
    top-level `1.` under a head as a prepared answer. I rebuilt the memo's exact
    fixture (one `### Q1` head, three numbered answers, first `(recommended)`)
    in a scratch board: `questions.py check` exits 0 with no output, where the
    memo records six lines and exit 1. Fixed by commit 3a84801
    ("transitions-are-commands"). The memo should be closed; memos are not in my
    footprint so I did not touch it.

F3. BUILT: resources/questions.py now carries the plain-words rule — `plain()`,
    `split_question()`, `slugs_of()`, wired into `check`. The acceptance fixture
    (probe/fixture.sh) reports exactly four lines, one per bad question, each
    naming the caught word; the PRD's own worked example passes clean.
    `questions.py check` on the real board still exits 0.

F4. `resources/board/transitions.py` ALREADY runs the check on
    `release <prd> question` — `gate_release` calls `qlib.check(...)` and
    refuses with the lines (transitions.py:146-157). So half the row the PRD
    assigns to that file is already standing, and my new rules inherit it for
    free. What is NOT there is `answer` running the check; `cmd_answer` never
    calls `qlib.check`. I did not edit the file — another session's analyst is
    live in it — so that goes to the implementer as spec05.

F5. CONTRACT DEFECT (author unreachable). The rule table says a question may
    never say "one of the nine state names", and the PRD's own worked example
    says "when they open the board" — `open` is one of the nine. Five of the
    nine (`open`, `question`, `blocked`, `done`, `failed`) are ordinary English
    a person uses about their own work; a bare-word check on them refuses
    correct questions, including the example the PRD ships as correct. I built
    the narrow reading — the four board-only spellings (`analyzing`, `specced`,
    `claimed`, `refine`, plus `deferred`) are caught bare; the other five are
    caught only in their board spelling, which is the backtick row 1 already
    refuses. The "## Done when" list only requires `specced` to be caught, so
    the narrow reading satisfies the contract as written.

F6. CONTRACT DEFECT (author unreachable). Row 5 of the table says the checker
    "now catches" "a fact a build can find". That is not mechanisable — no
    regex distinguishes a decision from a lookup. I built the half that is:
    the "should we also…" hedge family. The rest stays a rule for the analyst
    in drill.md, enforced by reading, not by the checker. Claiming the checker
    catches it would be a check that cannot fail.

F7. Harness box, re-taken after the build:
      index.py check   exit 0 (was 0)
      doctor.sh        exit 0 (was 0) — every named row unchanged; `questions`
                       still ok, `briefs` still ok, `index` still ok
      find prds -name verify.sh   28 (was 26)
    Two of those three new harnesses are NOT mine: `prds/a-parked-prd-comes-back/
    probe/verify.sh` is the other session's, and one more appeared during the
    round. Only `prds/the-board-asks-for-itself/a-question-in-plain-words/probe/
    verify.sh` is mine. The count is a shared number and cannot be read as a
    box for one worker while two sessions write the same tree.

F8. `resources/board/transitions.py` was dirty in the working tree throughout,
    with only the other session's `a-parked-prd-comes-back` work in it
    (`gate_release` early-return for the parked → open edge, `parked()`,
    `way_back()`). I did not edit it. Their change lands ABOVE the `question`
    branch in `gate_release` and does not touch it, so the two builds do not
    collide.

F9. "## Done when" item 4 is vacuously satisfied: no PRD on this board carries
    a `## Questions` round at all (doctor's `questions` row says so), so there
    is nothing to rewrite and nothing to list.
