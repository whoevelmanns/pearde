# Graph

The knowledge-graph feature, whole. One tool: [graphify](https://github.com/Graphify-Labs/graphify),
installed once per machine, driven through @resources/graph/graph.sh.

## What it is

| piece | is |
|---|---|
| `graph.json` | the persistent graph — nodes, typed edges, provenance (`EXTRACTED` / `INFERRED` / `AMBIGUOUS`) |
| `graph.html` | interactive graph — click nodes, search, filter by community |
| `obsidian/` | the graph as an Obsidian vault — one note per concept, wikilinks per edge, opened as its own vault |
| `GRAPH_REPORT.md` | god nodes, surprising connections, suggested questions |
| `cache/` | SHA256 cache — re-runs touch only changed files |

Everything lands in `.pearde/graphify/` inside the folder being mapped —
`graph.sh` redirects graphify's own default there with `GRAPHIFY_OUT`, set
absolute before every call. It is regenerable and gitignored — the graph is
data, not source.

## The backend split

Code is parsed locally with tree-sitter AST: deterministic, no LLM, nothing
leaves the machine. Docs, PDFs, images get a semantic pass through the
backend. The wrapper pins `--backend ollama` and `--model glm-5.3-flash:cloud`
— an ollama cloud model, routed by the local ollama daemon. Not local
inference; it leaves the machine. For a fully local round:

```bash
PEARDE_GRAPH_MODEL=gpt-oss:20b graph.sh extract <folder>
```

`PEARDE_GRAPH_MODEL` overrides the model for one call, `PEARDE_GRAPH_FOLDER`
the default folder.

## Commands

Every command takes the folder first, optional; default is the current
directory. Run them from a round, not for their own sake.

```bash
bash @resources/graph/graph.sh extract @.          # full: AST + semantic + clusters + vault
bash @resources/graph/graph.sh extract @. --force  # skip the incremental manifest gate and cache
bash @resources/graph/graph.sh update @.           # changed files only; code needs no LLM
bash @resources/graph/graph.sh query @. "what connects the board to the view?"
bash @resources/graph/graph.sh path @. "plan.py" "render.py"
bash @resources/graph/graph.sh explain @. "guard.py"
bash @resources/graph/graph.sh god-nodes @.
bash @resources/graph/graph.sh open @.             # .pearde/graphify/obsidian as a vault in Obsidian
```

- **Extract is the only LLM call.** Update, query, path, explain, god-nodes
  read `graph.json` locally.
- **Cloud models answer through the local daemon** — `ollama list` names what
  is available; `glm-5.3-flash:cloud` and `deepseek-v4-flash:cloud` are paired,
  `gpt-oss:20b` and `granite4:3b` run on the machine.
- **A mixed corpus needs the backend up.** Code-only work needs none — a
  failed semantic pass leaves the AST graph intact.

## The vault

`.pearde/graphify/obsidian/` is its own vault, separate from the board's —
`.pearde/` is already an Obsidian vault, and the graph's notes stay out of it
(the board vault ignores `graphify/`).
`graph.sh open` opens it in Obsidian. The vault is output: edit nothing in it,
edit the corpus and re-extract instead.

## Relationship to the rest

- The `.pearde/wiki/` KB is the research layer with its own graph of
  conclusions, hand-built by @resources/knowledge.py; graphify's graph is
  the corpus map. Different questions, kept in different vaults.
- One commit per PRD holds @references/files.md and @index.md; `.pearde/graphify/`
  never enters one.