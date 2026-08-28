---
memo: the-orchestrator-may-write-a-spec
kind: decision
status: decided
subject: The orchestrator may write a spec, and only to close a rule the PRD already states
date: 2026-08-28
prds:
  - workflows-on-the-board/workflow-attach
---

# the-orchestrator-may-write-a-spec — one spec, and only to close a rule already written

## Decision

The orchestrator may write a `specNN.md` on a PRD it is collecting, and only
for this: a rule the PRD's own body already states that no spec closes. It
widens the footprint by whatever file carries the rule, records the widening on
the PRD's frontmatter, and hands the spec to the implementer in the same round.

It may not write a spec that adds a requirement the PRD does not already make.
That is REFINE, or a new PRD, and it is the analyst's to propose.

## Why

`workflows-on-the-board/workflow-attach` said in its committed `## Rules` that
a PRD whose `workflow:` resolves to nothing *"is not dispatched until it is
fixed or removed"*. Its analyst built the three units its `## Files` table
asked for, reported that nothing enforced that rule, named the two ways to
close it, and declined both because each widens the footprint by a file. That
was the correct analyst call — @references/parts/workers.md tells a worker
that widening the contract is REFINE, not initiative.

But the contract was not being widened. The sentence was already there, in a
committed body, as context in the diff rather than as an addition. What was
missing was a spec, and specs are written by whoever is holding the PRD at the
moment the gap is found. Sending it back as a REFINE would have created a
child PRD whose entire deliverable is one paragraph — the shape
@references/parts/derived.md's tripwire exists to prevent. Putting it to the
user would have been asking permission to finish what the PRD already said.

The narrowness is the whole of the rule. An orchestrator that may write specs
freely is an orchestrator that specs its own preferences into other people's
PRDs, and the board loses the one property that makes its states trustworthy:
that the contract came from the user and the analyst, and the orchestrator only
moves the states.

## Alternatives considered

**REFINE it back to a child PRD** — the mechanism the board already has for
work that does not fit. It lost on proportion: a child PRD carries a `prd.md`,
an analyst dispatch, an implementer dispatch and a commit, to land one
paragraph in a file the parent already touches. `derived.md` names that shape
as the loop feeding on itself.

**Put the fork to the user** — three prepared answers, the drill format. It
lost because there is no fork. The PRD already decided; the only question was
whether anyone would do it. A drill round that asks the user to confirm their
own written rule spends the one resource the board cannot make more of.

**Leave the rule unenforced and note it** — the cheapest option, and the one
this session had already been burned by twice: a struck acceptance box whose
obligation nearly landed as prose, and a check comment that argued a
disagreement without naming its consequence. A rule with no mechanism is a
note, and a note in a document that reads like a rule is worse than silence.

## Consequences

- @references/parts/contract.md attributes every `specNN.md` key —
  `complexity`, `footprint`, `workflow`, `est` — to **the analyst**, and has no
  row for a spec the orchestrator wrote. Until that row exists this act is
  permitted but unnamed, which is the state this memo half-repairs: it records
  the decision, and the row is still owed.
- The widening has to be visible or it is invisible: the footprint key on the
  PRD is the only place a later reader sees that the file was added, and it
  says nothing about who added it or why. This memo is that record, and
  `prds:` above is the link back.
- It deliberately does not settle whether the orchestrator may write a spec on
  a PRD it did **not** dispatch — a `failed` post-mortem, say, or a `blocked`
  PRD it is unblocking by hand. That case has not come up. When it does, it is
  the next memo's.
