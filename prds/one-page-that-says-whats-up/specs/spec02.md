---
complexity: 14
footprint:
  - resources/board/render.py
  - resources/board/view.js
  - resources/board/view.css
---

# spec02 — section 1 renders the report, and shows how old it is

A prose section at the top of the page, above everything, filled from
`prds/report.md` over the `/report` endpoint that already exists. It is a
renderer, not an author. Beside the prose it shows the age of what it is
showing.

## What the probe measured — the answer to the PRD's one question

The PRD asked the build to try `report.md` in the slot before generating
sentences from the scan. It was tried, against the live board, and it reads
well: the file already carries a title, a dateline, a lede, `## In work` and
`## Planned` — the exact four things this section needs, already in a person's
register. Rendered lede + first `In work` paragraph + first `Planned`
paragraph, trimmed to two or three sentences each, the section came to 852
characters and left the plan visible at y=509 on a 900px fold.

**So the answer is: the section is a renderer.** Generating sentences from the
scan was not needed and would be worse — see the truth test below.

**But `report.md` is not kept fresh by anything.** When this PRD was picked up
the file was dated `2026-08-28, end of day` and was sixteen commits behind; it
became current only because a person rewrote it. That is the same defect as
`.round.md` in a politer voice, and it is why this spec renders **the age**
rather than only the words. The report's own dateline is prose the file's
author wrote and can forget to change; the honest age is the file's git mtime,
which the service can read and the author cannot lie about.

Nothing is edited yet. The probe filled this section in the browser only.

## The truth test this section must pass

The board today shows `workflows-on-the-board` as live work worth `est: 20.0`
while all six of its children are `done` — confirmed in the `/data` payload.
The planner's existing `containers` fold does not catch it, because that fold
only removes a PRD whose scheduled span is zero. A section that generated
"what is next" from the scan would therefore state something false about that
PRD. Rendering `report.md` sidesteps this: a person writing prose does not
list a finished parent as upcoming work. This is a reason to render rather
than generate, and it is not a licence to fix the state machine — that is
recorded in `prds/memos/a-container-cannot-reach-done.md` and is not in this
PRD's footprint.

## Acceptance

- [x] The page's first section, above the plan, shows the report's title, its lede, what is in work, and what is next
- [x] The section shows the age of `prds/report.md`, in words, from the file's modification time and not from the dateline inside it
- [x] When that age is over 24 hours the age line is visibly marked as stale, and the marking is a class a check can read, not only a colour
- [x] With `prds/report.md` absent, the section renders a stated empty case naming the command that writes it, and the page below it is unaffected
- [x] Each rendered paragraph is cut on a sentence boundary, never mid-clause, and no paragraph exceeds three sentences
- [x] `grep -c 'function md(' resources/board/view.js` is `1` — the existing prose renderer is reused, not duplicated
- [x] No change is made to `resources/board/serve.py`

## Why there is no word-level assertion here

The PRD asks that section 1 contain "no `state:` word". **That assertion cannot
be written against English prose and this spec does not write it.** Run against
the live report, a state-word blocklist flags `question` in the sentence "a real
question rather than a detail" — ordinary English — and `specced` in a sentence
correctly describing a PRD about speccing. The words are indistinguishable from
their tool meanings by grep.

What *is* mechanical is the source: section 1 renders `prds/report.md` and
nothing else. That is greppable, and it is the acceptance box above. The
register rule stays where it is enforceable, on the report's author, in
`@@report`.

## Verify and Proof

```sh
grep -n 'report?board=' resources/board/view.js
grep -c 'function md(' resources/board/view.js
grep -n 'whatsup\|stale' resources/board/render.py resources/board/view.css
python3 -c "import re,sys; s=open('resources/board/view.js').read(); sys.exit(0 if 'serve.py' not in s else 1)"
```
