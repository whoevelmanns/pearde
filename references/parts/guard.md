# The guard

@resources/guard.py — the loop's rules as a mechanism rather than a sentence.

@references/parts/loop.md says a step is one command and one decision, that
the board is read with one `scan`, and that an established fact is cited
rather than re-run. A model that ignores those sentences still burns the context
window; the round that cost 318,584 output tokens ignored all three. The guard
is the same three rules where ignoring them is not possible.

## What it refuses

| the call | what it says |
|---|---|
| a board walked by hand — `find … prd.md`, `grep -r state:`, `ls prds/*/prd.md` | step 1 is `plan.py scan`, and it already answers this |
| a board-reading command run twice with nothing changed since | the output is byte-for-byte what you have; cite it from `prds/.round.md` |
| a third read of the same file, unchanged since the first | what you needed from it belongs in the round file |
| a third read of a **reference** file — this manual, through any install link | the manual does not move while a round runs. @references/parts/loop.md and @references/parts/round.md are exempt, because a compacted round has to be able to re-read the steps |
| an `Edit` or `Write` that changes the `state:` line of a `prd.md` — or writes a new `prd.md` carrying one | `use pearde set <prd> <state>`: the command checks the gate of @references/parts/states.md, and a new PRD is `pearde add` or `pearde refine`. A body edit passes. @resources/board/transitions.py writes through @resources/board/edit.py, never through a tool call, so it is never matched — and a worker's shell passes every gate a command has, which is why "never run a transition" stays a sentence in the brief |

And two it only comments on:

- The first read of a spec says the boxes are counted for you — `boxes c/t` in
  the scan. The spec is read for its contract, never to count.
- A `prd.md` written while `prds/.round.md` is older than it says the round
  file is owed. A command is never a tool edit, so every transition command
  says the same on its own line — `round file owed`, before `as`.

A reference is keyed by its real path, so the same file read once here and
once through a skill folder of links is one file, not two.

**It refuses only what is provably redundant.** "Nothing changed" is the
newest mtime of any `.md` under the board and its members — 7 ms on a
227-PRD master board. An unchanged stamp means an identical answer, which is
why the refusal is safe; a board that moved lets the same command straight
through. `plan.py` itself is never refused: a round recovering from a
compaction has to be able to ask again, and that is exactly when the board has
not moved.

Anything outside a board is not its business, and a guard that throws exits
zero — a broken guard must never be able to block a tool call.

## Wiring it

Project settings in the repo the board lives in, `.claude/settings.json`:

```json
{
  "env": { "MAX_THINKING_TOKENS": "8000" },
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash|Read",
      "hooks": [{ "type": "command",
                  "command": "python3 <pearde>/resources/guard.py pre" }]
    }, {
      "matcher": "Edit|Write",
      "hooks": [{ "type": "command",
                  "command": "python3 <pearde>/resources/guard.py pre" }]
    }],
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{ "type": "command",
                  "command": "python3 <pearde>/resources/guard.py post" }]
    }]
  }
}
```

`<pearde>` is this repo's absolute path. The `state:` refusal is a mechanism
exactly where this block is wired and a sentence everywhere else. `doctor`
reports `guard` as `ok`, `off` or `broken` and prints the file it looked in;
it does not write the block, for the same reason it does not wire a status line — a settings file is
the reader's, and this one decides what their tools may refuse. A newly
created `.claude/settings.json` is picked up after `/hooks` or a restart: the
settings watcher only watches directories that had a settings file when the
session started.

**`MAX_THINKING_TOKENS` is the other half.** The guard bounds what a round
re-reads; the cap bounds what it can think in one response. The round that
prompted all of this produced five responses that each hit a 32,000-token
output ceiling inside a thinking block and emitted nothing at all — no tool
call, no text — and were retried into the same analysis. No productive
thinking block in that session exceeded 7,073 tokens. 8,000 is above every one
of them and a quarter of the ceiling that was being hit.

## Turning it off

Delete the `hooks` block, or set `disableAllHooks` for a session that needs a
free hand. The guard holds no state on the board — one JSON file per session
under `resources/board/state/guard/`, which is machine-local like everything
else in that directory.

An orchestrator that hits a refusal it believes is wrong should say so in the
round rather than working around it: a false refusal is a bug in the stamp,
and the stamp is one function.
