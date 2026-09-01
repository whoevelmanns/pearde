# Obsidian — talking to the vault natively

The board is the vault. Obsidian roots at `.pearde/` — not the repo root —
and renders what pearde already writes: `prds/**/prd.md` (through the
generated board notes), `memos/`, `workflows/`, the knowledge layer under
`wiki/`. Nothing is duplicated into a second location — the vault is the
board seen through Obsidian's index, and its link resolution, backlinks and
graph view are a person's read layer for the board's own data.

The root is `.pearde/` because Obsidian skips every path whose name starts
with a `.` before any setting is read, and `userIgnoreFilters` only adds
ignores. From a vault at the repo root the whole board is invisible; from a
vault whose *own* root is `.pearde/` every child of it shows. So every
vault-relative path the board writes — the Dataview sources in
`Dashboard.md`, the wikilinks in `wiki/board/` — is written against
`.pearde/`, and a board from before this reads its notes one level off until
`knowledge.py board` regenerates them.

A vault directory is not enough on its own: `obsidian://open` resolves only
against Obsidian's own register (`~/Library/Application Support/obsidian/obsidian.json`,
`~/.config/obsidian/obsidian.json` on Linux). A folder that is not in it does
not open — the URI lands in the nearest registered ancestor, the repo root
when the repo is a vault too, which is exactly the wrong tree. The status
line's `▸vault` names the vault by the id that file holds for the board's
exact path.

**The register is only writable while Obsidian is closed.** The app reads it
once at launch and writes it back *from memory* on quit: an entry added under
a running app is not seen by that app (`Unable to find a vault for the URL`)
and is erased when it exits. The order that holds is quit → write → launch,
and one command is that order:

```sh
pearde vault --wait --open        # quit Obsidian when it says to
```

It seeds `.pearde/.obsidian/` if it is missing, waits for the process to go,
writes the entry, and opens the vault. Without `--wait` it refuses while the
app is running rather than writing something that will be erased. `init` calls
the same writer, and says this when it finds Obsidian up. `doctor`'s `vault`
row reads the register back and is `broken` when the entry is not there.

Two plugins are the requirement, their settings at `@resources/board/obsidian/`
and their bundles fetched by `install.sh --apply` at pinned versions, and
seeded by `@resources/board/init.py` into any new board's
`.pearde/.obsidian/`:

- **dataview** — executes the DQL/DataviewJS views in `Dashboard.md` and the
  `_index.md` files when the vault is open.
- **obsidian-local-rest-api** ("Local REST API with MCP") — the port a tool
  talks to. Serves HTTPS on `127.0.0.1:27124`; an MCP endpoint on `/mcp`
  ships in the same server, so the MCP question is settled by the same
  install — nothing extra to add when an agent wants Obsidian as tools.

## The two ways in — and when each

| | direct REST (curl / urllib) | MCP |
|---|---|---|
| setup | zero — the port answers | one config line per client (`/mcp` endpoint) |
| transport | `curl -sk https://127.0.0.1:27124/<route>` | the client's MCP handshake against `https://127.0.0.1:27124/mcp` |
| best for | rounds, scripts, `knowledge.py` verbs — anything on this machine | a chat client that wants named tools (`read note`, `search`, `patch`) |
| auth | same bearer key | same — the plugin's API key |

Same server, same key, same vault. REST when a script or a round does the
work; MCP when a chat client wants the button surface. Both die with the
Obsidian app — the files remain, the port does not.

## The connection facts

```
https://127.0.0.1:27124              base URL (HTTPS, self-signed certificate)
Authorization: Bearer <key>          every call, no exceptions
<board>/wiki/.obsidian-api-key       the key a tool reads — mirrors
                                     .obsidian/plugins/obsidian-local-rest-api/data.json,
                                     and is rewritten to match it whenever
                                     the two disagree
GET  /                               alive? -> {"status": "OK", "authenticated": …}
GET  /vault/<path>                   one note's bytes
PUT  /vault/<path>                   write one note (whole file)
PATCH /vault/<path>                  a targeted insert — Content-Type:
                                     application/vnd.olrapi.patch
POST /search/simple/?query=<q>       Obsidian's own search index, scored
POST /search/                        structured — Content-Type:
                                     application/vnd.olrapi.jsonlogic+json,
                                     {"==": [{"var": "frontmatter.state"}, "open"]}
GET  /commands/ · POST /commands/<id>   list and fire the app's 190+ commands
GET  /active/                        the note a person is looking at
GET  /open/<filename>                open one in the app
/mcp                                 the plugin's MCP server endpoint
```

The key rides at `.pearde/wiki/.obsidian-api-key` on every board
(`init` mints it fresh, in the v5 schema the plugin reads). `.pearde/wiki/`
is gitignored — the key is machine-local, like the vault itself.

## Queries that matter to the board

One-liners, real against this vault:

```sh
K=$(cat .pearde/wiki/.obsidian-api-key)
# every open PRD, through Obsidian's own frontmatter index
curl -sk -X POST https://127.0.0.1:27124/search/ -H "Authorization: Bearer $K" \
  -H "Content-Type: application/vnd.olrapi.jsonlogic+json" \
  -d '{"==": [{"var": "frontmatter.state"}, "open"]}'

# read the dashboard a person sees
curl -sk https://127.0.0.1:27124/vault/wiki/Dashboard.md \
  -H "Authorization: Bearer $K"
```

The deep views stay in Dataview (DQL over `wiki/board`, `memos`,
`workflows` — vault-relative, so `.pearde/`-relative — see `Dashboard.md`); the REST `search/`
answers one flat predicate per call. A round that needs joins uses
`knowledge.py` and `plan.py` directly; REST is the door for everything a
vault-shaped question needs — backlinks via `file.inlinks` stay in
Dataview's DQL, which runs in-app.

## What pearde guarantees

- **`init` seeds it.** A new board's `.pearde/.obsidian/` ships with both plugins
  from the preset the install fetched (`@resources/board/obsidian/`), a fresh API key minted in the v5
  schema, mirrored at `.pearde/wiki/.obsidian-api-key`. One manual step
  remains, unavoidable: Obsidian loads a vault's plugins when the person
  opens it the first time — until then the port is silent.
- **Already-installed wins.** `init` never overwrites a plugin, a key, or a
  hand-tuned config — the board conforms to the vault, never the reverse.
- **A round reads files first.** The REST port is for app-flavored work —
  the person's active note, running a search against the live index,
  driving the app. `plan.py scan`, `knowledge.py query`, and plain file
  reads already answer a board question; Obsidian is reached when the
  question is Obsidian's.