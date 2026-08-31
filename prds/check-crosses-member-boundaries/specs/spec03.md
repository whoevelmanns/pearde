---
complexity: 4
workflow: implement-a-spec
footprint:
  - resources/workflows.py
---

# spec03 — `brief` keeps the shape of `## Use when` instead of gluing it into one run-on

`brief` reduced the `## Use when` section with `[l for l in use if l.strip()]`,
dropping every blank line in it. A `## Use when` whose bullets are followed by
a paragraph therefore rendered with the paragraph welded onto the last bullet —
on the one page a worker actually reads before starting. No file in the library
triggers it today only because the analyst who hit it worked around it by
making its closing sentence a bullet, so the defect is latent rather than
absent and every future workflow needing more than a flat list meets it.

**What already stands.** All of it, in the working tree: the blanks at the two
ends are trimmed and the ones in the middle are kept, which is what the two
loops do and what the comment explains.

**What is left.** Nothing in code.

**Why not simply keep every line.** The blanks at the ends come from the
section split, not from the author, and passing them through puts a stray
blank between the `## Use when` heading and its first bullet and another
before the first step heading. Trimming the ends and keeping the interior is
the smallest rule that renders an authored section as it was authored.

## Acceptance

- [x] a `## Use when` holding bullets, a blank line, and a paragraph renders with that blank line intact
- [x] the paragraph is not welded onto the last bullet
- [x] no stray blank line appears between the `## Use when` heading and its first bullet, or before the first step heading
- [x] `brief` on a `## Use when` that is a flat list of bullets renders exactly as it did before
- [x] `bash prds/workflows-on-the-board/workflow-reader/verify.sh` still passes at its full total

## Verify and Proof

```sh
bash prds/check-crosses-member-boundaries/probe/verify.sh
bash prds/check-crosses-member-boundaries/probe/verify.sh --vs-head
bash prds/workflows-on-the-board/workflow-reader/verify.sh
python3 resources/workflows.py brief probe-then-spec | head -20
```

The harness's `brief` check is one of the ten that fail against HEAD — run
`--vs-head` to see it named. Boxes 3, 4 and 5 pass against HEAD as well: they
are regression guards on behaviour that was already correct, and they exist to
catch a fix that over-corrects by passing every blank through.

## Boxes closed by the orchestrator — 2026-08-29

The implementer was killed eleven times without recording a tick — the machine
slept or the connection dropped at or before its first command, every time. I
verified the twenty-one myself against the analyst's harness rather than resume
a twelfth.

What the evidence is:

```
probe/verify.sh              verify: 18/18 checks pass
probe/verify.sh --vs-head    vs HEAD: 10 of 18 checks FAIL against the unpatched readers
workflow-reader/verify.sh    verify: 39/39 checks pass
index.py check · workflows.py check · doctor.sh    all exit 0
```

The eighteen harness checks carry the behavioural boxes; I read their labels and
mapped each to the box it closes. Four boxes are not behavioural — two assert
prose in `references/workflow.md`, two assert the gates — and I checked those
directly.

**One correction worth recording, because it is the failure this PRD is about.**
My first grep for the prose boxes returned zero for *"the library does not
merge"* and *"the key holds one slug"*, and I nearly recorded them as unmet. The
document says both — as `The library does **not** merge` and `The key holds
**one slug**`, with markdown bold inside the phrase my pattern required to be
contiguous. The check was wrong, not the work. That is the same defect this
board has found in three acceptance lines this week, and I walked into it while
verifying somebody else's.

Ticked by the orchestrator, not by a worker. The evidence above is mine and the
build is the analyst's.
