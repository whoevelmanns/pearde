# Knowledge

The research layer: what the board has learned from outside the repo, as
linked notes with provenance. The board holds process and decisions; this
holds conclusions and the sources they stand on. One question, one home — a
decision goes to a memo per @references/memo.md, knowledge here.

```
prds/knowledge/          one folder, the whole layer — the wiki, the vault, the graph
    sources/             external findings, one file per topic; raw, arguing nothing of ours
    conclusions/         synthesized answers, each derived from named sources
    pending/             research questions queued, priority-tagged, not yet run
    graphs/              generated wiki pages over the KB
    .graphify/           the note graph, graph.json (gitignored, regenerable)
    .obsidian/           the vault preset — this folder is its own Obsidian vault
    WORKFLOW.md          focus, rules, routing — the configuration every verb reads
    Dashboard.md         live Dataview views over all of it
```

The folder is the Obsidian vault: open `prds/knowledge` in Obsidian and the
dashboard renders, the graph view colors sources and conclusions, nothing
from outside needs to be open. The folder is gitignored — machine-local
data, not source. The tool that runs the loop is @resources/knowledge.py:
stdlib-only Python, every verb takes `--root`, so another board's folder
follows the same contract.

## The loop

| step | verb | decides |
|---|---|---|
| ask | `knowledge.py query "<question>"` | whether an answer is already on record |
| gap | prints `gap:` when nothing strong hits | `enqueue` the question (auto on gap) or research it now |
| capture | `remember <title>` — body on stdin, one topic per file | what the finding is, which sweep or page it came from (`--provenance`) |
| conclude | `conclude <title> --sources <slug,…>` | whether ≥ `min_sources_per_conclusion` takeaways agree enough to synthesize |
| link | `relink` | the note graph, symmetrized `related:`, `graphs/` communities via `wiki` |

- **A source states, a conclusion argues.** A source carries findings and the
  route id or URL that produced it (`--provenance`). A conclusion carries
  `sources:` naming every file it derived from — fewer than two, the tool
  refuses: a hunch, not a conclusion.
- **Wikilinks hold the graph together.** `[[their-slug]]` from conclusion to
  source and conclusion to conclusion; `relink` resolves them, symmetrizes
  `related:`, and writes `prds/knowledge/.graphify/graph.json`. Links are by
  slug or title — a note id like `260831-cbe9` and its human title both
  resolve. The graph is hand-built, no LLM pass, so no backend key is needed
  and no note orphans.
- **Scout is the tap.** A sweep finds; the ranking pages are the raw material
  per @@scout. Distill what won into `sources/` notes tagged with the bucket
  and route id, then `conclude` when a job's answer is stable.
- **Pending is not a backlog.** A question enqueued and never needed again is
  deleted, not drained to zero. Stale rows read as work owed; `doctor` names
  them.
- **The vault is output.** Edit the corpus through the tools; hand edits to
  `graphs/` die on the next `wiki`, and `Dashboard.report.md` on the next
  `dashboard --write`.
- **`doctor` closes the loop.** Frontmatter valid, every wikilink resolves,
  graph in sync with the files, pending honest. Run it after moves and
  before calling a KB fact settled.

## Where the tools end and the repo starts

The verbs write only under `prds/knowledge/` — the folder is machine-local
(gitignored) and the tool's default root is the repo it sits in; pass
`--root` to run the loop on another board's folder. Inside pearde the scope
is `@@knowledge` and its door is @skills/pearde-knowledge.md.

`WORKFLOW.md` is the configuration: `active_focus` biases `query`, `min_sources_per_conclusion`
guards `conclude`, `auto_enqueue` decides whether a gap queues itself. The
verbs re-read it on every call.

## Relationship to the rest

- **Memos cite knowledge, knowledge cites memos.** A memo's body wikilinks
  `[[<conclusion>]]` when the decision rests on recorded knowledge; a
  conclusion's body links back to the memo that consumed it. Neither moves a
  state.
- **Scout findings stay where they land.** `@resources/scout/findings.md` is
  the dated record of what a sweep measured — never copied here. The
  distilled takeaway is the note; the sweep is the citation.
- **`@@graph` maps the repo; the note graph maps the KB.** Two graphs, two
  questions. `@resources/graph/graph.sh extract` reads the corpus and can
  also run semantic passes; `knowledge.py relink` reads `prds/knowledge/`
  only, hand-built from the wikilinks, never an LLM call.
- **The dashboard is the view a person opens.** A round queries the KB
  through the tools, never by reading `Dashboard.md`.