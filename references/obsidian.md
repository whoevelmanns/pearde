# Obsidian — talking to the vault natively

The repo is the vault. Obsidian sits on top of the repo root and renders what
pearde already writes: `.pearde/prds/**/prd.md` (through the generated board notes),
`.pearde/memos/`, `.pearde/workflows/`, the knowledge layer under
`.pearde/wiki/`, every reference and spec. Nothing is duplicated into a
second location — the vault is this repo seen through Obsidian's index, and
its link resolution, backlinks and graph view are a person's read layer for
the board's own data.

Two plugins are the requirement, their settings at `@resources/board/obsidian/`
and their bundles fetched by `install.sh --apply` at pinned versions, and
seeded by `@resources/board/init.py` into any new board's `.obsidian/`:

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
<vault>/.pearde/wiki/.obsidian-api-key   the key a tool reads — mirrors
                                     .obsidian/plugins/obsidian-local-rest-api/data.json
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
curl -sk https://127.0.0.1:27124/vault/.pearde/wiki/Dashboard.md \
  -H "Authorization: Bearer $K"
```

The deep views stay in Dataview (DQL over `.pearde/wiki/board`,
`.pearde/memos`, `.pearde/workflows` — see `Dashboard.md`); the REST `search/`
answers one flat predicate per call. A round that needs joins uses
`knowledge.py` and `plan.py` directly; REST is the door for everything a
vault-shaped question needs — backlinks via `file.inlinks` stay in
Dataview's DQL, which runs in-app.

## What pearde guarantees

- **`init` seeds it.** A new board's `.obsidian/` ships with both plugins
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