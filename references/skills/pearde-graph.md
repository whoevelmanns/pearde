---
name: pearde-graph
description: Knowledge-graph rounds over this repo or any folder, via graphify with a local Ollama backend — deterministic code AST, semantic concept extraction over docs through ollama cloud models, a queryable graph.json, an interactive graph.html, and an Obsidian vault written to .pearde/graphify/obsidian/. Use for "/pearde-graph", "graph the repo", "graphify extract", "query the knowledge graph", "what connects X to Y", "god nodes", "graph path between A and B", "explain node X", "open the graph vault", "update the graph".
---

Read @references/graph.md. The scope is `@@graph`. The tool runs through
@resources/graph/graph.sh — never invoke `graphify` by hand for a round; the
wrapper holds the backend and model choices.