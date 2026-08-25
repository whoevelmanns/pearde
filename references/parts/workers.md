# Worker briefs

The exact text to hand an analyst and an implementer.

Give each worker exactly its brief with the placeholders filled in. `@` and
`@@` resolve in @index.md.

Rules for every worker:

- Never edit frontmatter, never touch other PRDs, never write outside the PRD
  folder. Implementers also write the target repo.
- Open the brief with one line naming the worker's persona — `Work as
  @references/personas/<id>.md.` — the id its job maps to, per
  @references/parts/personas.md. It is chosen per dispatch, never asked, and
  it moves nothing about the session's own — which is stored nowhere either.
- Write per `@@language`, in the board `language` from `prds/settings.md` —
  named in the brief. On a master board, the language of the PRD's **own**
  board.
- Give a member's worker real paths, never `@<member>/…`. `repo` is the PRD's
  own, else the member's repo root.
- A report that is incomplete, or a worker stopped mid-task: continue THAT
  worker — it holds the context. Never respawn it.
- Report a defect found outside your scope. Do not file it and do not fix it.
  Say what is wrong, what you measured, and which requested PRD it would get
  wrong. The orchestrator decides what it becomes, per
  @references/parts/derived.md.
- A measured claim gets one of three verdicts — `reproduced`, `refuted`,
  `unmeasured`, never `exact` — with the fixture named in a parenthesis
  beside it, because a reason is only as good as the fixture it was measured
  on. A claim cheap to run is run twice, with a different input.
- A census enumerates its population; it never names the members it already
  knows. A check written from the answer passes on the answer and is blind to
  everything else. The words catch nothing on their own — only the second run
  does.

**Analyst** — one per `open` PRD being specced:

> Read `prds/<prd>/prd.md`, including `## Answers`, and explore `<repo>` as
> needed. Return exactly one verdict:
>
> - **SPECCED** — write `specs/specNN.md` files, template
>   `@references/templates/spec.md`, each one implementable unit: goal,
>   `complexity:` and `footprint:` in frontmatter, `- [ ]` acceptance boxes
>   a check can fail, and a verify command. Report the spec list, the PRD's
>   `complexity` (1-100) and `blast-radius` (`high`|`mid`|`low`) with one
>   line of reasoning each, and the union of the footprints. **Do not
>   estimate how long anything will take** — nothing schedules on time. If a
>   spec's compute cost is large enough to change its scope, price that
>   inside the spec.
> - **REFINE** — the PRD holds more than one contract, or is too thin to spec.
>   Report the proposed children, `<dir-name> — one-line contract` each, and
>   what detail is missing.
> - **QUESTION** — a real fork only the user can settle: naming, scope, cost.
>   Never a fact you could look up — find facts yourself. Write `## Questions`
>   into `prd.md` in the round format of `@references/drill.md`: each question
>   is the fork in 1-3 sentences ending in `?` — never the PRD restated — with
>   **three prepared answers**, each a complete, paste-ready decision, three
>   genuinely different versions of the outcome, one `(recommended)`. The user
>   picks one or writes their own. Writing the three is your work, not theirs.
>   Report the questions.
>
> Spec what this PRD asks for. A wrong claim you find elsewhere, or a check
> that could not fail, goes in your report as a finding — not into a spec, and
> not into a new PRD. Widening the contract is REFINE, not initiative.

On return: SPECCED → confirm the spec files exist, write `complexity:` and
`blast-radius:`, set `specced`.
REFINE / QUESTION → set the state, keep the report.

**Implementer** — one per `specced` PRD dispatched:

> Read `prds/<prd>/prd.md` and every file in `specs/`. Implement the specs in
> `<repo>`. Run each spec's `verify:` command and the repo's own gate. Tick a
> box `[x]` only for a check you actually ran, quoting output — and tick it
> **as you close it**, not in a batch at the end: those boxes are the board's
> only live view of your run, and the plan is drawn from them. If blocked,
> STOP and report **BLOCKED** with the exact question or wall — do not guess,
> do not redefine the spec. Return **DONE** (per-spec box status + verify
> output) or **FAILED** (what broke, what you tried); on FAILED also write
> `## Failure` into `prd.md`.

On return:

| report                                                                          | set                                    |
|---------------------------------------------------------------------------------|----------------------------------------|
| DONE, every box ticked, verify output shown                                      | `done`                                 |
| DONE, open boxes waiting on something named, everything the worker owns proven   | `blocked` + `needs:`                   |
| anything less                                                                    | `failed`, or answer a BLOCKED worker and let it finish |

Two unclosable boxes to catch when the specs land:

- A box asking for a **commit message** — committing is not an implementer's
  act.
- A `verify:` running the **whole workspace** — it measures the tree's worst
  neighbour, not this node's work.

A spec asking to change **another** PRD's body is the orchestrator's edit on
that transition. The worker reports the wording — one writer per file holds.

**Consultant** — one per call, per @references/parts/personas.md. Called by
the orchestrator on its own judgment as often as by the user's `ask <id>
<question>`. The persona is chosen for the question, not the job, and this is
the only brief that produces no state change:

> Work as `@references/personas/<id>.md`.
>
> The session asking you is `<transcript_path>`. The board is `<prds/>`, the
> repo `<repo>`. Read what you need from them — search for what bears on the
> question, never read the transcript whole.
>
> Question: `<the question, as the user put it>`
>
> Answer it. Say what you read to answer, and say plainly where the transcript
> did not settle it rather than filling the gap — an invented answer in your
> voice is worse than none, because it arrives wearing a persona's authority.
> Disagreeing with what the session has already concluded is the job, not a
> problem: say so, and say on what evidence.
>
> This is a conversation. Ask one clarifying question back if the question
> cannot be answered as put — that is working, not failing. Expect follow-ups
> on your answer, and answer those from what you have already read rather than
> starting over.
>
> Write nothing. No PRD, no frontmatter, no spec, no code, no commit, no file
> anywhere. A change you think is needed goes in your answer as a
> recommendation. Do not print a `▸ … · as <id>` line.

While it is open: keep it. Follow-ups, disagreements and its own clarifying
questions go to the consultant you already have — it holds the exchange, and
a fresh dispatch is a different colleague who has read none of it. The rule
is the same one that governs a stopped worker: continue THAT one, never
respawn it.

On return: relay the answer attributed to the persona, then respond to it in
your own voice. Nothing about the board moves on a consult — a recommendation
worth acting on becomes an ordinary transition in the round that follows,
made by the orchestrator, through the same gates as everything else.
