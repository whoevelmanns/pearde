# The round file

`prds/.round.md` — the session's own memory, fifteen lines, rewritten at every
transition. Machine-local and git-ignored, like `prds/.plan.json`: it is what
one session is holding, not what the board is.

A context window ends without warning. When it does, everything the round
worked out — which PRD is being collected, what a check returned, what the user
answered, what is owed — is gone, and the cheapest thing the session can do
next is the most expensive thing it can do: re-read the specs, re-run the
sweeps, re-derive the conclusion it already had. This file is the alternative,
and it costs one write per transition.

## What goes in it

Only what `@resources/board/plan.py scan` cannot print. The scan already has
every state, weight, gate, claim and box count — copying those in makes the
file wrong the moment a worker moves.

```markdown
# Round — <what this round is doing>

## Established
- <fact> — <how it was checked> · <time>

## Decided
- <decision> — <what it beat, in a clause>

## Asked
- <question put to the user> · <answered | out>

## Owed
- <the next action, as an action>
```

- **Established** is the section that pays for the file: a count, a diff, a
  command's verdict, with the time on it. A fact in here is cited, never
  re-run — @references/parts/loop.md.
- **Decided** is the round's judgment calls. A decision the code will not
  explain graduates to a memo, per @references/parts/memos.md; this is the
  scratch it is drafted in.
- **Asked** is the live frontier: what went to the user and whether it came
  back. A question in here is never re-asked.
- **Owed** is one line, in the imperative, and it is the first thing the next
  turn does.

## When it is written

At every transition — the same moment the progress line is printed. Steps 2,
3, 6 and 7 of the loop all move something; each rewrites this file whole
before it moves on. Never appended and never sectioned by round: the file says
what is true now, and there is nothing to prune later.

## After a compaction

Read this file, run `scan`, act. In that order and nothing else — no spec
re-read, no tree sweep, no re-derivation of a conclusion the file already
carries. If the file does not carry it, that is the bug: write it down this
time.

If the steps themselves are gone, re-read @references/parts/loop.md — that
one file, not the `@@loop` scope and not the reference tree behind it. A round
that re-opens the manual after every compaction pays for the manual as many
times as it compacts.
