# Personas

Who works the **session**, and how one is chosen. Two other questions are
answered elsewhere and do not need this file: a dispatched worker's persona is
a table in @references/parts/workers.md, and calling one mid-round is
@references/parts/consult.md.

A persona is what gets noticed first, what gets pushed back on, what counts as
done. The role is what the session does; the persona is who does it. One is
active at a time. @references/personas/INDEX.md is the roster.

**A persona is stored on no board file.** No key in `.pearde/settings.md`, no
file beside the board. It is session state, and the session's environment is
where it lives: `PEARDE_AS`, exported as `engineer` by the line
`install --apply` prints beside the alias, read by every command that moves a
PRD. It starts as `engineer`, holds until switched, ends with the shell.
`persona <id>` is `export PEARDE_AS=<id>`; where each command runs in a fresh
shell — an agent's tool call — it is `--as <id>` on the line instead. The
round's line carries `· as <id>` from the same variable per
@references/parts/progress.md, and that line is the only record on the board
— which is also where the status line reads it from.

A command with neither `--as` nor `PEARDE_AS` refuses, naming the install
line: a guessed `engineer` after a `persona skeptic` would rewrite the only
record the switch has. `add` alone runs — a new PRD has no earlier line to
rewrite — and its line says `· as engineer (default)`, so the record shows
nobody chose it.

That is deliberate — a persisted persona outlives the round that justified it,
follows a board into work of a different shape, and lets two sessions on one
board overwrite each other's answer. One line per round re-states it, cheaper
than a file that can disagree with the session holding it.

## Three scopes

| scope       | who                                       | chosen                                 | asked | lives                          |
|-------------|-------------------------------------------|----------------------------------------|-------|--------------------------------|
| **session** | the orchestrator working this board       | once, and again on a real phase change | yes   | this session's context, and its round lines |
| **worker**  | one dispatched analyst or implementer     | per dispatch, from its job — @references/parts/workers.md | never | that worker's brief |
| **consult** | one asked a question — @references/parts/consult.md | for the question | never | that one answer |

A worker's persona is a property of the job it was handed. A `skeptic`
verifying one PRD does not make the session skeptical, and neither does a
consult: the user names one, gets its answer, and the session goes on wearing
what it was wearing.

## The signals

Read top to bottom. **The first row that matches is the candidate.** A row
matches on what the work is, never on how the user phrased it.

| # | the signal                                                                                                  | candidate  |
|---|---------------------------------------------------------------------------------------------------------------|------------|
| 1 | the user names one — `persona <id>`, "as the skeptic", "be more adversarial"                                  | that one   |
| 2 | `drill`, or the user asks why, asks to be walked through, or is deciding rather than directing                | `mentor`   |
| 3 | verifying before `done`, `collect`'s gate, auditing a worker report, checking a plan, a `failed` post-mortem   | `skeptic`  |
| 4 | the PRD's contract is user flow, product shape, or naming a user-facing thing; the view's UX calls             | `designer` |
| 5 | anything else — the loop, specs, implementation, memos, commits, `plan`, `master`                              | `engineer` |

- **Row 1 is the user speaking.** It outranks every other row, and it is never
  put back to them as a question.
- **Rows 2-4 are the work speaking.** They propose. The user disposes.
- **Two rows match** — a `drill` about a user flow is both 2 and 4. The lower
  number wins: it describes the *round*, the higher one only the *subject*.
  Genuinely tied and it matters — offer both in the ask.
- Row 3 is about **checking finished work**, not about work going badly. A
  failing test inside an implementer's own loop is engineering, not review.

## From candidate to active

| the case                                                  | do                                                                      |
|-----------------------------------------------------------|-------------------------------------------------------------------------|
| candidate = active                                         | nothing. Do not mention it                                              |
| the user stated it (row 1)                                 | switch, and say so in one line. No question                             |
| candidate ≠ active, and the round is dispatching a worker  | that is the worker's brief, not a switch — @references/parts/workers.md |
| candidate ≠ active, and it governs the round               | ask — one question, below — and wear the answer                         |
| nothing has been stated yet                                | run as `engineer`, and ask on the first round that has a job to match    |

A switch takes effect immediately and holds until the next one or the end of
the session. No board file is written, so nothing has to be unwritten: the way
back to `engineer` is `export PEARDE_AS=engineer`, the install line again.

**Never switch the session silently.** Print the switch in the same `▸ … · as
<id>` form the round line uses, even when no state moved — that line is the
only record the switch has, and the status line reads it from there.

## The ask

One question, in the @references/drill.md round format, folded into the round
that raised it — never a round of its own, never twice in one round.

```
Question *Q1*: **Who should work this?**
<one sentence: the job, and the signal row it matched>

1. `<candidate>` — <name> · <what it optimizes for>
2. `<alternative>` — <name> · <why you might want it instead>
3. `<alternative>` — <name> · <why you might want it instead>

Recommendation `<candidate>` — <the reason, in one line>
```

- The recommendation is the candidate. Offer at most three — the roster is one
  hop away for the rest.
- Wear the answer from the next line onward and carry it on the round's line.
- Answered once, it holds for the session. The next PRD in the same loop is not
  a phase change, and the question is not asked twice for the same reason.
- **None of the three fits** — that is `persona create <topic>`, per
  @references/personas/INDEX.md. Offer it only when the job really is a field
  the roster does not cover; a job that is merely specific is still one of the
  four wearing it.

`persona` with no argument reports who is working and which signal row put them
there. It changes nothing.

## What never switches it

Thrash costs more than a slightly wrong persona. None of these is a signal:

- **Tone.** The user being terse, annoyed, or in a hurry.
- **Formatting.** A request for shorter answers or no preamble — an output
  style, not a persona.
- **One question.** A single "why did you do that" inside an engineering round
  is answered, not switched for.
- **A red build.** Fixing what you broke is the work, not a review of it.
- **The board's language.** `language:` is a board setting; a persona is not a
  setting at all.
- **A worker's dispatch.** The brief carries it. The session does not move.
- **A consult.** Asking the skeptic one question is asking it, not becoming it.

## What a persona does not change

A persona changes emphasis. It never changes the contract:

- The seven steps, the nine states, and who may write them —
  @references/parts/loop.md, @references/parts/states.md.
- The gates: `specced` needs spec files on disk, `done` needs verify output
  actually run. The skeptic gets no stricter gate and the mentor no softer one.
- `language:`, the memo rules, the commit rules, the frontmatter contract.
- One orchestrator per board.

`persona create <topic>` builds a new one from research, never invention — the
steps are @references/personas/INDEX.md.
