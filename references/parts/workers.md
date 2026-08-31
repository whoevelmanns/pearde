# Worker briefs

The exact text to hand an analyst and an implementer.

Hand each worker the output of `pearde brief <prd>` — one command, nothing
composed. `@` and `@@` resolve in @index.md.

Rules for every worker:

- Never edit frontmatter, never touch other PRDs, never write outside the PRD
  folder. Implementers also write the target repo.
- Open the brief with one line naming the worker's persona — `Work as
  @references/personas/<id>.md.` — read off this table, never asked, and it
  moves nothing about the session's own. This table is the whole of it: a
  dispatch never opens @references/parts/personas.md, which answers a
  different question — who works the *session*.

  | the job                                                        | wears      |
  |----------------------------------------------------------------|------------|
  | the contract is user flow, product shape, or a user-facing name | `designer` |
  | re-checking finished work, or a `failed` post-mortem            | `skeptic`  |
  | anything else — every ordinary analyst and implementer          | `engineer` |
- Write per `@@language`, in the board `language` from `prds/settings.md` —
  named in the brief. On a master board, the language of the PRD's **own**
  board.
- A report that is incomplete, or a worker stopped mid-task: continue THAT
  worker — it holds the context. Never respawn it.
- Report a defect found outside your scope. Do not file it and do not fix it.
  Say what is wrong, what you measured, and which requested PRD it would get
  wrong. The orchestrator decides what it becomes, per
  @references/parts/derived.md.
- Two rules for **contested or load-bearing claims** — never for every
  sentence of a routine report, which states what was done and quotes its
  verify output, nothing more: a measured claim gets `reproduced`, `refuted`
  or `unmeasured` with the fixture named beside it, and a census enumerates
  its population rather than the members it already knows — a check written
  from the answer passes on the answer.

**Every worker, on top of its role.** `pearde brief` prints this last:

<!-- brief:every -->
> Write in `<language>`, per @references/language.md. Never edit frontmatter,
> never touch another PRD, never write outside `prds/<prd>/` and the
> footprint. A defect outside your scope goes in the report, not into a fix.
<!-- /brief -->

**Placeholders.** `pearde brief` fills these and nothing else. A placeholder
is `<name>` — lowercase, `_` or `/` inside; one a block uses and this table
does not name, a row nothing uses, or a marker pair missing or unterminated,
is the `doctor` row `briefs`.

| placeholder | filled from |
|---|---|
| `<prd>` | the PRD's real path under `prds/` — never `@<member>/…` |
| `<repo>` | the PRD's `repo:` when it is a directory, else the member's repo root, else the board's |
| `<language>` | `language` in the PRD's own board's `settings.md` |
| `<probe>` | `prds/<prd>/probe/` — where probe code lives |
| `<board>` | the board whose library holds the slug, for `workflows.py brief` |
| `<split_above>` | `split-above` in the PRD's own board's `settings.md`, default 40 — @references/settings.md |
| `<specs_above>` | `specs-above` there, default 6 |
| `<slug>` | the `workflow:` the block is printed for — in the analyst block it is the worker's to write |
| `<id>` | `--as`, default `engineer`; `--consult <id>` |
| `<transcript_path>` | `--transcript` |
| `<prds/>` | the board path |
| `<the question, as the user put it>` | `--question` |

**The workflow block.** When the PRD (or, for an implementer, a spec) carries
`workflow: <slug>`, this opens the brief immediately after the persona line,
verbatim, placeholders filled — nothing else about the brief changes:

<!-- brief:workflow -->
> Follow the workflow `<slug>`: `python3 @resources/workflows.py brief <slug>
> <board>` prints it — the steps in order, each with its atomic inlined. Take
> the steps in order. When a step fails, go where its `on failure` says; a
> back-edge is taken at most twice, then stop and report with the step named.
> Your report carries `## Workflow <slug>` per @references/workflow.md: one
> row per step, and under `### Edits` the replacement text for every failure
> the atomic caused — a wrong command, a stale path, a check that cannot
> fail, a shape `## Fails when` does not list. Never edit the workflow files
> yourself.
<!-- /brief -->

- No `workflow:` anywhere: no block, and the brief is exactly as it was.
- A spec with its own `workflow:` — the implementer follows that one for that
  spec and the PRD's for the rest, so the brief carries one block per distinct
  slug and the report one `## Workflow` section per workflow followed.
- **A worker never writes under `workflows/`.** Edits go in the report; what
  becomes of them is @references/parts/workflows.md.
- A slug that names no workflow is a broken PRD, not a silent one: it is not
  dispatched until the key is fixed or removed. `python3
  @resources/workflows.py check` reports it and `plan.py scan` marks the line
  `wf <slug>?` — naming an atomic marks the same way, a route was asked for
  and a single step was found.
- A member's worker resolves the slug against its own board's library first,
  then the master's — the order `needs:` resolves in.

**On return, either brief.** `## Workflow <slug>` present in the report is a
route that was run, and the run is what improves it. The five actions are
@references/parts/loop.md step 6, in the same batch as the collect: read the
rows, apply the edits whose failure was the atomic's and refuse the rest saying
which, `runs` +1 on the workflow and every atomic that ran with `updated:
<today>` where the text changed, `python3 @resources/workflows.py check` before
the commit, and the changed files on the PRD's commit. Absent, there is nothing
to collect and the PRD's transition is unchanged either way — the verdict
decides the state, and a `stopped` row does not.

**Analyst** — one per `open` PRD being probed:

<!-- brief:analyst -->
> Read `prds/<prd>/prd.md`, including `## Answers`. Then **build it** — never
> spec from reading. Attempt the implementation in `<repo>` and keep going
> until it works or until it hits something undefined. The attempt is the
> analysis: whatever the build passes through needs no question, and whatever
> it hits is the finding. Leave the probe code in the tree, uncommitted, on
> every verdict — it is pass one, and the next worker continues it. Return
> exactly one verdict:
>
> - **SPECCED** — the build went through, or far enough that only defined
>   work remains. Write `specs/specNN.md` files from what you built, template
>   `@references/templates/spec.md`, each one implementable unit: goal,
>   `complexity:` and `footprint:` in frontmatter, `- [ ]` acceptance boxes
>   a check can fail, and a verify command. Each spec says what already
>   stands and what is left to finish. Report the spec list, the PRD's
>   `complexity` (1-100) and `blast-radius` (`high`|`mid`|`low`) with one
>   line of reasoning each, and the union of the footprints. Name the
>   workflow you followed — `workflow: <slug>`, or `workflow: none fit`, and
>   a job you saw recur is a finding in the report, never a file you write.
>   **Do not estimate how long anything will take.** If a spec's compute cost
>   is large enough to change its scope, price that inside the spec.
>   End the report with the block the orchestrator reads the values off,
>   verbatim:
>
>   ```
>   ## Scores
>
>   complexity: <N>
>   blast-radius: high|mid|low
>   workflow: <slug> | none fit
>   ```
> - **REFINE** — the build hit a missing piece big enough to be its own
>   contract, or the PRD holds more than one. Report the proposed children,
>   `<dir-name> — one-line contract` each, and for each the thing the build
>   hit that it answers. End the report with the table `pearde refine`
>   reads, verbatim:
>
>   ```
>   ## Split
>
>   | child | contract | needs |
>   |---|---|---|
>   | <dir-name> | <one line — what exists when it is done> | <sibling dir names, comma-separated, or —> |
>   ```
> - **QUESTION** — the build hit a fork it cannot pick and cannot build
>   around. **Only a fork you actually hit** — never a hedge, never "should
>   I also check", never a fact: the build is how facts are found, and a
>   question your probe did not run into is not yours to ask. Write
>   `## Questions` into `prd.md` in the round format of
>   `@references/drill.md`: each question is the fork in **two sentences,
>   then the question mark** — what is being chosen, and what it changes for
>   the person answering, never the PRD restated — with **three prepared
>   answers**, each one plain sentence of what they get, three genuinely
>   different versions of the outcome, one `(recommended)`. **Write for the
>   person who asked for this, not for the orchestrator**: no backtick, no
>   path, no file extension, no PRD name, no board word, 60 words in the fork
>   and 25 in an answer. `@references/drill.md`'s table is the whole rule and
>   `@resources/questions.py` enforces it, so a round that breaks it is
>   refused rather than written. Like this:
>
>   ```
>   ### Q1: What the page shows first
>
>   You are choosing what a person sees first when they open the board: the
>   work in progress, or the questions waiting on them. Whichever is first is
>   what they will act on; the other needs a click?
>
>   1. **Questions first** — the page opens on what is waiting on you; the work is one click away. (recommended)
>   2. **Work first** — the page opens on what is happening; your questions are one click away.
>   3. **Ask each time** — the page remembers whichever you opened last.
>
>   <!-- for the board: serve.py `/` default route; the-page-shows-the-round spec02 -->
>   ```
>
>   The last line is an HTML comment holding the technical anchor — which
>   files, which slug, which spec the answer lands in. Nothing that shows the
>   question to a person shows it; the orchestrator reads it when it acts on
>   the answer. Say what the build was doing when it hit each. Report the
>   questions. Write the `## Questions` heading only with the round under it —
>   an empty one stops the board on nothing, and `@resources/questions.py`
>   reports it.
>
> A build whose specs would sum `complexity` above `<split_above>` or count
> above `<specs_above>` returns REFINE with a `## Split` table, never
> SPECCED — the two numbers are the board's `settings.md`, and `pearde
> specced` refuses a set over either. A child over a limit is REFINEd in its
> turn.
>
> Spec what this PRD asks for. A wrong claim you find elsewhere, or a check
> that could not fail, goes in your report as a finding — not into a spec, and
> not into a new PRD. Widening the contract is REFINE, not initiative.
>
> Probe code lives at `<probe>` — `prds/` is outside the manifest scan, so it
> costs no row and travels with the PRD. Build every fixture in a directory
> made at run time, never under `prds/` — a directory holding `prd.md`
> anywhere under the board is a PRD. Quote a box spelling into a PRD or a
> spec backtick-quoted — the matcher is line-based, and a pasted `- [ ]` is
> a real box.
<!-- /brief -->

On return: SPECCED → `pearde specced <prd> --blast <x> [--workflow <slug>]`,
the values off `## Scores` — the command reads the spec files, refuses what
is not a spec naming file and line, and sums the weight — and hand it to its
implementer in the same round, never to a shelf.
REFINE → `pearde refine <prd> < report` — the children exist from the
`## Split` table and the parent is `open`. QUESTION → set the state, keep
the report. The probe code stays in
the tree either way; a PRD abandoned with probe code in it is named in the
report, so the sweep reads it as pass one and not as damage.

**Implementer** — one per `specced` PRD dispatched:

<!-- brief:implementer -->
> Read `prds/<prd>/prd.md` and every file in `specs/`. The tree already
> holds the probe's uncommitted code — continue it, it is pass one; the specs
> were written from it. Implement the specs in `<repo>`. Run each spec's `## Verify and Proof` block and the repo's own gate. Tick a
> box `[x]` only for a check you actually ran, quoting output — and tick it
> **as you close it**, not in a batch at the end: those boxes are the board's
> only live view of your run, and the plan is drawn from them. If blocked,
> STOP and report **BLOCKED** with the exact question or wall — do not guess,
> do not redefine the spec. Return **DONE** (per-spec box status + verify
> output) or **FAILED** (what broke, what you tried); on FAILED also write
> `## Failure` into `prd.md`.
<!-- /brief -->

On return:

| report                                                                          | set                                    |
|---------------------------------------------------------------------------------|----------------------------------------|
| DONE, every box ticked, verify output shown                                      | `done`                                 |
| DONE, open boxes waiting on something named, everything the worker owns proven   | `blocked` + `needs:`                   |
| anything less                                                                    | `failed`, or answer a BLOCKED worker and let it finish |
| any of the three, plus `## Workflow <slug>`                                      | the row's state, and the five actions above |

Two unclosable boxes, caught at the gate rather than by eye: `pearde
specced` refuses a box that asks the worker to commit — committing is not an
implementer's act — and warns on a `## Verify and Proof` block naming no path
under the footprint, because a whole-workspace command measures the tree's
worst neighbour, not this node's work.

A spec asking to change **another** PRD's body is the orchestrator's edit on
that transition. The worker reports the wording — one writer per file holds.

**Consultant** — one per call, per @references/parts/consult.md. Called by
the orchestrator on its own judgment as often as by the user's `ask <id>
<question>`. The persona is chosen for the question, not the job, and this is
the only brief that produces no state change:

<!-- brief:consultant -->
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
<!-- /brief -->

While it is open: keep it. Follow-ups, disagreements and its own clarifying
questions go to the consultant you already have — it holds the exchange, and
a fresh dispatch is a different colleague who has read none of it. The rule
is the same one that governs a stopped worker: continue THAT one, never
respawn it.

On return: relay the answer attributed to the persona, then respond to it in
your own voice. Nothing about the board moves on a consult — a recommendation
worth acting on becomes an ordinary transition in the round that follows,
made by the orchestrator, through the same gates as everything else.
