---
name: pearde-knowledge
description: The project knowledge base — research sources and synthesized conclusions with provenance links, queried before new research, fed by scout sweeps, cross-linked into memos, graphed by wikilink and viewed through an Obsidian vault with Dataview dashboards. Use for "/pearde-knowledge", "what do we know about X", "query the knowledge base", "research <topic>", "save this finding", "record this conclusion", "what sources back this", "is this on record", "knowledge dashboard", "relink the knowledge graph".
---

Read @references/knowledge.md. The scope is `@@knowledge`. The tool is
`python3 @resources/knowledge.py <verb>` — every verb takes `--root`, the
default root is `prds/knowledge/`, the folder is its own Obsidian vault.

- `query` first. A question the KB answers costs nothing; one it does not
  prints `gap:` and goes to `enqueue` or a research pass.
- Write with `remember` and `conclude`, never by hand — the verbs carry the
  frontmatter the graph and the dashboard read; `conclude` refuses a lone
  source, per `min_sources_per_conclusion`.
- `relink` after writing (and `wiki` when the graph grew a community);
  `doctor` before calling a KB fact settled.
- Scout sweeps distill here; memo bodies wikilink in.