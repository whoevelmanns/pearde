# Plugins that propel pearde — the curated install list

Measured 2026-08-31 via GitHub search API (`topic:claude-code-plugin`,
`topic:claude-plugin`, `topic:claude-skills`, marketplace queries, each sorted
by stars), then state-checked (push date, license, archived). Stars are the
discovery layer, never the verdict — see
[`../resources/scout/findings.md`](../resources/scout/findings.md) for the row.

## How the suggestion surfaces

Plugins are Claude-Code-only, so the recommendation lives on the Claude
adapter itself: `resources/board/adapters/claude.json` carries a `plugins`
list (`{"name","marketplace","repo"}` per entry), and `doctor.sh` compares it
against the machine's install record
(`$CLAUDE_CONFIG_DIR/plugins/installed_plugins.json`, falling back to
`~/.claude/plugins/`). Run `bash resources/doctor.sh` — every missing plugin
prints its exact two install commands. `off`, never `broken`: a round runs
without these; they make it cheaper. An adapter for any other runtime carries
no list and the row stays silent — no agent is named by the check itself,
only by the adapter's own data.

## Install these

| plugin | stars | job | why it fits pearde |
|---|---|---|---|
| [ponytail](https://github.com/DietrichGebert/ponytail) | 117.9k | think like the laziest senior dev — best code is code never written | output discipline composes with caveman; MIT, active |
| [claude-hud](https://github.com/jarrodwatts/claude-hud) | 27.7k | shows context usage, active tools, running agents | makes the round visible while it runs |
| [planning-with-files](https://github.com/OthmanAdi/planning-with-files) | 26.5k | crash-proof markdown plans that survive session death | same plain-markdown conviction as the board |
| [cc-safety-net](https://github.com/kenryu42/cc-safety-net) | 1.5k | blocks destructive git/fs commands before execution | one board, many sessions, one writer per file — the guard earns its keep |

`caveman` (102k, MIT) is already installed and active on this machine.

## Add as marketplaces, browse on demand

- [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) — 35.7k — official directory
- [wshobson/agents](https://github.com/wshobson/agents) — 39.3k — multi-harness marketplace, MIT
- [obra/superpowers-marketplace](https://github.com/obra/superpowers-marketplace) — 1.2k — curated
- [davepoon/buildwithclaude](https://github.com/davepoon/buildwithclaude) — 3.4k — hub of hubs

## Do not install — pearde already is this

| plugin | stars | why reject |
|---|---|---|
| claude-mem | 92.7k | persistent memory layer — the knowledge layer already is that |
| claude-obsidian | 14.4k | second brain — same overlap |
| engram, recall, claude-db | 1.4k–0.2k | memory engines, same overlap |
| cavekit, cavemem | 1.1k / 0.7k | frozen by their own README |

The memory-plugins corner is the biggest star pool in the ecosystem and the
one this tree must not pull from — installing one rebuilds, worse and outside
the board, what `resources/knowledge.py` does natively.

## What overturns a pick

A pick going archived or frozen, or pearde shipping the job natively (as it
already did against the entire memory corner). Re-measure 2027-03-01.