#!/usr/bin/env python3
"""pearde knowledge — the research layer, whole. One tool, no dependency.

The loop: query first; a gap enqueues or researches; a finding is remembered;
a conclusion is concluded from >=2 sources; relink holds the graph together;
the dashboard and the wiki are what a person opens.

Written for the folder this file sits beside: <repo>/.pearde/wiki/ —
sources/, conclusions/, pending/, graphs/, WORKFLOW.md, Dashboard.md — the
self-contained Obsidian vault. Every verb takes --root to run on any other
board's folder.
"""

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

# --- paths -----------------------------------------------------------------

def default_root():
    return Path(__file__).resolve().parent.parent / ".pearde" / "wiki"


class Store:
    def __init__(self, root):
        self.root = Path(root).expanduser().resolve()
        self.sources = self.root / "sources"
        self.absorbed = self.sources / ".absorbed"
        self.conclusions = self.root / "conclusions"
        self.pending = self.root / "pending"
        self.graphs = self.root / "graphs"
        self.graphify = self.root / ".graphify"
        self.graph_json = self.graphify / "graph.json"
        self.workflow_md = self.root / "WORKFLOW.md"
        self.dashboard_md = self.root / "Dashboard.md"
        self.report_md = self.root / "Dashboard.report.md"

    def ensure(self):
        for d in (self.sources, self.conclusions, self.pending,
                  self.graphs, self.graphify, self.absorbed):
            d.mkdir(parents=True, exist_ok=True)

    def workflow(self):
        """WORKFLOW.md frontmatter — the configuration, read on every call."""
        config = {
            "active_focus": [],
            "priority_tags": [],
            "auto_enqueue": True,
            "min_sources_per_conclusion": 2,
            "default_workflow": "default",
        }
        try:
            text = self.workflow_md.read_text(encoding="utf-8")
        except OSError:
            return config
        meta = parse_frontmatter(text)[0]
        for key in config:
            if key in meta:
                value = meta[key]
                if isinstance(value, list) and len(value) == 1:
                    value = value[0]
                if key != "auto_enqueue" and key != "default_workflow" \
                        and key != "min_sources_per_conclusion" \
                        and isinstance(value, str):
                    value = [v.strip() for v in value.split(",") if v.strip()]
                if isinstance(value, str) and key == "auto_enqueue":
                    value = value.strip().lower() in ("true", "yes", "1")
                if key == "min_sources_per_conclusion":
                    try:
                        value = int(value)
                    except (TypeError, ValueError):
                        value = 2
                config[key] = value
        return config


# --- frontmatter / note parsing ---------------------------------------------

FM_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")


def parse_frontmatter(text):
    """Return (dict-of-keys, body). Lists stay lists; scalars stay strings;
    list items keep their quotes stripped but nothing else is coerced."""
    match = FM_RE.match(text)
    if not match:
        return {}, text
    meta, current_key, current_list = {}, None, None
    for line in match.group(1).split("\n"):
        if not line.strip() or line.strip().startswith("#"):
            continue
        item = re.match(r"^  - \"?(.+?)\"?\s*$", line)
        if item and current_key is not None:
            current_list.append(item.group(1))
            continue
        pair = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if pair:
            key, value = pair.group(1), pair.group(2)
            if value == "":
                current_key, current_list = key, []
                meta[key] = current_list
            else:
                current_key, current_list = key, None
                if value.startswith("[") and value.endswith("]"):
                    inner = value[1:-1]
                    meta[key] = [v.strip().strip('"') for v in inner.split(",") if v.strip()] if inner.strip() else []
                else:
                    meta[key] = value.strip().strip('"')
        else:
            current_key, current_list = None, None
    return meta, text[match.end():]


class Note:
    def __init__(self, path):
        self.path = path
        self.rel = path.relative_to(Path(path.anchor)) if False else path  # set below
        raw = path.read_text(encoding="utf-8")
        self.meta, self.body = parse_frontmatter(raw)
        self.title = self.meta.get("title") or path.stem
        self.type = self.meta.get("type", "")
        self.tags = list(self.meta.get("tags", []))
        date = self.meta.get("date", "")
        try:
            self.date = dt.date.fromisoformat(str(date)[:10]) if date else None
        except ValueError:
            self.date = None


def load_notes(store, kinds=("sources", "conclusions")):
    notes = []
    bases = {"sources": store.sources, "conclusions": store.conclusions}
    for kind in kinds:
        base = bases[kind]
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            if store.absorbed in path.parents:
                continue
            if path.name == "_index.md":
                continue
            note = Note(path)
            note.kind = kind  # sources / conclusions
            notes.append(note)
    return notes


# --- ids and slugs ----------------------------------------------------------

def slugify(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:60] or "note"


def note_id(when=None):
    day = (when or dt.date.today()).strftime("%y%m%d")
    entropy = hashlib.sha1(str(dt.datetime.now(tz=dt.timezone.utc)).encode()).hexdigest()[:4]
    return f"{day}-{entropy}"


def resolve_slug(store, slug):
    """Slug or wikilink target -> Path, or None. Wikilinks are shortest-path:
    any file whose stem or title matches."""
    slug = slug.strip().strip("[[]]")
    stems = {}
    titles = {}
    for note in load_notes(store, ("sources", "conclusions")):
        stems[note.path.stem] = note.path
        titles[note.title.strip().lower()] = note.path
    return stems.get(slug) or stems.get(Path(slug).stem) \
        or titles.get(slug.lower()) or titles.get(Path(slug).stem.lower())


# --- verbs -------------------------------------------------------------------

def cmd_remember(store, args):
    store.ensure()
    config = store.workflow()
    when = dt.date.today()
    body = sys.stdin.read().strip()
    if not body:
        print("remember: body is empty — pipe the note in: echo \"...\" | knowledge.py remember <title>", file=sys.stderr)
        return 1
    slug = slugify(args.title)
    folder = store.sources
    if args.folder:
        folder = store.sources / args.folder.strip("/ ")
        if store.absorbed in folder.parents or folder == store.absorbed:
            print("remember: .absorbed is closed — files live there only by crystalize", file=sys.stderr)
            return 1
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{note_id(when)}.md"
    # id collision: shift the entropy a second forward until free
    while target.exists():
        target = folder / f"{note_id(when)}{hashlib.sha1(target.name.encode()).hexdigest()[:1]}.md"
    related = [r.strip().strip("[[]]") for chunk in (args.related or []) for r in chunk.split(",") if r.strip()]
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    tags = sorted(set(tags + ["source"]))
    lines = [
        "---",
        f"title: {args.title}",
        f"date: {when.isoformat()}",
        "type: source",
        f"tags: [{', '.join(tags)}]",
    ]
    if args.provenance:
        lines.append(f"provenance: \"{args.provenance}\"")
    if related:
        lines.append("related:")
        lines += [f"  - \"[[{r}]]\"" for r in related]
    lines += ["---", "", f"# {args.title}", "", body, ""]
    target.write_text("\n".join(lines), encoding="utf-8")
    print(f"remembered: {target.relative_to(store.root)} · [[{target.stem}]]")
    return 0


def cmd_conclude(store, args):
    store.ensure()
    config = store.workflow()
    minimum = config["min_sources_per_conclusion"]
    when = dt.date.today()
    sources = [s.strip().strip("[[]]") for s in (args.sources or "").split(",") if s.strip()]
    resolved, missing = [], []
    for slug in sources:
        path = resolve_slug(store, slug)
        (resolved if path else missing).append((slug, path))
    if missing:
        print("conclude: unresolved source link(s):", file=sys.stderr)
        for slug, _ in missing:
            print(f"  {slug}", file=sys.stderr)
        return 1
    if len(sources) < minimum:
        print(f"conclude: {len(sources)} source(s) is a hunch, not a conclusion "
              f"— min_sources_per_conclusion={minimum}", file=sys.stderr)
        return 1
    slug = slugify(args.title)
    target = store.conclusions / f"{slug}.md"
    if target.exists() and not args.force:
        print(f"conclude: {target.relative_to(store.root)} exists — new wording is an edit, "
              "a second finding is a --force or a new title", file=sys.stderr)
        return 1
    body = sys.stdin.read().strip()
    if not body:
        print("conclude: body is empty — pipe the argument in", file=sys.stderr)
        return 1
    related = [r.strip().strip("[[]]") for chunk in (args.related or []) for r in chunk.split(",") if r.strip()]
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    tags = sorted(set(tags + ["conclusion"]))
    lines = [
        "---",
        f"title: {slug}",
        f"date: {when.isoformat()}",
        "type: conclusion",
        f"tags: [{ ', '.join(tags)}]",
        "sources:",
    ] + [f"  - \"[[{p.stem}]]\"" for _, p in resolved] + ([
        "related:",
    ] + [f"  - \"[[{r}]]\"" for r in related] if related else []) + [
        "derived_from: []",
        "---",
        "",
        f"# {args.title}",
        "",
        body,
        "",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    print(f"concluded: {target.relative_to(store.root)} · [[{target.stem}]] "
          f"· {len(resolved)} source(s)")
    return 0


def cmd_enqueue(store, args):
    store.ensure()
    when = dt.date.today()
    question = " ".join(args.question).strip()
    if not question or question == '""':
        print("enqueue: empty question", file=sys.stderr)
        return 1
    dedupe_only = getattr(args, "_dedupe_only", False)
    existing = []
    if store.pending.exists():
        for path in store.pending.glob("*.md"):
            try:
                meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
            except OSError:
                continue
            if str(meta.get("question", "")).strip().lower() == question.lower():
                existing.append(path)
    if existing:
        print(f"enqueued: already pending — {existing[0].relative_to(store.root)}")
        return 0
    if dedupe_only:
        return 0
    target = store.pending / f"{note_id(when)}.md"
    lines = [
        "---",
        f"date: {when.isoformat()}",
        "type: pending",
        f"status: pending",
        f"priority: {args.priority}",
    ]
    if args.requested_by:
        lines.append(f"requested_by: \"{args.requested_by}\"")
    lines += [
        f"question: \"{question}\"",
        "---",
        "",
        f"# {question}",
        "",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    print(f"enqueued: {target.relative_to(store.root)} · priority {args.priority}")
    return 0


def score_note(note, terms, focus, priority_tags):
    score = 0
    haystacks = [(note.title.lower(), 3), (note.body.lower(), 1)]
    tag_text = " ".join(note.tags).lower()
    haystacks.append((tag_text, 2))
    for term in terms:
        for text, weight in haystacks:
            if term in text:
                score += weight
    matched_focus = [f for f in focus if f.lower() in tag_text or f.lower() in note.title.lower()]
    if matched_focus:
        score += 2 * len(matched_focus)
    matched_priority = [t for t in priority_tags if t.lower() in tag_text]
    if matched_priority:
        score += 3 * len(matched_priority)
    if note.date:
        age_days = (dt.date.today() - note.date).days
        if age_days <= 14:
            score += 1
    return score


def cmd_query(store, args):
    config = store.workflow()
    question = " ".join(args.question).strip()
    terms = [t for t in re.split(r"\W+", question.lower()) if len(t) > 2]
    notes = load_notes(store)
    scores = sorted(((score_note(n, terms, config["active_focus"], config["priority_tags"]), n)
                     for n in notes), key=lambda pair: pair[0], reverse=True)
    hits = [(s, n) for s, n in scores if s > 0]
    strong = [(s, n) for s, n in hits if s >= 4]
    print(f"query: {len(hits)} hit(s), {len(strong)} strong · {len(notes)} notes on record")
    for score, note in hits[:args.limit]:
        marker = "@" if score >= 4 else " "
        links = list(WIKILINK_RE.findall(note.body))
        print(f"  {marker} {score:>2}  [[{note.path.stem}]] {note.kind:<9} {note.title[:70]}")
        if args.verbose:
            first = next((line.strip() for line in note.body.split("\n")
                          if line.strip() and not line.startswith("#")), "")
            print(f"        {first[:100]}")
            if links:
                print(f"        links: {', '.join(links[:6])}")
    if not hits:
        print("gap: nothing on record for this question")
        if config["auto_enqueue"] and not args.no_enqueue:
            cmd_enqueue(store, argparse.Namespace(
                question=[question], priority="med", requested_by="query gap"))
        elif args.no_enqueue:
            cmd_enqueue(store, argparse.Namespace(
                question=[question], priority="med", requested_by="query gap", _dedupe_only=True))
        return 2
    if len(strong) < 1:
        print("gap: thin — hits name the topic but no note answers it")
        if config["auto_enqueue"] and not args.no_enqueue:
            cmd_enqueue(store, argparse.Namespace(
                question=[question], priority="med", requested_by="query gap"))
        elif args.no_enqueue:
            cmd_enqueue(store, argparse.Namespace(
                question=[question], priority="med", requested_by="query gap", _dedupe_only=True))
        return 2
    return 0


def build_graph(store):
    """Nodes = notes. Edges: body wikilinks (resolved), `sources:` frontmatter,
    `related:` frontmatter, symmetrized. Provenance per edge says where it
    came from. Writes .graphify/graph.json. Returns (notes, edges)."""
    notes = load_notes(store)
    by_stem = {n.path.stem: n for n in notes}
    by_title = {n.title.strip().lower(): n for n in notes}

    def resolve(link):
        link = link.strip().strip("[[]]").strip()
        return by_stem.get(link) or by_title.get(link.lower()) \
            or next((n for t, n in by_title.items()
                     if t.startswith(link.lower()) or link.lower().startswith(t)), None)

    edges = {}

    def add_edge(src, dst, kind, provenance):
        if src.path == dst.path:
            return
        key = (src.path.stem, dst.path.stem)
        if key not in edges:
            edges[key] = {"from": src.path.stem, "to": dst.path.stem,
                          "type": kind, "provenance": provenance}
        elif provenance == "frontmatter" and edges[key]["provenance"] != "frontmatter":
            edges[key]["type"] = kind if kind == "derives" else edges[key]["type"]
            edges[key]["provenance"] = provenance

    for note in notes:
        for link in WIKILINK_RE.findall(note.body):
            target = resolve(link)
            if target:
                kind = "derives" if note.kind == "conclusions" else "links"
                add_edge(note, target, kind, "wikilink")
        for key, kind in (("sources", "derives"), ("related", "related")):
            for link in note.meta.get(key, []) or []:
                target = resolve(link)
                if target:
                    add_edge(note, target, kind, "frontmatter")

    # frontmatter `related:` is a symmetric claim; the reverse edge follows
    for edge in list(edges.values()):
        if edge["type"] == "related":
            back = (edge["to"], edge["from"])
            if back not in edges:
                edges[back] = {"from": edge["to"], "from_type": None,
                               "to": edge["from"], "type": "related",
                               "provenance": "frontmatter"}

    graph = {
        "nodes": [
            {
                "id": n.path.stem,
                "title": n.title,
                "kind": n.kind,
                "type": n.type,
                "tags": n.tags,
                "date": str(n.meta.get("date", "")),
                "path": str(n.path.relative_to(store.root)),
            }
            for n in notes
        ],
        "edges": sorted(edges.values(), key=lambda e: (e["from"], e["to"])),
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "note_count": len(notes),
        "edge_count": len(edges),
    }
    return notes, list(edges.values()), graph


def cmd_relink(store, args):
    store.ensure()
    notes, edges, graph = build_graph(store)
    store.graph_json.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    # symmetrize related: frontmatter, both directions, idempotently
    for note in notes:
        wanted = sorted({e["to"] if e["from"] == note.path.stem else e["from"]
                         for e in edges
                         if e["type"] == "related"
                         and note.path.stem in (e["from"], e["to"])})
        if not wanted:
            continue
        text = note.path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        listed = [str(r).strip("[[]]") for r in meta.get("related", []) or []]
        missing = [s for s in wanted if s not in listed]
        if not missing:
            continue
        # rebuild the related block inside the frontmatter
        lines = text.split("\n")
        out, in_related, done = [], False, False
        for line in lines:
            if line.startswith("related:"):
                in_related = True
                out.append(line)
                out += [f'  - "[[{s}]]"' for s in wanted if s not in listed]
                done = True
                continue
            if in_related:
                if line.startswith("  - "):
                    continue  # drop the old entries; the wanted set replaces them
                in_related = False
            out.append(line)
        if not done:  # no related block — insert one after the frontmatter opener
            close = out.index("---", 1)
            block = ["related:"] + [f'  - "[[{s}]]"' for s in wanted]
            out = out[:close] + block + out[close:]
        note.path.write_text("\n".join(out), encoding="utf-8")
        print(f"  related: {note.path.stem} + {', '.join(missing)}")
    print(f"relink: {graph['note_count']} nodes, {graph['edge_count']} edges "
          f"-> {store.graph_json}")
    orphan_stems = set()
    for edge in edges:
        orphan_stems.add(edge["from"])
        orphan_stems.add(edge["to"])
    orphans = [n for n in notes if n.path.stem not in orphan_stems]
    if orphans:
        print(f"  orphans ({len(orphans)}): " + ", ".join(o.path.stem for o in orphans))
    return 0


def cmd_wiki(store, args):
    """graphs/ — one hub page per connected component of >= 2 notes."""
    store.ensure()
    notes, edges, graph = build_graph(store)
    adjacency = {}
    for edge in edges:
        adjacency.setdefault(edge["from"], set()).add(edge["to"])
        adjacency.setdefault(edge["to"], set()).add(edge["from"])
    seen, components = set(), []
    for node in graph["nodes"]:
        if node["id"] in seen:
            continue
        stack, component = [node["id"]], set()
        while stack:
            current = stack.pop()
            if current in component:
                continue
            component.add(current)
            stack += [m for m in adjacency.get(current, ()) if m not in component]
        seen |= component
        if len(component) >= 2:
            components.append(sorted(component))
    components.sort(key=len, reverse=True)
    for index, component in enumerate(components, 1):
        hub = max(component, key=lambda cid: len(adjacency.get(cid, ())))
        member = {n["id"]: n for n in graph["nodes"] if n["id"] in component}
        lines = [
            "---",
            f"title: community-{index}-{slugify(hub)}",
            f"date: {dt.date.today().isoformat()}",
            "type: wiki",
            "community:",
            f"  hub: \"[[{hub}]]\"",
            f"  size: {len(component)}",
            "---",
            "",
            f"# {member[hub]['title']}",
            "",
            f"{len(component)} notes travel together in this component. Hubs "
            f"first, then the rest.",
            "",
            "```dataview",
            "TABLE WITHOUT ID file.link AS Node, type, length(file.inlinks) AS In",
            f"WHERE file.path != this.file.path",
            "AND (",
        ]
        lines += [f'  file.name = "{cid}"' + (" OR" if cid != component[-1] else "")
                  for cid in component]
        lines += [")", "SORT length(file.inlinks) DESC", "```", ""]
        target_path = store.graphs / f"community-{index:02d}-{slugify(hub)}.md"
        target_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  {target_path.relative_to(store.root)} ({len(component)} notes, hub [[{hub}]])")
    # drop stale community pages
    keep = {f"community-{i:02d}-{slugify(max(c, key=lambda cid: len(adjacency.get(cid, ()))))}.md"
            for i, c in enumerate(components, 1)}
    for old in store.graphs.glob("community-*.md"):
        if old.name not in keep:
            old.unlink()
            print(f"  removed stale {old.relative_to(store.root)}")
    if not components:
        print("wiki: no component of two or more linked notes — the graph is thin")
    return 0


def cmd_board(store, args):
    """board/ — one generated note per PRD, the board as a linkable graph.

    Reads the board beside the KB (the parent of the KB folder): every
    .pearde/prds/<name>/prd.md's frontmatter (state, origin, priority, complexity,
    blast-radius, needs, from, workflow, footprint), the memos, the
    workflows. Writes <KB>/board/<slug>.md per PRD — frontmatter carries the
    state fields as Dataview fields, the body carries the wikilinks: needs,
    fed-by (the computed reverse), derived-from, children, the memos that
    mention the PRD, the workflow it runs on. Stale pages for PRDs that left
    the board are removed. Regenerable: edit prd.md, run board again.
    """
    store.ensure()
    board_root = store.root.parent                # <board> — .pearde, the KB's parent
    prds = board_root / "prds"                     # <board>/prds, the PRD tree
    vault_root = board_root.parent                 # the Obsidian vault: the repo root
    def scalar(value):
        # prd.md frontmatter carries trailing comments — "open  # open|..." —
        # so cut on the first " #", and treat the empty-list marker as empty
        text = str(value or "").split("#")[0].strip()
        return "" if text in ("[]", '""', "''") else text

    prds_found = {}          # PRD path-as-slug ("parent/child" for nested) -> fields
    for prd_file in sorted(prds.rglob("prd.md")):
        if "wiki" in prd_file.relative_to(prds).parts:
            continue
        slug = prd_file.parent.relative_to(prds).as_posix()
        entry = prd_file.parent
        meta, body = parse_frontmatter(prd_file.read_text(encoding="utf-8"))
        title = next((line[2:].strip() for line in body.split("\n")
                      if line.startswith("# ")), entry.name)
        prds_found[slug] = {
            "title": title or entry.name,
            "state": scalar(meta.get("state")),
            "origin": scalar(meta.get("origin")),
            "priority": scalar(meta.get("priority")),
            "complexity": scalar(meta.get("complexity")),
            "blast": scalar(meta.get("blast-radius")),
            "needs": [scalar(n) for n in meta.get("needs", []) or [] if scalar(n)],
            "from": scalar(meta.get("from")),
            "workflow": scalar(meta.get("workflow")),
            "footprint": [scalar(f) for f in meta.get("footprint", []) or [] if scalar(f)],
            "text": body,
        }
    memos = {}
    for memo_path in sorted((board_root / "memos").glob("*.md")):
        memo_raw = memo_path.read_text(encoding="utf-8")
        memo_meta, memo_body = parse_frontmatter(memo_raw)
        memos[memo_path.stem] = {
            "subject": str(memo_meta.get("subject", "")).strip() or memo_path.stem,
            "kind": str(memo_meta.get("kind", "")).strip(),
            "status": str(memo_meta.get("status", "")).strip(),
            "cites": [str(p).strip() for p in memo_meta.get("prds", []) or []],
            "text": memo_raw,
        }
    board_dir = store.root / "board"
    board_dir.mkdir(parents=True, exist_ok=True)
    # a memo belongs to a PRD when it names the PRD in its `prds:` frontmatter,
    # or the memo body cites the PRD dir name, or the PRD body cites the memo slug
    memo_hits_by_prd = {}
    for name, prd in prds_found.items():
        leaf = name.split("/")[-1]
        memo_hits_by_prd[name] = sorted(
            slug for slug, memo in memos.items()
            if leaf in memo["cites"] or leaf in memo["text"]
            or slug in prd["text"])
    flat = {name.split("/")[-1]: f".pearde/wiki/board/{name}"
            for name in prds_found}
    written, removed = [], []
    for name, prd in prds_found.items():
        name_parts = (name, name.split("/")[-1])
        fed_by = sorted(other for other, p in prds_found.items()
                        if any(part in p["needs"] for part in name_parts)
                        or any(other == n.split("/")[0] and n.split("/")[-1] == name.split("/")[-1]
                               for n in p["needs"]))
        children = sorted(other for other, p in prds_found.items()
                          if p["from"] in name_parts)
        lines = [
            "---",
            f"title: {name}",
            "type: prd",
            f"state: {prd['state'] or 'unknown'}",
            f"origin: {prd['origin'] or 'requested'}",
            f"priority: {prd['priority'] or 0}",
            f"complexity: {prd['complexity'] or 0}",
            f"blast: {prd['blast'] or 'low'}",
        ]
        if prd["from"]:
            lines.append(f'from: "[[{flat.get(prd["from"], prd["from"])}]]"')
        if prd["needs"]:
            lines.append("needs:")
            for n in prd["needs"]:
                lines.append(f'  - "[[{flat.get(n, n)}]]"')
        if prd["workflow"]:
            lines.append(f'workflow: "[[{prd["workflow"]}]]"')
        lines += [
            "---", "",
            f"# {prd['title']}", "",
            f"`state: {prd['state'] or 'unknown'} · origin: {prd['origin'] or 'requested'}"
            f" · priority {prd['priority'] or 0} · complexity {prd['complexity'] or 0}"
            f" · blast {prd['blast'] or '—'}`", "",
        ]
        if fed_by:
            lines += ["## Fed by (needs this one)", ""]
            lines += [f"- [[{flat.get(n, n)}]]" for n in fed_by] + [""]
        if prd["needs"]:
            lines += ["## Needs (gates this one behind)", ""]
            lines += [f"- [[{flat.get(n, n)}]]" for n in prd["needs"]] + [""]
        if prd["from"]:
            lines += [f"Derived from [[{flat.get(prd['from'], prd['from'])}]].", ""]
        if children:
            lines += ["## Children (derived from this)", ""]
            lines += [f"- [[{flat.get(c, c)}]]" for c in children] + [""]
        if prd["workflow"]:
            lines += [f"Runs on: [[{prd['workflow']}]]", ""]
        if prd["footprint"]:
            lines += ["## Footprint", ""]
            lines += [f"- `{f}`" for f in prd["footprint"]] + [""]
        specs = sorted(((prd_dir / "specs").glob("spec*.md"))
                       if (prd_dir := prds / name).exists() else [])
        if specs:
            lines += ["## Specs", ""]
            # [[folder/spec]] — the full path resolves the spec file in the vault
            lines += [f"- [[{s.relative_to(vault_root).with_suffix('')}]]"
                      for s in specs] + [""]
        if memo_hits_by_prd[name]:
            lines += ["## Decisions", ""]
            lines += [f"- [[{slug}]] — {memos[slug]['subject']}"
                      for slug in memo_hits_by_prd[name]] + [""]
        # the knowledge under the decisions: conclusions the citing memos stand on
        conclusions = sorted({link
                              for slug in memo_hits_by_prd[name]
                              for link in WIKILINK_RE.findall(memos[slug]["text"])
                              if link.strip() and not link.strip().startswith("#")})
        if conclusions:
            lines += ["## Knowledge", ""]
            lines += [f"- [[{c}]]" for c in conclusions] + [""]
        target = board_dir / f"{name}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(lines), encoding="utf-8")
        written.append(name)
    for old in sorted(board_dir.rglob("*.md")):
        if old.relative_to(board_dir).as_posix()[:-3] not in prds_found:
            old.unlink()
            removed.append(old.stem)
    print(f"board: {len(written)} PRD note(s), {len(memos)} memos scanned"
          + (f" · {len(removed)} stale removed" if removed else ""))
    return 0


def memo_text(prds, slug):
    try:
        return (prds / "memos" / f"{slug}.md").read_text(encoding="utf-8")
    except OSError:
        return ""


def cmd_dashboard(store, args):
    """Rewrite Dashboard.md's numbers only — a human edits the queries; this
    prints the plain report. --write regenerates the report file."""
    notes, edges, graph = build_graph(store)
    today = dt.date.today()
    conclusions = [n for n in notes if n.kind == "conclusions"]
    sources = [n for n in notes if n.kind == "sources"]
    pending = []
    for path in sorted(store.pending.glob("*.md")):
        meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        pending.append((path, meta))
    in_edges = {}
    out_edges = {}
    for edge in edges:
        out_edges.setdefault(edge["from"], 0)
        out_edges[edge["from"]] += 1
        in_edges.setdefault(edge["to"], 0)
        in_edges[edge["to"]] += 1
    cited = {e["to"] for e in edges if e["type"] in ("derives", "links")}
    uncited = [n for n in sources if n.path.stem not in cited]
    orphans = [n for n in notes
               if n.path.stem not in in_edges and n.path.stem not in out_edges]
    hubs = sorted(in_edges.items(), key=lambda pair: pair[1], reverse=True)[:8]

    def line(name, value):
        return f"{name}: {value}"

    out = [
        f"# Knowledge report — {today.isoformat()}",
        "",
        line("notes on record", f"{len(notes)} ({len(conclusions)} conclusions, {len(sources)} sources)"),
        line("edges", f"{graph['edge_count']} ({len([e for e in edges if e['type'] == 'derives'])} derive from sources)"),
        line("pending queue", f"{len(pending)} question(s)" + (
            ", priorities: " + ", ".join(f"{m.get('priority', '?')}" for _, m in pending) if pending else "")),
    ]
    if hubs:
        out += ["", "## Hubs (most referenced)", ""]
        out += [f"- [[{stem} — {count} inbound" for stem, count in hubs]
    if orphans:
        out += ["", "## Orphans (no edges in either direction)", ""]
        out += [f"- [[{n.path.stem}]] — {n.title}" for n in orphans]
    if uncited:
        out += ["", "## Sources no conclusion stands on yet", ""]
        out += [f"- [[{n.path.stem}]] — {n.title}" for n in uncited]
    out += ["", "The live views are in the vault: open the folder in Obsidian, "
            "or read Dashboard.md's Dataview blocks."]
    report = "\n".join(out) + "\n"
    print(report)
    if args.write:
        store.report_md.write_text(report, encoding="utf-8")
        print(f"written: {store.report_md.relative_to(store.root)}")
    return 0


def cmd_doctor(store, args):
    problems = []
    config = store.workflow()
    if not store.workflow_md.exists():
        problems.append("WORKFLOW.md missing — the loop has no configuration")
    notes = load_notes(store)
    stems = set()
    for note in notes:
        stems.add(note.path.stem)
        if not note.meta:
            problems.append(f"{note.path.name}: no frontmatter")
        if note.kind == "conclusions":
            n_sources = len(note.meta.get("sources", []) or [])
            if n_sources < config["min_sources_per_conclusion"]:
                problems.append(f"{note.path.name}: {n_sources} source(s) — below "
                                f"min_sources_per_conclusion={config['min_sources_per_conclusion']}")
            if "derived_from" not in note.meta:
                problems.append(f"{note.path.name}: conclusion without derived_from:")
    # resolve every wikilink in every body
    titles = {n.title.strip().lower() for n in notes}
    stems = set()
    for note in notes:
        stems.add(note.path.stem)
    for note in notes:
        for link in WIKILINK_RE.findall(note.body + " " + " ".join(
                str(v) for v in (note.meta.get("related", []) or []) +
                (note.meta.get("sources", []) or []))):
            link = link.strip().strip("[[]]").strip()
            if link in stems:
                continue
            low = link.lower()
            if low in titles or any(t.startswith(low) or low.startswith(t) for t in titles):
                continue
            problems.append(f"{note.path.name}: unresolved wikilink [[{link}]]")
    if store.graph_json.exists():
        try:
            graph = json.loads(store.graph_json.read_text(encoding="utf-8"))
            disk = {n.path.stem for n in notes}
            graph_ids = {n["id"] for n in graph.get("nodes", [])}
            if graph_ids != disk:
                stale = (graph_ids - disk) | (disk - graph_ids)
                problems.append("graph.json is behind the files: " + ", ".join(sorted(stale)[:6]))
        except (OSError, json.JSONDecodeError) as error:
            problems.append(f"graph.json unreadable: {error}")
    else:
        problems.append("graph.json missing — run relink")
    stale_pending = []
    for path in store.pending.glob("*.md"):
        meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        date = str(meta.get("date", ""))[:10]
        try:
            age = (dt.date.today() - dt.date.fromisoformat(date)).days
            if age > 30:
                stale_pending.append(f"{path.name}: pending {age} days — a question enqueued "
                                     "and never needed again is deleted, not drained")
        except ValueError:
            pass
    problems += stale_pending
    if problems:
        for problem in problems:
            print(f"  ✗ {problem}")
        print(f"doctor: {len(problems)} problem(s)")
        return 1
    print(f"doctor: clean — {len(notes)} notes, graph in sync, pending honest")
    return 0


# --- CLI ----------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="knowledge.py",
        description="pearde knowledge — the research layer, whole.",
        epilog="The loop: query · enqueue · remember · conclude · relink · dashboard · doctor.",
    )
    parser.add_argument("--root", help="KB folder (default: <repo>/.pearde/wiki)")
    sub = parser.add_subparsers(dest="verb")

    p = sub.add_parser("remember", help="capture a finding as a source note (body on stdin)")
    p.add_argument("title")
    p.add_argument("--folder", help="subfolder of sources/ (e.g. scout)")
    p.add_argument("--tags", help="comma-separated")
    p.add_argument("--related", nargs="*", help="slugs, space- or comma-separated")
    p.add_argument("--provenance", help="where the finding came from — sweep, URL, route id")

    p = sub.add_parser("conclude", help="write a conclusion from >=2 sources (body on stdin)")
    p.add_argument("title")
    p.add_argument("--sources", required=True, help="comma-separated source slugs")
    p.add_argument("--tags", help="comma-separated")
    p.add_argument("--related", nargs="*", help="slugs, space- or comma-separated")
    p.add_argument("--force", action="store_true", help="overwrite an existing conclusion")

    p = sub.add_parser("enqueue", help="queue a research question")
    p.add_argument("question", nargs="+")
    p.add_argument("--priority", default="med", choices=["low", "med", "high"])
    p.add_argument("--requested-by", dest="requested_by")

    p = sub.add_parser("query", help="ask the KB; prints the gap when the answer is not on record")
    p.add_argument("question", nargs="+")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--no-enqueue", action="store_true",
                   help="report the gap without auto-enqueuing it")

    p = sub.add_parser("relink", help="rebuild the link graph (.graphify/graph.json), symmetrize related:")
    p = sub.add_parser("board", help="regenerate board/ — one linkable note per PRD with its needs, fed-by, memos")
    p = sub.add_parser("wiki", help="regenerate graphs/ community pages from the graph")
    p = sub.add_parser("dashboard", help="print the plain report; --write saves Dashboard.report.md")
    p.add_argument("--write", action="store_true")
    p = sub.add_parser("doctor", help="frontmatter, wikilinks, graph sync, pending age")

    args = parser.parse_args(argv)
    if not args.verb:
        parser.print_help()
        return 0
    store = Store(args.root or default_root())
    verbs = {
        "remember": cmd_remember,
        "conclude": cmd_conclude,
        "enqueue": cmd_enqueue,
        "query": cmd_query,
        "relink": cmd_relink,
        "board": cmd_board,
        "wiki": cmd_wiki,
        "dashboard": cmd_dashboard,
        "doctor": cmd_doctor,
    }
    return verbs[args.verb](store, args)


if __name__ == "__main__":
    sys.exit(main())