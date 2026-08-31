---
complexity: 4
footprint:
  - resources/guard.py
  - references/parts/guard.md
  - prds/nothing-left-open/a-quoted-walk-is-data/probe/verify.sh
---

# spec01 — the Bash hook matches a walk on what the shell runs

`guard.py pre`, on a `Bash` call, matches the `WALKS` rules against
`data_free(command)` instead of the raw command: heredoc bodies and quoted
strings are blanked first, except a string given to a command that runs it —
`find`, `grep`, `rg`, `ls` (the pattern *is* the walk) and `sh`/`bash`/`zsh`
/`eval` (the string is a command). A prefix (`env`, `sudo`, `X=1`) does not
hide the command word behind it. A walk after a heredoc, after a `;`, or
piped into a quoted interpreter is still the walk. Nothing else in the hook
moves; the deny text is unchanged.

`references/parts/guard.md`'s refusals table says, on the walk row, that a
walk carried as data — a script piped to python, a fixture, a refusal quoted
into a memo — is not a walk.

## Verify

```
bash prds/nothing-left-open/a-quoted-walk-is-data/probe/verify.sh
PEARDE_GUARD_STATE=$(mktemp -d) bash prds/the-tool-keeps-its-word/guard-on-is-one-command/probe/verify.sh | tail -1
PEARDE_GUARD_STATE=$(mktemp -d) bash prds/nothing-left-open/the-skill-tree-is-guarded/probe/verify.sh | tail -1
PEARDE_GUARD_STATE=$(mktemp -d) bash prds/the-board-runs-itself/the-loop-is-commands/probe/verify.sh | tail -1
python3 resources/guard.py status /Users/feb/dev/infra/pearde | head -1
```

## Done when

- [ ] the probe prints `19 checks · 19 pass · 0 fail`
- [ ] guard-on-is-one-command still `78 checks · 78 pass · 0 fail`
- [ ] the-skill-tree-is-guarded still `41 checks · 41 pass · 0 fail`
- [ ] the-loop-is-commands: no count dropped from its baseline (`60 checks`, one pre-existing red line `loop.md is 130 lines` from another session's dirty file, or 60/60 once that lands)
- [ ] `guard status` on this repo still reads `ok … skill tree guarded`
