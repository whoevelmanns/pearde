---
complexity: 7
footprint:
  - references/drill.md
  - references/parts/workers.md
  - references/templates/prd.md
---

# spec02 — the rule where the four readers of it look

The rule is written once, in `references/drill.md`, and the three files that
hand it to somebody cite it rather than restate it.

**What already stands** (built during the analysis, uncommitted):

- `references/drill.md` — *The shape of a question* is now the rule: two
  sentences then the question mark, three answers each one plain sentence of
  what they get, the open door as the last line, the *what a question may never
  say* table, and the worked example with its technical anchor.
- `references/parts/workers.md` — the analyst brief's QUESTION verdict carries
  the rule in one sentence, the worked example, and the line *write for the
  person who asked for this, not for the orchestrator*.
- `references/drill.md` — the ask mapping stated once: header is
  the `### Qn:` title, question is the fork, the three options are the answers
  with their labels, the mechanism's free-text choice is *write your own*, and
  at a terminal with no mechanism the round is printed in the same words with
  *or write your own* as the fourth line.
- `references/templates/prd.md` — the `## Questions` comment says the rule in
  one line and points at drill.md.

**What is left**: run the boxes below against the landed tree. The numbering is
a non-goal and must not move: `### Q1:` heads and `1.`/`2.`/`3.` answers are
what the three readers parse.

## Acceptance

- [x] `python3 resources/index.py check` exits 0 — every anchor added resolves.
- [x] `python3 resources/board/brief.py brief --check` exits 0 — the five
      blocks still parse and every placeholder is named.
- [x] `pearde brief <any open prd> --role analyst` prints the QUESTION verdict
      carrying the worked example and the *write for the person who asked*
      line.
- [x] `references/drill.md` holds the never-table and the worked example, and
      still shows the abstract round format the view parses.
- [x] The round format in drill.md still spells the heads `### Q1:` and the
      answers `1.` `2.` `3.`.

## Verify and Proof

```sh
python3 resources/index.py check ; echo "index exit=$?"
python3 resources/board/brief.py brief --check ; echo "brief exit=$?"
grep -c "or write your own" references/drill.md
grep -c "person who asked for this" references/parts/workers.md
grep -n "### Q1:" references/drill.md references/parts/workers.md
grep -n "write your own" references/drill.md
grep -n "plain words" references/templates/prd.md
```

## Moved 2026-08-29 — the mapping lives in drill.md, not loop.md

This spec put the ask mapping in `references/parts/loop.md` step 2. It landed
there and took that file from 120 lines to 130, which turned
`the-board-runs-itself/the-loop-is-commands`' committed harness red on its own
contract: **`loop.md` is the seven commands and nothing a command does not
enforce, capped at 120 lines.**

A mapping from a question round onto a rendering mechanism is neither a command
nor something a command enforces. It is exactly the kind of sentence that PRD
deleted to reach 120, so putting it back was undoing another PRD's contract to
satisfy this one.

Moved whole to `references/drill.md`, which owns the round format and is in this
spec's footprint either way. `loop.md` is restored to HEAD byte-for-byte and
`the-loop-is-commands` reads `60 checks · 60 pass · 0 fail` again. The box below
now greps `drill.md`; nothing about the rule changed, only where it is written.

Found by the other session running its own harness against my uncommitted work —
which is the whole argument for a shared tree being measured by more than the
worker that changed it.
