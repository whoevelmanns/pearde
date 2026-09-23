# The report

The one document on the board written for a person. One file,
`prds/report.md`, rewritten whole every time. Nothing parses it.

Reader: whoever the work is for, reading fast, who has never seen the board.
They want three things — what is planned, what is being worked on now, and
what is stuck or waiting on them.

## One state, not a log

- **One file.** `prds/report.md`, next to `settings.md`. A board is needed to
  write one; with none in scope, write the text and say where it goes.
- **Rewritten whole.** Never appended, never a dated entry, never a section
  per round. The file says what is true today and nothing about yesterday —
  git holds every earlier state.
- **Written on demand, and at the end of a round that moved anything** —
  @references/parts/loop.md step 7.

## Human, not agent

The board's own vocabulary is the failure mode. None of it survives:

| never write            | write instead                                  |
|------------------------|-------------------------------------------------|
| a PRD directory name   | the thing in plain words — "the login screen"    |
| `specced`, `claimed`, `refine` | what that means for the reader            |
| `complexity`, weights, `priority` | "big", "small", "next"               |
| `origin: derived`      | "we found we also need"                          |
| a percentage of weight | one plain fraction, in the lead, or nothing      |

- **Prose, lists, or one table per section.** Whichever is shorter.
- **Present tense, current state.** Not the story of arriving at it.
- **Every entry says what it means for the reader** — what they get, or what
  it costs them that it is not there yet.
- **Fits one screen.** A section past six entries is a table, or is summarised
  with the tail counted: "and four smaller cleanups".

## Shape

@references/templates/report.md is the file. Four parts:

1. **A lead** — two or three sentences: where the work stands, what landed
   since it last mattered, one fraction if it helps.
2. **Planned** — not started. Ordered as the board would run it, so the first
   entry is what happens next.
3. **In work** — someone or something is on it right now.
4. **Undecided or failing** — needs the reader's decision, waits on a named
   event, or was tried and did not work. Each entry names the one thing that
   would move it.

## What goes where

Every PRD on the board lands in exactly one section. A PRD in none is a bug in
the report.

| state       | section                | written as                            |
|-------------|------------------------|----------------------------------------|
| `done`      | the lead               | what now exists, in one clause         |
| `analyzing` | In work                | "being worked out"                     |
| `claimed`   | In work                | "being built"                          |
| `specced`   | Planned, first         | "ready to start"                       |
| `open`      | Planned                | plain, no qualifier                    |
| `refine`    | Planned                | "too big as one piece — being split"   |
| `question`  | Undecided or failing   | the decision itself, as a question the reader can answer |
| `blocked`   | Undecided or failing   | "waiting on <the event>" — name it     |
| `failed`    | Undecided or failing   | what was tried, and what it needs      |
| parked      | one line, at the end   | "set aside" — @references/parts/states.md |

- **Questions are the point of the section.** A reader who answers three of
  them unblocks the board, so each is a real fork with the choices spelled
  out, not "needs input on auth".
- `blocked` and `failed` read differently to a person: one is waiting, one
  went wrong. Never merge the wording.
- On a master board, group by project — the member's name as the reader knows
  it, not its path. @references/parts/master.md.
