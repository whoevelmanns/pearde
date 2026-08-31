---
type: dashboard
---

# Pearde Dashboard

Live views over the board and the knowledge base. Requires Dataview (DQL + JS).

> Configure focus + workflow in [[WORKFLOW]]. Regenerate the board notes with `python3 resources/knowledge.py board`.

## Board — PRDs by state

```dataview
TABLE WITHOUT ID file.link AS "PRD", state, origin, priority, complexity, blast AS "blast-radius"
FROM "prds/knowledge/board"
SORT choice(state = "blocked", 0, choice(state = "open", 1, choice(state = "analyzing", 2, 3))) ASC, priority DESC
```

## Board — open work ordered the way plan.py orders it

Dependency first (unresolved needs), then priority. The same three axes the scheduler reads: needs, priority, complexity.

```dataview
TABLE WITHOUT ID file.link AS "PRD", needs AS "Gated on", priority, complexity, blast AS "Blast"
FROM "prds/knowledge/board"
WHERE state != "done" AND state != "failed"
FLATTEN needs AS need
WHERE need.file.state != "done"
GROUP BY file.link AS PRD
SORT PRD.priority DESC
```

## Board — fed-by chains (what does this unblock)

```dataview
TABLE WITHOUT ID file.link AS "PRD", length(file.inlinks) AS "Dependents", state
FROM "prds/knowledge/board"
WHERE length(file.inlinks) > 0 AND state != "done"
SORT length(file.inlinks) DESC
```

## Board — derived lines (from → children)

```dataview
TABLE WITHOUT ID file.link AS "Child", from AS "Derived from", state, origin
FROM "prds/knowledge/board"
WHERE from
SORT from ASC
```

## Board — footprint heatmap

Which files the touched-and-open PRDs point at — overlapping footprints are merge hazards.

```dataview
TABLE WITHOUT ID footprint AS "Path", length(rows) AS "Open PRDs touching it"
FROM "prds/knowledge/board"
WHERE footprint AND state != "done" AND state != "failed"
FLATTEN footprint AS footprint
GROUP BY footprint
SORT length(rows) DESC
LIMIT 20
```

## Board — memos citing PRDs (decision record)

```dataview
TABLE WITHOUT ID file.link AS "Memo", kind, status, subject
FROM "prds/memos"
WHERE status != "superseded"
SORT file.name DESC
```

## Board — workflows and what runs on them

```dataview
TABLE WITHOUT ID file.link AS "Workflow", length(file.inlinks) AS "PRDs on it"
FROM "prds/workflows"
SORT length(file.inlinks) DESC
```

## KB — counts

```dataview
TABLE WITHOUT ID type AS "Type", length(rows) AS "Count"
FROM "prds/knowledge/conclusions" OR "prds/knowledge/sources" OR "prds/knowledge/pending"
WHERE type
GROUP BY type
SORT length(rows) DESC
```

## KB — the loop's queue

```dataview
TABLE WITHOUT ID file.link AS "Question", priority, requested_by, date
FROM "prds/knowledge/pending"
WHERE status = "pending"
SORT choice(priority = "high", 0, choice(priority = "med", 1, 2)) ASC, date ASC
```

## KB — most important nodes (hub ranking)

Inbound link count is a proxy for centrality.

```dataview
TABLE WITHOUT ID file.link AS "Node", length(file.inlinks) AS "Inlinks", length(file.outlinks) AS "Outlinks", type
FROM "prds/knowledge/conclusions" OR "prds/knowledge/sources"
WHERE length(file.inlinks) > 0
SORT length(file.inlinks) DESC
LIMIT 20
```

## KB — sources awaiting synthesis

Sources with no inbound link from a conclusion — candidates for the next `conclude` pass.

```dataview
TABLE WITHOUT ID file.link AS "Source", length(file.inlinks) AS "Inlinks", date
FROM "prds/knowledge/sources"
WHERE length(filter(file.inlinks, (l) => startswith(meta(l).path, "prds/knowledge/conclusions"))) = 0
SORT length(file.inlinks) DESC, date DESC
LIMIT 25
```

## KB — orphans (isolated nodes)

No inbound, no outbound links. Candidates for `relink`.

```dataview
LIST
FROM "prds/knowledge/conclusions" OR "prds/knowledge/sources"
WHERE length(file.inlinks) = 0 AND length(file.outlinks) = 0
LIMIT 25
```

## KB — by focus (from WORKFLOW.md)

```dataviewjs
const wf = dv.page("prds/knowledge/WORKFLOW");
const focus = (wf?.active_focus ?? []).length ? wf.active_focus : (wf?.active_focus ? [wf.active_focus] : []);
if (!focus.length) {
  dv.paragraph("_No `active_focus` set in WORKFLOW.md — showing nothing._");
} else {
  dv.header(4, "Focus: " + focus.join(", "));
  const pages = dv.pages('"prds/knowledge/conclusions" or "prds/knowledge/sources"')
    .where(p => (p.tags ?? []).some(t => focus.includes(String(t)))
             || focus.some(f => (p.file.path ?? "").toLowerCase().includes(f.toLowerCase())));
  dv.table(["Node", "Type", "Tags", "Date"],
    pages.sort(p => p.date, "desc").limit(25)
      .map(p => [p.file.link, p.type, p.tags, p.date]));
}
```

## KB — tag cloud

```dataview
TABLE WITHOUT ID rows.file.link AS "Notes", length(rows) AS "Count"
FROM "prds/knowledge/conclusions" OR "prds/knowledge/sources"
FLATTEN tags AS tag
WHERE tag
GROUP BY tag
SORT length(rows) DESC
LIMIT 30
```