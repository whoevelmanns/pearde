---
state: done
origin: requested
priority: 75
complexity: 38
blast-radius: mid
repo: pearde
footprint:
  - resources/board/render.py
  - resources/board/view.js
  - resources/board/view.css
  - resources/board/viewtest.js
  - references/parts/view.md
actual: 2.1h
---

# one-page-that-says-whats-up — the board reads top to bottom, and says what it is doing in words

When this is done, a person opens `/board/<name>`, reads a short paragraph
that tells them what the board is doing and what is next, and scrolls — the
board, then the analytics, then the rest. No tab bar to learn, and no session
scratch file on the page.

## What is wrong with the page today

- **`<pearde-round>` renders `prds/.round.md`**, which @references/parts/round.md
  calls "the session's own memory — machine-local and git-ignored… what one
  session is holding, not what the board is." It is a crash-recovery file for
  a machine, in `.gitignore` at line 13, written in the board's own vocabulary
  — `specced`, footprints, commit shas, struck boxes. @@report forbids every
  one of those words in the one document written for a person, and the page
  puts them in the first screenful.
- **Seven tab-panes** mean the answer to "what is happening" is behind a
  click, and which click is a thing you have to know.

## The three sections, in order

| # | section | is |
|---|---|---|
| 1 | **what's up** | prose, at the top, above everything. Two or three sentences: what the board is working on now, what is next, and what waits on the reader. Written in the register of @@report — no PRD directory names, no state words, no weights. Not `prds/.round.md` |
| 2 | **the board** | the timeline and the bands, as they are today |
| 3 | **the analytics** | below the board, not beside it |

Everything the tabs hold today becomes a section in this order, reachable by
scrolling. The tab bar, if it survives at all, becomes anchors that jump — it
never hides a section.

## The one question the build has to answer

**Where the prose comes from.** Three sources exist and only one is right:

- `prds/.round.md` — rejected above; it is the session's scratch.
- `prds/report.md` — already written for a person, already rewritten whole at
  every round that moves something, already in the board's own register. It is
  the obvious source and the build should try it first.
- Generated from the scan — counts turned into sentences. Cheap, always
  current, and says nothing a person could not read off the bands themselves.

The build picks by trying, not by arguing. If `report.md`'s opening reads well
in that slot, that is the answer and the section is a renderer, not an author.

## Rules

- **No state word, no PRD directory name, no weight** in section 1. The rule
  is @@report's and it is what makes the section worth having.
- **Nothing that is git-ignored is rendered for a person.** That is the
  general form of the `<pearde-round>` defect, and it should hold after this
  PRD as a sentence in @references/parts/view.md.
- The page keeps working with **JavaScript's own tools only** — no build step,
  no dependency, per @README.md.

## Verify

- The page renders top to bottom with the three sections in order, at a narrow
  width and a wide one.
- `grep -c 'pearde-round' resources/board/render.py resources/board/view.js`
  is 0, or the element renders something that is not `.round.md`.
- Section 1 contains no `state:` word from @references/parts/states.md, no
  `prds/` path, and no `complexity` number — asserted, not eyeballed.
- Every section the tabs used to hold is reachable by scrolling, and each is
  named in `references/parts/view.md`.
