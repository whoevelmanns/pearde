# Targets

Where a skill goes so an agent finds it. One row per agent, and the row is
the whole of what this repo knows about that agent — no agent is named
anywhere else in the code. Adding one is adding a row.

`@resources/targets.py` is the only reader. `@resources/install.sh` links
against it and `@resources/doctor.sh` reports against it. A row is data: no
agent is named in any script in this repo.

## What a skill is, everywhere

A folder under `skills/` holding a `SKILL.md` with `name:` and
`description:` in frontmatter. The folder name is the skill name. Nothing in
that folder points outside it: `references`, `resources`, `README.md` and
`index.md` are symlinks committed alongside `SKILL.md`, relative to the
folder's real location, so the same folder reads the same whether it is
opened here or through a link somewhere else.

That is the entire portable contract. An agent that reads skill folders gets
a symlink. An agent that reads one instructions file gets a block pointing at
the folders where they actually are.

## The rows

**`present`** — a path whose existence means this agent is on the machine.
Several are alternatives, `·` separated, first hit wins. Nothing exists →
the agent is absent, and every row about it reports `off`, never `broken`.

**`skills`** — the directory the agent discovers skill folders in. One
symlink per skill is made there. `—` means the agent has no such directory;
it is served by `context` alone.

**`context`** — the instructions file appended with the block from
@references/system.md, between its `pearde:begin` / `pearde:end` markers.
`—` means the agent does not read one.

**`status`** — where a continuously-rendered line is configured, spelled
`<file>:<dotted.key>`, first hit wins. `@resources/statusline.sh` is the
command that belongs there. `—` means the agent renders nothing continuously,
and the numbers are asked for instead.

**Scope is spelled by the path.** A path starting `$`, `~` or `/` is
machine-wide and installed once. A bare relative path is per-project and
resolves against the repo being worked in.

| agent | present | skills | context | status |
|---|---|---|---|---|
| claude | `$CLAUDE_CONFIG_DIR` · `~/.claude` | `$CLAUDE_CONFIG_DIR/skills` · `~/.claude/skills` | `CLAUDE.md` | `.claude/settings.local.json:statusLine.command` · `.claude/settings.json:statusLine.command` · `$CLAUDE_CONFIG_DIR/settings.json:statusLine.command` · `~/.claude/settings.json:statusLine.command` |
| codex | `~/.codex` | — | `AGENTS.md` | — |
| cursor | `~/.cursor` · `.cursor` | `.cursor/skills` | `.cursor/rules/pearde.md` | — |
| windsurf | `~/.windsurf` · `.windsurf` | `.windsurf/skills` | `.windsurf/rules/pearde.md` | — |
| gemini | `~/.gemini` | — | `GEMINI.md` | — |
| cline | `.clinerules` | — | `.clinerules/pearde.md` | — |
| opencode | `~/.config/opencode` | — | `AGENTS.md` | — |

`$CLAUDE_CONFIG_DIR` is why `present` takes alternatives at all: the variable
moves an agent's whole configuration, so a machine can hold several profiles
and a link written into the wrong one is correct and inert. Unset variables
drop out of the list rather than expanding to a path at `/skills`.

## Neither tier

An agent with no `skills` directory and no `context` file is not a gap.
Every skill folder is readable where it lies — `skills/<name>/SKILL.md` and
what it links to — and pointing that agent at the path by hand is the whole
install. `@resources/doctor.sh` prints those paths when it finds no target at
all, so a machine with no supported agent still gets a working answer.
