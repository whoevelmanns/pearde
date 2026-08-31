---
memo: the-persona-lives-in-the-shell
kind: decision
status: decided
subject: The session's persona is `PEARDE_AS` in the environment — exported once at install, re-exported on a switch, never a board file
date: 2026-08-28
prds:
  - the-board-runs-itself/the-next-line-runs
  - the-board-runs-itself/transitions-are-commands
---

# the-persona-lives-in-the-shell — session state goes where the session's shell already is

## Decision

Every transition command reads the persona from `--as <id>`, else `PEARDE_AS`.
`install.sh --apply` prints `export PEARDE_AS=engineer` beside the alias;
`persona <id>` is `export PEARDE_AS=<id>`. A command that files a **new** PRD
(`add`) with neither set reads `engineer` and prints `· as engineer (default)`;
every other transition refuses, naming the variable and the install line.

## Why

@references/parts/personas.md forbids a board file for the persona — it
outlives the round and lets two sessions overwrite each other's answer. The
environment is what that rule wanted: per session, gone with it, read by every
shell command without a flag. The alternative — `--as` on every command — was
built first (transitions-are-commands) and its first newcomer hit the refusal
on the line `init` itself printed as "run this next" (the-next-line-runs).

## Alternatives considered

**`--as` required everywhere, no default.** The safest record and the worst
first minute: the printed next line refuses. Rejected for `add` only, kept
for every transition that moves an existing PRD.

**Default `engineer` everywhere.** The line then lies after a `persona
skeptic` switch — the skeptic's finding that put the refusal in.

**Read the last `· as <id>` off the transcript.** The status line does this;
a command has no transcript path unless a hook hands it one.

## Consequences

- A profile that exports `PEARDE_AS=engineer` and a session that switched to
  `skeptic` without re-exporting writes `engineer` silently — the hazard the
  refusal guarded returns for a persisted shell. `persona <id>` re-exports;
  the round line still says what was written, so the lie is visible on the
  line, not hidden.
- `(default)` on the line is tolerated by `statusline.sh`'s grep (measured);
  a reader that pins the exact id must allow the suffix.
