#!/usr/bin/env python3
"""pearde gantt — the plan as distance to the vision, not as a calendar.

One self-contained HTML file: `plan.py gantt` writes it to `prds/.gantt.html`
from the schedule `plan` saved in `.plan.json`, and the live service
serves the same render at `/board/<name>`.

**Why the x axis is not time.** The workers are agents. They start when the
work is dispatchable and there are as many of them as the board can usefully
run, so a calendar date on a bar is a guess about staffing, not a fact about
the plan. What is a fact is the dependency structure: how much work has to
finish, in sequence, before the vision is reached. That is the axis — hours
along the critical path, zero at *now*, and the right edge is the vision.

Read off it directly:

  · **critical** bars are the ones that set the finish. Shorten one and the
    vision moves left; shorten anything else and nothing happens
  · **float** is drawn as a tail: how late a task may start before it becomes
    critical. A long tail is slack you can spend
  · **ready now** is the frontier at x=0 — everything dispatchable this second,
    ordered by how much work each one unblocks. That ordering IS the dispatch
    order for the fastest path to the vision
  · **wave bands** across the top are the plan's rounds, so the structure of
    the plan is the structure of the axis

`dates` mode is still one click away for a human who wants a calendar — it
draws the same bars on the worker-limited schedule `plan` computed.

The critical-path arithmetic happens here, in Python (`cpm`), so the numbers
the page draws and the numbers an agent reads out of it are the same numbers.
plan.py builds the payload (it owns the scan, the map, and the settings); this
module enriches it, renders it, and writes it.
"""
import json
import os

VIEW_FILE = ".view.html"


def cpm(tasks):
    """Critical-path method over the plan's dependency graph, in est-hours.

    Forward pass with no worker limit — the question is not "when will three
    workers get to it" but "how soon could this possibly be reached", which
    is the only bound agents cannot argue with. Backward pass from the finish
    gives every task its float. Returns (tasks, meta); tasks gain:

        es ef      earliest start / finish, hours from now
        ls lf      latest start / finish that still hits the finish
        slack      ls - es. 0 means critical
        critical   on a longest chain
        ready      dispatchable now — starts at zero: no dependency and no
                   earlier wave in front of it
        unblocks   est-hours of work waiting downstream, transitively. The
                   frontier sorts by this: it is the size of the door the
                   task opens
        downstream how many PRDs those hours are

    A `needs` naming a PRD outside the plan (done, parked, never scheduled) is
    already satisfied and drops out — `plan` resolved it, the graph only holds
    what is left to do."""
    by = {t["rel"]: t for t in tasks}
    deps = {r: [d for d in (t.get("needs") or []) if d in by and d != r]
            for r, t in by.items()}
    feeds = {r: [] for r in by}
    for r, ds in deps.items():
        for d in ds:
            feeds[d].append(r)

    # topological order (Kahn). A cycle is the planner's error, not ours: the
    # leftovers go last in a stable order rather than hanging the render.
    indeg = {r: len(deps[r]) for r in by}
    queue = sorted(r for r in by if not indeg[r])
    order = []
    while queue:
        r = queue.pop(0)
        order.append(r)
        for s in sorted(feeds[r]):
            indeg[s] -= 1
            if not indeg[s]:
                queue.append(s)
    order += sorted(r for r in by if r not in set(order))

    est = {r: float(by[r].get("est") or 0.0) for r in by}
    # The wave is a constraint, not a label. `plan` bumps a PRD into a later
    # wave when its footprint clashes with an earlier one — two agents editing
    # one file is not a schedule, it is a merge conflict — so a wave runs after
    # the one before it even where no `needs` says so. Dependencies alone would
    # draw every ready PRD starting at zero and call it the fastest path; it
    # is not a path anyone can walk.
    waves = sorted({t.get("wave") for t in tasks if t.get("wave")})
    floor = {w: 0.0 for w in waves}
    es, ef = {}, {}
    for w in waves:
        for r in order:
            if by[r].get("wave") != w:
                continue
            es[r] = max([ef.get(d, 0.0) for d in deps[r]] + [floor[w]])
            ef[r] = es[r] + est[r]
        nxt = [x for x in waves if x > w]
        if nxt:
            done = max([ef[r] for r in by if by[r].get("wave") == w] or [floor[w]])
            floor[nxt[0]] = max(floor[nxt[0]], done)
    for r in order:                      # a PRD the plan left unwaved
        if r not in es:
            es[r] = max([ef.get(d, 0.0) for d in deps[r]] or [0.0])
            ef[r] = es[r] + est[r]
    length = max(ef.values()) if ef else 0.0

    # the same wave gate, read backwards: a task may not slide past the start
    # of the earliest task in the next wave, or it would push that wave
    ceil = {}
    for i, w in enumerate(waves):
        nxt = waves[i + 1] if i + 1 < len(waves) else None
        ceil[w] = (min([es[r] for r in by if by[r].get("wave") == nxt] or [length])
                   if nxt else length)
    ls, lf = {}, {}
    for r in reversed(order):
        lf[r] = min([ls[s] for s in feeds[r] if s in ls] or
                    [ceil.get(by[r].get("wave"), length)])
        ls[r] = lf[r] - est[r]

    # transitive downstream, accumulated backwards so nothing is walked twice
    down = {}
    for r in reversed(order):
        acc = set()
        for s in feeds[r]:
            acc.add(s)
            acc |= down.get(s, set())
        down[r] = acc

    for r, t in by.items():
        t["es"], t["ef"] = round(es[r], 3), round(ef[r], 3)
        t["ls"], t["lf"] = round(ls[r], 3), round(lf[r], 3)
        t["slack"] = round(ls[r] - es[r], 3)
        t["critical"] = t["slack"] < 0.01
        t["ready"] = es[r] < 0.01
        t["unblocks"] = round(sum(est[s] for s in down[r]), 2)
        t["downstream"] = len(down[r])
        t["blocks"] = sorted(feeds[r])

    # the chain itself, for the header and for anyone reading the file
    chain, cur = [], None
    pool = [r for r in order if by[r]["critical"]]
    for r in sorted(pool, key=lambda r: (es[r], -est[r])):
        if cur is None or es[r] >= round(ef[cur], 3) - 0.01:
            chain.append(r)
            cur = r
    # how many agents the fastest path asks for at its widest moment. The
    # answer to "can we go faster" is usually this number, not an estimate.
    edges = sorted([(es[r], 1) for r in by] + [(ef[r], -1) for r in by])
    peak = run = 0
    for _, d in edges:
        run += d
        peak = max(peak, run)
    meta = {
        "length": round(length, 2),
        "total": round(sum(est.values()), 2),
        "peak": peak,
        "chain": chain,
        "ready": sorted((r for r in by if by[r]["ready"]),
                        key=lambda r: (-by[r]["unblocks"], -by[r]["prio"], r)),
        "waves": {},
    }
    for r, t in by.items():
        w = t.get("wave")
        if w is None:
            continue
        lo, hi = meta["waves"].get(str(w), (es[r], ef[r]))
        meta["waves"][str(w)] = (min(lo, es[r]), max(hi, ef[r]))
    meta["waves"] = {k: [round(v[0], 3), round(v[1], 3)]
                     for k, v in sorted(meta["waves"].items(),
                                        key=lambda kv: int(kv[0]))}
    return tasks, meta


def enrich(payload):
    p = dict(payload)
    p["tasks"], p["cpm"] = cpm([dict(t) for t in payload.get("tasks", [])])
    return p


def render(payload):
    p = enrich(payload)
    data = json.dumps(p, sort_keys=True).replace("</", "<\\/")
    return (TEMPLATE
            .replace("__TITLE__", p.get("vision", {}).get("title") or p["board"])
            .replace("__PAYLOAD__", data))


def write(board, payload):
    path = os.path.join(board, VIEW_FILE)
    with open(path, "w", encoding="utf-8") as f:
        f.write(render(payload))
    return path


# The chart follows the board's data-viz conventions: state-as-progress is an
# ordinal one-hue ramp (open → analyzing → specced → claimed, light→dark on a
# light surface, mirrored for dark), exception states wear the reserved status
# colors (question=warning, blocked=serious, failed=critical), and every row
# names its state in text so color never carries identity alone. Two hues are
# reserved and used by nothing else: magenta for the vision edge, and the
# critical chain's own outline.
TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ — plan</title>
<style>
:root{
  color-scheme:light;
  --page:#f9f9f7; --surface:#fcfcfb; --sunk:#f2f1ec;
  --ink:#0b0b0b; --ink2:#52514e; --muted:#898781;
  --grid:#e6e5de; --gridw:#d5d4cb; --axis:#c3c2b7;
  --border:rgba(11,11,11,.11); --wash:rgba(11,11,11,.028);
  --hover:rgba(11,11,11,.045); --sel:rgba(57,135,229,.10);
  --st-open:#86b6ef; --st-analyzing:#3987e5; --st-specced:#1c5cab;
  --st-claimed:#104281; --st-question:#fab219; --st-blocked:#ec835a;
  --st-failed:#d03b3b; --now:#d55181; --roll:#b9b7ad; --link:#8f8d85;
  --crit:#c2410c; --float:rgba(11,11,11,.12);
  --c1:#2a78d6; --c2:#eb6834; --c3:#1baf7a; --c4:#eda100; --c5:#e87ba4;
}
@media (prefers-color-scheme: dark){
  :root:where(:not([data-theme="light"])){
    color-scheme:dark;
    --page:#0d0d0d; --surface:#1a1a19; --sunk:#131312;
    --ink:#ffffff; --ink2:#c3c2b7; --muted:#898781;
    --grid:#262625; --gridw:#333331; --axis:#3d3d3a;
    --border:rgba(255,255,255,.11); --wash:rgba(255,255,255,.03);
    --hover:rgba(255,255,255,.055); --sel:rgba(90,150,230,.16);
    --st-open:#184f95; --st-analyzing:#2a78d6; --st-specced:#5598e7;
    --st-claimed:#9ec5f4; --now:#e87ba4; --roll:#4a4a46; --link:#6c6a63;
    --crit:#fb923c; --float:rgba(255,255,255,.14);
    --c1:#3987e5; --c2:#d95926; --c3:#199e70; --c4:#c98500; --c5:#d55181;
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --page:#0d0d0d; --surface:#1a1a19; --sunk:#131312;
  --ink:#ffffff; --ink2:#c3c2b7; --muted:#898781;
  --grid:#262625; --gridw:#333331; --axis:#3d3d3a;
  --border:rgba(255,255,255,.11); --wash:rgba(255,255,255,.03);
  --hover:rgba(255,255,255,.055); --sel:rgba(90,150,230,.16);
  --st-open:#184f95; --st-analyzing:#2a78d6; --st-specced:#5598e7;
  --st-claimed:#9ec5f4; --now:#e87ba4; --roll:#4a4a46; --link:#6c6a63;
  --crit:#fb923c; --float:rgba(255,255,255,.14);
  --c1:#3987e5; --c2:#d95926; --c3:#199e70; --c4:#c98500; --c5:#d55181;
}
*{box-sizing:border-box;margin:0}
body{background:var(--page);color:var(--ink);
  font:13px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;padding:12px}
header{display:flex;flex-wrap:wrap;gap:4px 16px;align-items:baseline;
  padding:0 2px 6px}
header h1{font-size:15px;font-weight:650;letter-spacing:-.01em}
header h1 small{color:var(--muted);font-weight:400;margin-left:6px}
#stats{color:var(--ink2);font-size:12px}
#stats b{font-weight:600;color:var(--ink)}
#stats .crit{color:var(--crit);font-weight:600}
.spacer{margin-left:auto}
#purpose{color:var(--muted);font-size:11.5px;padding:0 2px 8px;
  max-width:min(100%,980px)}

/* the frontier — what an agent should pick up, in order */
#front{display:flex;gap:6px;flex-wrap:wrap;align-items:center;
  padding:6px 8px;margin:0 0 8px;background:var(--sunk);
  border:1px solid var(--border);border-radius:8px;font-size:11.5px}
#front .h{color:var(--muted);font-weight:600;margin-right:2px}
#front .p{background:var(--surface);border:1px solid var(--border);
  border-radius:99px;padding:1px 9px;cursor:pointer;white-space:nowrap}
#front .p:hover{border-color:var(--axis)}
#front .p b{font-weight:600}
#front .p.crit{border-color:var(--crit);color:var(--crit)}
#front .p em{color:var(--muted);font-style:normal}

.bar-controls{display:flex;flex-wrap:wrap;gap:6px;align-items:center;
  padding:0 2px 8px}
button,select,input[type=search]{background:var(--surface);color:var(--ink2);
  border:1px solid var(--border);border-radius:6px;padding:3px 8px;
  font:12px system-ui,sans-serif;cursor:pointer}
button:hover,select:hover{color:var(--ink);border-color:var(--axis)}
button.on{background:var(--sel);color:var(--ink);border-color:var(--axis)}
input[type=search]{cursor:text;min-width:140px}
.seg{display:flex;gap:0}
.seg button{border-radius:0;margin-left:-1px}
.seg button:first-child{border-radius:6px 0 0 6px;margin-left:0}
.seg button:last-child{border-radius:0 6px 6px 0}
label.lab{color:var(--muted);font-size:11.5px}

#mini{position:relative;height:38px;border:1px solid var(--border);
  border-radius:7px 7px 0 0;border-bottom:none;background:var(--sunk);
  overflow:hidden;cursor:crosshair}
#mini .t{position:absolute;height:2px;border-radius:1px;opacity:.85}
#mini .t.crit{height:3px;background:var(--crit) !important;opacity:1}
#mini .edge{position:absolute;top:0;bottom:0;width:1px;background:var(--now)}
#mini .win{position:absolute;top:0;bottom:0;background:rgba(57,135,229,.13);
  border-left:1px solid var(--st-analyzing);
  border-right:1px solid var(--st-analyzing);cursor:grab}

#frame{position:relative;border:1px solid var(--border);
  border-radius:0 0 8px 8px;background:var(--surface);overflow:hidden}
#wrap{overflow:auto;max-height:calc(100vh - 300px);min-height:240px;
  overscroll-behavior-x:contain}
#canvas{position:relative}
#head{position:sticky;top:0;z-index:6;height:38px;background:var(--surface);
  border-bottom:1px solid var(--gridw)}
#corner{position:sticky;left:0;z-index:7;height:100%;background:var(--surface);
  border-right:1px solid var(--gridw);display:flex;align-items:center;
  gap:6px;padding:0 8px;font-size:11px;color:var(--muted)}
#axis{position:absolute;top:0;left:0;right:0;height:100%}
#axis .band{position:absolute;top:2px;height:15px;border-radius:3px;
  background:var(--wash);border:1px solid var(--grid);font-size:10px;
  color:var(--ink2);padding:0 5px;line-height:13px;overflow:hidden;
  white-space:nowrap}
#axis .m{position:absolute;top:3px;font-size:10.5px;font-weight:600;
  color:var(--ink2);border-left:1px solid var(--axis);padding-left:5px;
  height:13px;white-space:nowrap}
#axis .d{position:absolute;top:21px;font-size:10px;color:var(--muted);
  font-variant-numeric:tabular-nums;white-space:nowrap}
#grid{position:absolute;top:38px;left:0;bottom:0;right:0;z-index:0}
#grid .v{position:absolute;top:0;bottom:0;width:1px;background:var(--grid)}
#grid .v.w{background:var(--gridw)}
#grid .we{position:absolute;top:0;bottom:0;background:var(--wash)}
#links{position:absolute;top:38px;left:0;z-index:4;pointer-events:none;
  overflow:visible}
#now,#vision{position:absolute;top:0;bottom:0;width:2px;z-index:2;
  pointer-events:none}
#now{background:var(--now)}
#vision{background:var(--now);opacity:.85}
#nowtag,#vistag{position:absolute;top:2px;z-index:8;background:var(--surface);
  border:1px solid var(--now);border-radius:4px;padding:0 5px;font-size:10px;
  color:var(--ink);white-space:nowrap;pointer-events:none;line-height:14px}
#nowtag{transform:translateX(-50%)}
#vistag{transform:translateX(-100%);top:20px}

#rows{position:relative;z-index:1}
.row{position:relative;height:23px;white-space:nowrap}
.row:hover{background:var(--hover)}
.row.sel{background:var(--sel)}
.row.dim{opacity:.3}
.cell{position:sticky;left:0;z-index:3;display:inline-flex;align-items:center;
  gap:6px;height:100%;padding:0 8px;background:var(--surface);
  border-right:1px solid var(--gridw);font-size:11.5px;overflow:hidden}
.row:hover .cell{background:color-mix(in srgb,var(--surface) 88%,var(--ink))}
.row.sel .cell{background:color-mix(in srgb,var(--surface) 84%,var(--st-analyzing))}
.cell .n{overflow:hidden;text-overflow:ellipsis;font-weight:520}
.cell .meta{color:var(--muted);font-variant-numeric:tabular-nums;flex:none;
  margin-left:auto;padding-left:8px}
.cell .chip{flex:none;font-size:10px;color:var(--ink2);background:var(--sunk);
  border:1px solid var(--border);border-radius:3px;padding:0 4px}
.cell i{flex:none;width:8px;height:8px;border-radius:2px;
  border:1px solid var(--border)}
.cell i.hollow{background:transparent !important;
  border:1.5px solid var(--st-open)}
.cell .star{flex:none;color:var(--crit);font-size:10px}
.grp .cell{background:var(--sunk);font-weight:600}
.grp .tw{flex:none;width:12px;color:var(--muted);cursor:pointer;
  font-size:10px;text-align:center}
.bar{position:absolute;top:5px;height:13px;border-radius:3px;min-width:5px;
  border:1px solid var(--border);z-index:1}
.bar.hollow{background:transparent !important;border:1.5px solid var(--st-open)}
.bar.crit{outline:1.5px solid var(--crit);outline-offset:1px}
.float{position:absolute;top:11px;height:1px;background:var(--float);
  border-radius:1px;z-index:0;opacity:.7}
.row:hover .float,.row.sel .float{height:3px;top:10px;opacity:1}
.bar.roll{top:8px;height:7px;border-radius:2px;background:var(--roll);
  border:none;opacity:.85}

#empty{position:absolute;inset:38px 0 0 0;display:none;align-items:center;
  justify-content:center;color:var(--muted);font-size:12.5px;z-index:5;
  pointer-events:none}
/* the view switcher: four ways to read one board */
#views{display:flex;gap:0;margin:0 2px 8px}
#views button{border-radius:0;margin-left:-1px;padding:4px 12px}
#views button:first-child{border-radius:6px 0 0 6px;margin-left:0}
#views button:last-child{border-radius:0 6px 6px 0}
section[data-view]{display:none}
section[data-view].on{display:block}

/* board */
#board{display:flex;gap:8px;overflow-x:auto;padding-bottom:6px;
  align-items:flex-start}
.col{flex:0 0 232px;background:var(--sunk);border:1px solid var(--border);
  border-radius:8px;display:flex;flex-direction:column;max-height:calc(100vh - 230px)}
.col.over{border-color:var(--st-analyzing);background:var(--sel)}
.col h3{font-size:11.5px;font-weight:600;padding:7px 9px;display:flex;
  align-items:center;gap:6px;border-bottom:1px solid var(--border)}
.col h3 i{width:8px;height:8px;border-radius:2px;flex:none;
  border:1px solid var(--border)}
.col h3 .n{margin-left:auto;color:var(--muted);font-weight:500}
.col .cards{overflow-y:auto;padding:6px;display:flex;flex-direction:column;
  gap:5px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:6px;
  padding:6px 8px;font-size:11.5px;cursor:grab;line-height:1.35}
.card:hover{border-color:var(--axis)}
.card.drag{opacity:.4}
.card .t{font-weight:550;overflow:hidden;text-overflow:ellipsis;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.card .m{color:var(--muted);margin-top:3px;display:flex;gap:6px;
  font-variant-numeric:tabular-nums}
.card .m .chip{background:var(--sunk);border:1px solid var(--border);
  border-radius:3px;padding:0 4px}
.card .star{color:var(--crit)}

/* list */
#listbar{display:flex;gap:8px;align-items:center;margin:0 2px 8px}
#listbar .n{color:var(--muted);font-size:11.5px}
#list table{width:100%}
#list thead th{position:sticky;top:0;background:var(--page);z-index:2;
  box-shadow:0 1px 0 var(--grid)}
#list th{cursor:pointer;user-select:none;white-space:nowrap}
#list th.by{color:var(--ink)}
#list tr.r{cursor:pointer}
#list tr.r:hover td{background:var(--hover)}
#list td i{display:inline-block;width:8px;height:8px;border-radius:2px;
  margin-right:5px;border:1px solid var(--border)}

/* analytics */
#tiles{display:grid;gap:8px;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  margin-bottom:10px}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:8px;
  padding:9px 11px}
.tile .k{font-size:11px;color:var(--muted)}
.tile .v{font-size:22px;font-weight:650;letter-spacing:-.02em;
  font-variant-numeric:tabular-nums;line-height:1.2}
.tile .s{font-size:11px;color:var(--ink2)}
#charts{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(340px,1fr))}
.chart{background:var(--surface);border:1px solid var(--border);border-radius:8px;
  padding:10px 12px 12px}
.chart h3{font-size:12px;font-weight:600;margin-bottom:2px}
.chart p.sub{font-size:11px;color:var(--muted);margin-bottom:8px}
.chart .empty{color:var(--muted);font-size:11.5px;padding:14px 0}
.brow{display:grid;grid-template-columns:120px 1fr auto;gap:8px;
  align-items:center;font-size:11.5px;padding:1.5px 0}
.brow .lab{color:var(--ink2);overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap}
.brow .track{background:var(--wash);border-radius:4px;height:13px;
  position:relative}
.brow .fill{position:absolute;left:0;top:0;bottom:0;border-radius:4px;
  min-width:3px}
.brow .val{color:var(--ink2);font-variant-numeric:tabular-nums;
  text-align:right;min-width:64px}
.chart svg{display:block;width:100%;overflow:visible}
.chart svg .ax{stroke:var(--grid);stroke-width:1}
.chart svg .lbl{fill:var(--muted);font-size:10px}
.chart svg .dot{fill:var(--c1);stroke:var(--surface);stroke-width:2}
.chart svg .ref{stroke:var(--muted);stroke-dasharray:3 3;stroke-width:1}
.chart svg .line{fill:none;stroke:var(--c1);stroke-width:2;
  stroke-linejoin:round;stroke-linecap:round}
.chart svg .area{fill:var(--c1);opacity:.10}

.ask{border:1px solid var(--st-question);background:var(--wash);
  border-radius:7px;padding:8px 10px;margin:10px 0}
.ask h5{font-size:11px;font-weight:600;color:var(--st-question);
  margin-bottom:4px;text-transform:lowercase;letter-spacing:.04em}
.ask pre{white-space:pre-wrap;font:12px/1.5 ui-monospace,monospace;
  color:var(--ink2);margin-bottom:7px}
#drawer .say{width:100%;min-height:66px;font:12px/1.5 system-ui,sans-serif}
#drawer .row2{display:flex;gap:6px;align-items:center;margin-top:5px}
#drawer .row2 .hint{font-size:11px;color:var(--muted);margin-left:auto}
#drawer pre.sec{white-space:pre-wrap;font:11.5px/1.5 ui-monospace,monospace;
  color:var(--ink2)}
#memos{display:grid;gap:8px;grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.memo{background:var(--surface);border:1px solid var(--border);border-radius:8px;
  padding:10px 12px}
.memo h3{font-size:12.5px;font-weight:600;margin-bottom:3px}
.memo .f{font-size:11px;color:var(--muted);margin-bottom:6px}
.memo .f b{color:var(--ink2);font-weight:600}
.memo pre{white-space:pre-wrap;font:11.5px/1.5 ui-monospace,monospace;
  color:var(--ink2);max-height:230px;overflow:auto}
#newbox{position:fixed;inset:0;z-index:40;background:rgba(0,0,0,.35);
  display:none;align-items:flex-start;justify-content:center;padding-top:12vh}
#newbox.on{display:flex}
#newbox .card2{background:var(--surface);border:1px solid var(--border);
  border-radius:10px;padding:14px;width:min(560px,92vw);
  box-shadow:0 8px 30px rgba(0,0,0,.2)}
#newbox h3{font-size:13px;font-weight:600;margin-bottom:8px}
#newbox input,#newbox textarea{width:100%;background:var(--page);
  color:var(--ink);border:1px solid var(--border);border-radius:6px;
  padding:6px 8px;font:12px system-ui,sans-serif;margin-bottom:7px}
#newbox textarea{min-height:120px;font-family:ui-monospace,monospace}
#drawer{position:fixed;top:0;right:0;bottom:0;width:min(520px,46vw);z-index:30;
  background:var(--surface);border-left:1px solid var(--border);
  box-shadow:-6px 0 24px rgba(0,0,0,.13);display:none;flex-direction:column}
#drawer.open{display:flex}
#dhead{padding:10px 12px;border-bottom:1px solid var(--grid);display:flex;
  gap:8px;align-items:flex-start}
#dhead .who{flex:1;min-width:0}
#dhead .rel{font:11px ui-monospace,monospace;color:var(--muted);
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#dbody{overflow:auto;padding:10px 12px 16px;flex:1}
#drawer h4{font-size:11px;font-weight:600;color:var(--muted);margin:14px 0 5px;
  text-transform:lowercase;letter-spacing:.04em}
#drawer h4:first-child{margin-top:0}
#drawer input[type=text],#drawer textarea,#drawer select,#drawer input[type=number]{
  width:100%;background:var(--page);color:var(--ink);border:1px solid var(--border);
  border-radius:6px;padding:5px 7px;font:12px system-ui,sans-serif}
#drawer textarea{font:12px/1.5 ui-monospace,SFMono-Regular,monospace;
  resize:vertical;min-height:220px;white-space:pre}
#drawer .fields{display:grid;grid-template-columns:1fr 1fr;gap:6px}
#drawer .facts{display:flex;flex-wrap:wrap;gap:4px 10px;font-size:11.5px;
  color:var(--ink2)}
#drawer .facts b{color:var(--ink);font-weight:600}
#drawer .chips{display:flex;flex-wrap:wrap;gap:4px}
#drawer .chip2{font-size:11px;background:var(--sunk);border:1px solid var(--border);
  border-radius:99px;padding:1px 8px;cursor:pointer}
#drawer .chip2:hover{border-color:var(--axis);color:var(--ink)}
#drawer .ev{border-left:2px solid var(--st-question);padding:2px 0 2px 8px;
  margin:6px 0;font-size:11.5px;color:var(--ink2)}
#drawer .ev b{color:var(--ink)}
#drawer .spec{border:1px solid var(--border);border-radius:6px;padding:6px 8px;
  margin:5px 0;font-size:11.5px}
#drawer .spec .f{font:11px ui-monospace,monospace;color:var(--muted)}
#dsave{display:flex;gap:6px;align-items:center;padding:8px 12px;
  border-top:1px solid var(--grid)}
#dsave .msg{font-size:11.5px;color:var(--muted);margin-left:auto}
#dsave button.go{background:var(--st-analyzing);color:#fff;border-color:transparent}
#dlinks a{color:var(--st-analyzing);font-size:11.5px;text-decoration:none;
  margin-right:12px}
#dlinks a:hover{text-decoration:underline}
#tip{position:fixed;z-index:20;display:none;max-width:380px;
  background:var(--surface);border:1px solid var(--border);border-radius:7px;
  box-shadow:0 3px 14px rgba(0,0,0,.16);padding:8px 11px;font-size:11.5px}
#tip .t{font-weight:600;margin-bottom:3px}
#tip .r{color:var(--ink2)}
#tip .k{color:var(--muted)}
#legend{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:11.5px;
  color:var(--ink2);padding:8px 2px 0}
#legend i{display:inline-block;width:9px;height:9px;border-radius:2px;
  margin-right:5px;vertical-align:-1px;border:1px solid var(--border)}
#legend i.hollow{background:transparent !important;
  border:1.5px solid var(--st-open)}
#legend i.crit{background:transparent;border:1.5px solid var(--crit)}
#legend b{display:inline-block;width:9px;height:2px;background:var(--now);
  margin-right:5px;vertical-align:2px}
details{margin-top:10px;color:var(--ink2);font-size:12px}
summary{cursor:pointer;color:var(--muted)}
table{border-collapse:collapse;margin-top:8px;width:100%}
th,td{text-align:left;padding:3px 10px 3px 0;border-bottom:1px solid var(--grid);
  font-variant-numeric:tabular-nums}
th{color:var(--muted);font-weight:500;font-size:11px}
tr.crit td{color:var(--crit)}
#note{margin-top:8px;color:var(--muted);font-size:11.5px;padding:0 2px}
kbd{font:11px ui-monospace,monospace;background:var(--sunk);
  border:1px solid var(--border);border-radius:3px;padding:0 3px}
</style>
</head>
<body>
<header>
  <h1>__TITLE__<small id="sub">the plan</small></h1>
  <span id="stats"></span>
  <span class="spacer"></span>
  <span id="inview" style="color:var(--ink2);font-size:12px"></span>
</header>
<div id="purpose"></div>
<div id="front"></div>
<div id="views">
  <button data-v="timeline" class="on">timeline</button
  ><button data-v="board">board</button
  ><button data-v="list">list</button
  ><button data-v="analytics">analytics</button
  ><button data-v="memos">memos</button>
  <button id="newprd" title="write a PRD (n)" style="margin-left:8px">+ PRD</button>
</div>
<div class="bar-controls" id="tcontrols">
  <span class="seg">
    <button id="mVision" data-m="vision">vision</button
    ><button id="mDates" data-m="dates">dates</button>
  </span>
  <label class="lab" for="grp">group</label>
  <select id="grp"></select>
  <span class="seg" id="zooms"></span>
  <span class="seg">
    <button id="zo" title="zoom out (−)">−</button>
    <button id="zi" title="zoom in (+)">+</button>
  </span>
  <button id="ce" title="collapse every group">collapse all</button>
  <input type="search" id="q" placeholder="filter  /" autocomplete="off">
  <button id="onlycrit" title="only the tasks that set the finish">critical</button>
  <button id="onlyready" title="only what is dispatchable now">ready</button>
</div>
<section data-view="timeline" class="on">
<div id="mini"></div>
<div id="frame">
  <div id="wrap"><div id="canvas">
    <div id="head"><div id="axis"></div><div id="nowtag"></div>
      <div id="vistag"></div><div id="corner"></div></div>
    <div id="grid"></div>
    <svg id="links"></svg>
    <div id="now"></div><div id="vision"></div>
    <div id="rows"></div>
  </div></div>
  <div id="empty"></div>
</div>
<div id="legend"></div>
<div id="note"></div>
</section>
<section data-view="board"><div id="board"></div></section>
<section data-view="list">
  <div id="listbar"><input type="search" id="lq" placeholder="filter  /">
    <span class="n" id="lcount"></span></div>
  <div id="list"></div>
</section>
<section data-view="analytics">
  <div id="tiles"></div><div id="charts"></div>
</section>
<section data-view="memos"><div id="memos"></div></section>
<div id="newbox"><div class="card2">
  <h3>a new PRD</h3>
  <input type="text" id="ntitle" placeholder="title — what exists when this is done">
  <textarea id="nbody" placeholder="the request, for someone who knows the codebase but not this conversation"></textarea>
  <div style="display:flex;gap:6px;align-items:center">
    <input type="number" id="nprio" placeholder="priority" style="width:110px;margin:0">
    <input type="text" id="nparent" placeholder="parent (optional)" style="margin:0">
    <button id="ncreate" style="background:var(--st-analyzing);color:#fff;border-color:transparent">write it</button>
    <button id="ncancel">cancel</button>
  </div>
</div></div>
<div id="tip"></div>
<aside id="drawer">
  <div id="dhead">
    <div class="who">
      <input type="text" id="dtitle" placeholder="title">
      <div class="rel" id="drel"></div>
    </div>
    <button id="dclose" title="close (Esc)">✕</button>
  </div>
  <div id="dbody"></div>
  <div id="dsave">
    <button class="go" id="dgo">save</button>
    <button id="drevert">revert</button>
    <span class="msg" id="dmsg"></span>
  </div>
</aside>
<script>
"use strict";
const DATA = __PAYLOAD__;
const CPM = DATA.cpm;
const STATES = {
  open:      {c:"var(--st-open)",      hollow:false},
  refine:    {c:"var(--st-open)",      hollow:true},
  analyzing: {c:"var(--st-analyzing)", hollow:false},
  specced:   {c:"var(--st-specced)",   hollow:false},
  claimed:   {c:"var(--st-claimed)",   hollow:false},
  question:  {c:"var(--st-question)",  hollow:false},
  blocked:   {c:"var(--st-blocked)",   hollow:false},
  failed:    {c:"var(--st-failed)",    hollow:false},
};
const $ = id => document.getElementById(id);
const wrap = $("wrap"), canvas = $("canvas"), rowsEl = $("rows"),
      axis = $("axis"), grid = $("grid"), links = $("links"), tip = $("tip"),
      mini = $("mini");
const ROW = 23, MS = 86400000;
let LEFT = Math.min(340, Math.max(210, Math.round(innerWidth * 0.24)));

const a = DATA.anchor.split("-").map(Number);
const anchor = new Date(a[0], a[1] - 1, a[2]);
const nowDay = () => (Date.now() - anchor.getTime()) / MS;
const dayDate = d => new Date(a[0], a[1] - 1, a[2] + Math.floor(d));
const fmtD = d => dayDate(d).toLocaleDateString(undefined,
  {month:"short", day:"numeric"});
const fmtH = h => h >= 40 ? Math.round(h) + "h"
  : (Math.round(h * 10) / 10 + "h").replace(".0h", "h");
const esc = s => String(s).replace(/[&<>"]/g,
  c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

const tasks = DATA.tasks;
const byRel = new Map(tasks.map(t => [t.rel, t]));
for (const t of tasks) {
  t.deps = (t.needs || []).map(r => byRel.get(r)).filter(Boolean);
  t.feeds = (t.blocks || []).map(r => byRel.get(r)).filter(Boolean);
}

/* ── two axes, one geometry ───────────────────────────────────────────────
   vision: hours along the critical path. 0 is now, the right edge is the
   vision reached, and a bar's position is the soonest it could possibly run.
   dates:  the worker-limited calendar `plan` computed, for a human who wants
   a date. Everything downstream of MODE — grid, bars, minimap, arrows —
   reads u0/u1 and never knows which one it is drawing. */
const MODE = {
  vision: {
    u0: t => t.es, u1: t => t.ef,
    lo: 0, hi: Math.max(CPM.length, 1) * 1.02 + 1,
    unit: "h", ppu: 9, min: 0.15, max: 400,
    zooms: [["fine", 34], ["mid", 9], ["whole", 2.2]],
    fmt: v => fmtH(v),
  },
  dates: {
    u0: t => t.startDay, u1: t => t.endDay,
    lo: Math.floor(Math.min(0, nowDay(), ...tasks.map(t => t.startDay))) - 2,
    hi: Math.ceil(Math.max(nowDay(), ...tasks.map(t => t.endDay), 5)) + 3,
    unit: "d", ppu: 40, min: 2.5, max: 180,
    zooms: [["day", 46], ["week", 14], ["month", 4.5]],
    fmt: v => fmtD(v),
  },
};
let mode = "vision";
let M = MODE[mode];
let ppu = M.ppu;
const span = () => M.hi - M.lo;
const x = u => LEFT + (u - M.lo) * ppu;

const GROUPS = {
  wave:  {label:"wave",  key:t => t.wave == null ? "—" : "wave " + t.wave,
          sort:(p,q) => (parseInt(p.slice(5)) || 0) - (parseInt(q.slice(5)) || 0)},
  state: {label:"state", key:t => t.state,
          sort:(p,q) => Object.keys(STATES).indexOf(p) -
                        Object.keys(STATES).indexOf(q)},
  parent:{label:"parent", key:t => {
            const i = t.rel.lastIndexOf("/");
            return i < 0 ? "(top level)" : t.rel.slice(0, i);
          }, sort:(p,q) => p.localeCompare(q)},
  none:  {label:"nothing", key:() => "", sort:() => 0},
};
if ((DATA.boards || []).length)
  GROUPS.board = {label:"board", key:t => t.board || DATA.board,
                  sort:(p,q) => p.localeCompare(q)};
let groupBy = (DATA.boards || []).length ? "board" : "wave";
const collapsed = new Set();
let selected = null, filter = "", critOnly = false, readyOnly = false;

$("grp").innerHTML = Object.entries(GROUPS)
  .map(([k, g]) => `<option value="${k}">${g.label}</option>`).join("");
$("grp").value = groupBy;

function matches(t) {
  if (critOnly && !t.critical) return false;
  if (readyOnly && !t.ready) return false;
  if (!filter) return true;
  const f = filter.toLowerCase();
  return t.rel.toLowerCase().includes(f) || t.state.includes(f) ||
    (t.title || "").toLowerCase().includes(f) || ("wave " + t.wave) === f;
}

/* ── rows ─────────────────────────────────────────────────────────────────
   Rebuilt on grouping, filter and collapse — never on scroll. A row that
   moves under the pointer as you scroll is what makes a big chart
   unreadable, so the order is stable: group, then earliest start, then how
   much the task unblocks. */
function build() {
  rowsEl.innerHTML = "";
  const g = GROUPS[groupBy];
  const buckets = new Map();
  for (const t of tasks) {
    if (!matches(t)) continue;
    const k = g.key(t);
    if (!buckets.has(k)) buckets.set(k, []);
    buckets.get(k).push(t);
  }
  const keys = [...buckets.keys()].sort(g.sort);
  let shown = 0;
  for (const k of keys) {
    const items = buckets.get(k).sort((p, q) =>
      M.u0(p) - M.u0(q) || (q.critical - p.critical) ||
      q.unblocks - p.unblocks || q.est - p.est || p.rel.localeCompare(q.rel));
    const lo = Math.min(...items.map(M.u0)), hi = Math.max(...items.map(M.u1)),
          sum = items.reduce((s, t) => s + t.est, 0),
          ncrit = items.filter(t => t.critical).length;
    if (k !== "") {
      const open = !collapsed.has(k);
      const row = document.createElement("div");
      row.className = "grp row";
      row.innerHTML =
        `<span class="cell" style="width:${LEFT}px">` +
        `<span class="tw">${open ? "▾" : "▸"}</span>` +
        `<span class="n">${esc(k)}</span>` +
        `<span class="meta">${items.length} · ${fmtH(sum)}` +
        (ncrit ? ` · <span style="color:var(--crit)">${ncrit}★</span>` : "") +
        `</span></span>`;
      const roll = document.createElement("div");
      roll.className = "bar roll";
      roll.dataset.lo = lo; roll.dataset.hi = hi;
      row.append(roll);
      row.onclick = () => {
        collapsed.has(k) ? collapsed.delete(k) : collapsed.add(k);
        build(); place();
      };
      rowsEl.append(row);
      shown++;
      if (!open) continue;
    }
    for (const t of items) {
      const st = STATES[t.state] || STATES.open;
      const row = document.createElement("div");
      row.className = "row";
      row.innerHTML =
        `<span class="cell" style="width:${LEFT}px">` +
        `<i class="${st.hollow ? "hollow" : ""}" style="background:${
          st.hollow ? "transparent" : st.c}"></i>` +
        (t.critical ? '<span class="star" title="on the critical chain">★</span>' : "") +
        (groupBy !== "board" && t.board ? `<span class="chip">${esc(t.board)}</span>` : "") +
        `<span class="n"></span>` +
        `<span class="meta">${fmtH(t.est)}${t.unblocks ? " ▸" + fmtH(t.unblocks) : ""}</span>` +
        `</span>`;
      const n = row.querySelector(".n");
      n.textContent = t.name; n.title = t.title || t.name;
      const fl = document.createElement("div");
      fl.className = "float";
      const bar = document.createElement("div");
      bar.className = "bar" + (st.hollow ? " hollow" : "") +
        (t.critical ? " crit" : "");
      if (!st.hollow) bar.style.background = st.c;
      row.append(fl, bar);
      row.addEventListener("mousemove", e => showTip(e, t));
      row.addEventListener("mouseleave", () => tip.style.display = "none");
      row.onclick = () => { selected = t; paint(); openDrawer(t); };
      rowsEl.append(row);
      t.row = row; t.bar = bar; t.fl = fl;
      shown++;
    }
  }
  const hidden = tasks.length - tasks.filter(matches).length;
  $("inview").textContent = tasks.length + " scheduled" +
    (hidden ? ` · ${hidden} filtered out` : "") +
    (collapsed.size ? ` · ${collapsed.size} collapsed` : "");
  $("empty").style.display = shown ? "none" : "flex";
  $("empty").textContent = tasks.length
    ? "nothing matches — clear the filter" : "nothing scheduled — run plan";
  paint();
}

/* ── geometry: the only writer of x ─────────────────────────────────────── */
function niceStep(pxPerUnit, unit) {
  const want = 90 / pxPerUnit;                       // ~90px between labels
  const steps = unit === "h" ? [.5,1,2,4,8,12,24,48,96,168,336]
                             : [1,2,7,14,28,56,112];
  return steps.find(s => s >= want) || steps[steps.length - 1];
}

function place() {
  canvas.style.width = LEFT + span() * ppu + "px";
  $("corner").style.width = LEFT + "px";
  axis.innerHTML = ""; grid.innerHTML = "";
  if (mode === "vision") axisVision(); else axisDates();
  for (const t of tasks) {
    if (!t.row || !t.row.isConnected) continue;
    const s = M.u0(t), e = M.u1(t);
    const w = Math.max(5, (e - s) * ppu);
    t.bar.style.left = x(s) + "px";
    t.bar.style.width = w + "px";
    // float: how far this bar may slide right before it becomes critical.
    // Drawn only where it exists, and only in vision mode — on a calendar the
    // worker slots already spent it.
    const slack = mode === "vision" ? t.slack : 0;
    t.fl.style.display = slack > 0.05 ? "block" : "none";
    if (slack > 0.05) {
      t.fl.style.left = x(e) + "px";
      t.fl.style.width = Math.max(2, slack * ppu) + "px";
    }
  }
  for (const r of rowsEl.querySelectorAll(".bar.roll")) {
    r.style.left = x(+r.dataset.lo) + "px";
    r.style.width = Math.max(5, (+r.dataset.hi - +r.dataset.lo) * ppu) + "px";
  }
  markers();
  drawMini();
  paint();
}

function axisVision() {
  // tier 1: the plan's waves, as bands. The rounds of the plan ARE the
  // structure of this axis — nothing else about it is calendar-shaped.
  for (const [w, [lo, hi]] of Object.entries(CPM.waves || {})) {
    const el = document.createElement("div");
    el.className = "band";
    el.style.left = x(lo) + "px";
    el.style.width = Math.max(18, (hi - lo) * ppu) + "px";
    el.textContent = "wave " + w;
    el.title = `wave ${w} · ${fmtH(lo)} → ${fmtH(hi)} from now`;
    axis.append(el);
  }
  const step = niceStep(ppu, "h");
  for (let v = 0; v <= M.hi; v += step) {
    const d = document.createElement("div");
    d.className = "d"; d.style.left = x(v) + 3 + "px";
    d.textContent = v === 0 ? "now" : "+" + fmtH(v);
    axis.append(d);
    const g = document.createElement("div");
    g.className = "v" + (v % (step * 4) === 0 ? " w" : "");
    g.style.left = x(v) + "px";
    grid.append(g);
  }
}

function axisDates() {
  const everyDay = ppu >= 24, weekly = ppu >= 5;
  let m = -1;
  for (let d = Math.floor(M.lo); d <= M.hi; d++) {
    const dt = dayDate(d), dow = dt.getDay();
    if (dt.getMonth() !== m) {
      m = dt.getMonth();
      const el = document.createElement("div");
      el.className = "m"; el.style.left = x(d) + "px";
      el.textContent = dt.toLocaleDateString(undefined,
        {month:"short", year:"numeric"});
      axis.append(el);
    }
    if (everyDay || (weekly && dow === 1)) {
      const el = document.createElement("div");
      el.className = "d"; el.style.left = x(d) + 3 + "px";
      el.textContent = everyDay ? dt.getDate()
        : dt.toLocaleDateString(undefined, {month:"short", day:"numeric"});
      axis.append(el);
    }
    if (everyDay || dow === 1) {
      const v = document.createElement("div");
      v.className = "v" + (dow === 1 ? " w" : "");
      v.style.left = x(d) + "px";
      grid.append(v);
    }
    if (dow === 6) {
      const w = document.createElement("div");
      w.className = "we";
      w.style.left = x(d) + "px"; w.style.width = 2 * ppu + "px";
      grid.append(w);
    }
  }
}

function markers() {
  const nowU = mode === "vision" ? 0 : nowDay();
  $("now").style.left = x(nowU) - 1 + "px";
  $("nowtag").style.display = mode === "vision" ? "none" : "block";
  $("nowtag").style.left = x(nowU) + "px";
  $("nowtag").textContent = "now · " + new Date().toLocaleDateString(
    undefined, {weekday:"short", month:"short", day:"numeric"});
  const vis = mode === "vision" ? CPM.length
    : Math.max(...tasks.map(t => t.endDay), 0);
  $("vision").style.left = x(vis) - 1 + "px";
  $("vistag").style.left = x(vis) - 4 + "px";
  $("vistag").textContent = mode === "vision"
    ? "vision · " + fmtH(CPM.length) + " of work in front"
    : "vision · " + fmtD(vis);
}

/* ── selection: arrows for one row, never the whole web ───────────────── */
function paint() {
  links.innerHTML = "";
  for (const t of tasks) if (t.row) t.row.classList.remove("sel", "dim");
  if (!selected || !selected.row || !selected.row.isConnected) {
    links.setAttribute("width", 0); links.setAttribute("height", 0);
    return;
  }
  const kin = new Set([selected, ...selected.deps, ...selected.feeds]);
  for (const t of tasks)
    if (t.row && t.row.isConnected && !kin.has(t)) t.row.classList.add("dim");
  selected.row.classList.add("sel");
  links.setAttribute("width", canvas.clientWidth);
  links.setAttribute("height", rowsEl.offsetHeight);
  const y = t => t.row.offsetTop + ROW / 2;
  const arrow = (from, to) => {
    if (!from.row || !to.row || !from.row.isConnected || !to.row.isConnected)
      return;
    const x1 = x(M.u1(from)), y1 = y(from), x2 = x(M.u0(to)), y2 = y(to);
    const mx = Math.max(x1 + 10, x2 - 12);
    const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
    p.setAttribute("d", `M${x1} ${y1} H${mx} V${y2} H${x2 - 4}`);
    p.setAttribute("fill", "none");
    p.setAttribute("stroke", from.critical && to.critical
      ? "var(--crit)" : "var(--link)");
    p.setAttribute("stroke-width", "1.4");
    if (x2 < x1) p.setAttribute("stroke-dasharray", "3 3");
    links.append(p);
    const h = document.createElementNS("http://www.w3.org/2000/svg", "path");
    h.setAttribute("d", `M${x2 - 4} ${y2} l-5 -3.2 v6.4 z`);
    h.setAttribute("fill", from.critical && to.critical
      ? "var(--crit)" : "var(--link)");
    links.append(h);
  };
  for (const d of selected.deps) arrow(d, selected);
  for (const f of selected.feeds) arrow(selected, f);
}

function showTip(e, t) {
  const when = mode === "vision"
    ? `+${fmtH(t.es)} → +${fmtH(t.ef)} from now`
    : `${fmtD(t.startDay)} → ${fmtD(t.endDay)}`;
  tip.innerHTML =
    '<div class="t"></div><div class="r rel"></div>' +
    '<div class="r"><span class="k">state</span> ' + esc(t.state) +
    ' · <span class="k">prio</span> ' + t.prio +
    ' · <span class="k">est</span> ' + fmtH(t.est) +
    (t.wave ? ' · <span class="k">wave</span> ' + t.wave : "") +
    (t.board ? ' · <span class="k">board</span> ' + esc(t.board) : "") +
    "</div>" +
    '<div class="r">' + when + "</div>" +
    '<div class="r">' + (t.critical
      ? '<span style="color:var(--crit)">★ critical — every hour cut here ' +
        'moves the vision closer</span>'
      : '<span class="k">float</span> ' + fmtH(t.slack) +
        " before it becomes critical") + "</div>" +
    '<div class="r"><span class="k">unblocks</span> ' + fmtH(t.unblocks) +
      " across " + t.downstream + " PRD(s)" +
      (t.ready ? ' · <span class="k">ready now</span>' : "") + "</div>" +
    (t.deps.length ? '<div class="r"><span class="k">needs</span> ' +
      esc(t.deps.map(d => d.name).join(", ")) + "</div>" : "") +
    (t.feeds.length ? '<div class="r"><span class="k">blocks</span> ' +
      esc(t.feeds.map(d => d.name).join(", ")) + "</div>" : "");
  tip.querySelector(".t").textContent = t.title || t.name;
  tip.querySelector(".rel").textContent = t.rel;
  tip.style.display = "block";
  const w = tip.offsetWidth, h = tip.offsetHeight;
  tip.style.left = Math.min(e.clientX + 14, innerWidth - w - 8) + "px";
  tip.style.top = Math.min(e.clientY + 16, innerHeight - h - 8) + "px";
}

/* ── overview strip: the whole plan, always ──────────────────────────── */
function drawMini() {
  mini.innerHTML = "";
  const W = mini.clientWidth || 1;
  const mx = u => (u - M.lo) / span() * W;
  const lanes = 9, used = new Array(lanes).fill(-1e9);
  for (const t of [...tasks].sort((p, q) => M.u0(p) - M.u0(q))) {
    const l0 = mx(M.u0(t)), l1 = Math.max(l0 + 2, mx(M.u1(t)));
    let lane = used.findIndex(u => u < l0 - 1);
    if (lane < 0) lane = lanes - 1;
    used[lane] = l1;
    const el = document.createElement("div");
    el.className = "t" + (t.critical ? " crit" : "");
    el.style.left = l0 + "px";
    el.style.width = (l1 - l0) + "px";
    el.style.top = (3 + lane * 3.7) + "px";
    const st = STATES[t.state] || STATES.open;
    el.style.background = st.hollow ? "var(--st-open)" : st.c;
    mini.append(el);
  }
  for (const u of (mode === "vision" ? [0, CPM.length]
                                     : [nowDay(), M.hi - 3])) {
    const n = document.createElement("div");
    n.className = "edge"; n.style.left = mx(u) + "px";
    mini.append(n);
  }
  const win = document.createElement("div");
  win.className = "win"; win.id = "win";
  mini.append(win);
  syncWin();
}

function syncWin() {
  const win = $("win"); if (!win) return;
  const W = mini.clientWidth || 1;
  const v0 = wrap.scrollLeft / ppu + M.lo,
        v1 = (wrap.scrollLeft + wrap.clientWidth - LEFT) / ppu + M.lo;
  win.style.left = (v0 - M.lo) / span() * W + "px";
  win.style.width = Math.max(6, (v1 - v0) / span() * W) + "px";
}

function panTo(u) {
  wrap.scrollLeft = (u - M.lo) * ppu - (wrap.clientWidth - LEFT) / 2;
  syncWin();
}

mini.addEventListener("mousedown", e => {
  const W = mini.clientWidth || 1;
  const jump = ev => panTo(M.lo +
    (ev.clientX - mini.getBoundingClientRect().left) / W * span());
  jump(e);
  const move = ev => jump(ev);
  const up = () => { removeEventListener("mousemove", move);
                     removeEventListener("mouseup", up); };
  addEventListener("mousemove", move); addEventListener("mouseup", up);
});

/* ── controls ─────────────────────────────────────────────────────────── */
function setZoom(next, keepPx) {
  const at = keepPx === undefined ? (wrap.clientWidth - LEFT) / 2 : keepPx;
  const u = (wrap.scrollLeft + at) / ppu + M.lo;
  ppu = Math.min(M.max, Math.max(M.min, next));
  place();
  wrap.scrollLeft = (u - M.lo) * ppu - at;
  syncWin();
}

function zoomButtons() {
  $("zooms").innerHTML = M.zooms
    .map(([n, v]) => `<button data-z="${v}">${n}</button>`).join("") +
    '<button id="fit">fit</button>';
  for (const b of $("zooms").querySelectorAll("[data-z]"))
    b.onclick = () => setZoom(+b.dataset.z);
  $("fit").onclick = () => {
    ppu = Math.min(M.max, Math.max(M.min,
      (wrap.clientWidth - LEFT - 16) / span()));
    place(); wrap.scrollLeft = 0; syncWin();
  };
}

function setMode(next) {
  mode = next; M = MODE[mode]; ppu = M.ppu;
  $("mVision").classList.toggle("on", mode === "vision");
  $("mDates").classList.toggle("on", mode === "dates");
  $("sub").textContent = mode === "vision"
    ? "distance to the vision" : "the worker-limited calendar";
  zoomButtons();
  build(); $("fit").click();
}
$("mVision").onclick = () => setMode("vision");
$("mDates").onclick = () => setMode("dates");

$("zi").onclick = () => setZoom(ppu * 1.35);
$("zo").onclick = () => setZoom(ppu / 1.35);
$("ce").onclick = () => {
  const g = GROUPS[groupBy];
  if (collapsed.size) collapsed.clear();
  else for (const t of tasks) if (matches(t) && g.key(t) !== "")
    collapsed.add(g.key(t));
  build(); place();
};
$("grp").onchange = () => { groupBy = $("grp").value; collapsed.clear();
                            build(); place(); };
$("q").oninput = () => { filter = $("q").value.trim(); build(); place(); };
$("onlycrit").onclick = () => {
  critOnly = !critOnly; $("onlycrit").classList.toggle("on", critOnly);
  build(); place();
};
$("onlyready").onclick = () => {
  readyOnly = !readyOnly; $("onlyready").classList.toggle("on", readyOnly);
  build(); place();
};
wrap.addEventListener("scroll", () => syncWin(), {passive: true});
wrap.addEventListener("wheel", e => {
  if (e.ctrlKey || e.metaKey) {
    e.preventDefault();
    setZoom(ppu * (e.deltaY < 0 ? 1.12 : 1 / 1.12),
      e.clientX - wrap.getBoundingClientRect().left - LEFT);
  }
}, {passive: false});
addEventListener("resize", () => { place(); syncWin(); });
addEventListener("keydown", e => {
  if (e.target.tagName === "INPUT") {
    if (e.key === "Escape") { $("q").value = ""; filter = ""; build(); place();
                              $("q").blur(); }
    return;
  }
  if (e.key === "n") { e.preventDefault(); $("newprd").click(); }
  else if (e.key === "/") { e.preventDefault();
    (view === "list" ? $("lq") : $("q")).focus(); }
  else if (e.key === "f") $("fit").click();
  else if (e.key === "v") setMode(mode === "vision" ? "dates" : "vision");
  else if (e.key === "c") $("onlycrit").click();
  else if (e.key === "r") $("onlyready").click();
  else if (e.key === "+" || e.key === "=") $("zi").click();
  else if (e.key === "-") $("zo").click();
  else if (e.key === "Escape") {
    if ($("drawer").classList.contains("open")) closeDrawer();
    else { selected = null; paint(); }
  }
});

/* ── the detail pane ──────────────────────────────────────────────────────
   A bar says when and how long. Everything else about a PRD — what it asks
   for, what it is blocked on, what was answered about it — lives here, and is
   editable in place: the panel writes prd.md through the service, one field at
   a time. Served live it fetches; opened as a file with no service it degrades
   to what the payload already carries.                                       */
// The daemon stamps these in: the board's key, and the prefix its own routes
// live under, so the same page works behind a reverse proxy with no absolute
// URL anywhere in it.
const BOARD_KEY = window.__BOARD || null;
const API = window.__BASE || "";
const SERVED = !!BOARD_KEY;
const STATE_LIST = Object.keys(STATES).concat(["done"]);
let dTask = null, dData = null, dDirty = false;
// the live page reloads itself on every board change; it must not do that
// while someone is halfway through typing into this panel
window.__pearde_hold = () => dDirty;

// one `## Heading` section out of a body, ending at the next heading
function section(body, name) {
  const re = new RegExp("^##\\s+" + name + "\\s*$", "im");
  const m = re.exec(body || "");
  if (!m) return "";
  const rest = body.slice(m.index + m[0].length);
  const nxt = rest.search(/^##\s+/m);
  return (nxt < 0 ? rest : rest.slice(0, nxt))
    .replace(/<!--[\s\S]*?-->/g, "").trim();
}

async function openDrawer(t) {
  dTask = t; dDirty = false; dData = null;
  $("drawer").classList.add("open");
  $("dtitle").value = t.title || t.name;
  $("drel").textContent = t.rel + (t.board ? "  ·  " + t.board : "");
  $("dmsg").textContent = SERVED ? "loading…" : "read-only — no daemon";
  drawBody();
  // the open PRD lives in the URL: a deep link to one task, and the thing
  // that survives the live page reloading itself
  const h = "#prd=" + encodeURIComponent(t.rel);
  if (location.hash !== h) history.replaceState(null, "", h);
  if (!SERVED) return;
  try {
    const r = await fetch(API + "/prd?board=" + encodeURIComponent(BOARD_KEY) +
                          "&rel=" + encodeURIComponent(t.rel));
    if (!r.ok) throw new Error(await r.text());
    dData = await r.json();
    $("dmsg").textContent = "";
    drawBody();
  } catch (e) {
    $("dmsg").textContent = "could not load the PRD";
  }
}

function closeDrawer() {
  $("drawer").classList.remove("open");
  dTask = null; dDirty = false;
  history.replaceState(null, "", location.pathname + location.search);
}

function drawBody() {
  const t = dTask, d = dData;
  if (!t) return;
  const facts = t.plain ? [["est", fmtH(t.est)], ["prio", t.prio],
                          ["state", t.state], ["not in the plan", "—"]] : [
    ["est", fmtH(t.est)], ["prio", t.prio],
    ["wave", t.wave == null ? "—" : t.wave],
    ["starts", "+" + fmtH(t.es)], ["ends", "+" + fmtH(t.ef)],
    ["float", t.critical ? "★ critical" : fmtH(t.slack)],
    ["unblocks", fmtH(t.unblocks) + " · " + t.downstream + " PRD(s)"],
    ["dates", fmtD(t.startDay) + " → " + fmtD(t.endDay)],
  ];
  let h = '<h4>state</h4><div class="fields">' +
    '<select id="dstate">' + STATE_LIST.map(s =>
      `<option${s === t.state ? " selected" : ""}>${s}</option>`).join("") +
    "</select>" +
    '<input type="number" id="dprio" step="1" value="' + t.prio + '">' +
    "</div>";
  h += '<h4>plan</h4><div class="facts">' + facts.map(([k, v]) =>
    `<span>${k} <b>${esc(v)}</b></span>`).join("") + "</div>";
  if (t.deps.length || t.feeds.length) {
    h += "<h4>depends</h4><div class=chips>" +
      t.deps.map(x => `<span class="chip2" data-go="${esc(x.rel)}">◂ ${esc(x.name)}</span>`).join("") +
      t.feeds.map(x => `<span class="chip2" data-go="${esc(x.rel)}">${esc(x.name)} ▸</span>`).join("") +
      "</div>";
  }
  if (d && d.fm) {
    const skip = {state: 1, priority: 1};
    const rows = Object.entries(d.fm).filter(([k, v]) => !skip[k] &&
      !Array.isArray(v) && v !== "");
    if (rows.length)
      h += "<h4>frontmatter</h4><div class=facts>" + rows.map(([k, v]) =>
        `<span>${esc(k)} <b>${esc(v)}</b></span>`).join("") + "</div>";
  }
  // Questions and answers where they are actually read. A PRD in `question`
  // is the board waiting on a person; this is the whole exchange — the
  // section it wrote, and a box that writes the answer back and reopens it,
  // the same two edits the orchestrator makes when the answer is typed at a
  // terminal.
  if (d) {
    const qs = section(d.body, "Questions");
    if (t.state === "question" || qs)
      h += '<div class="ask"><h5>' +
        (t.state === "question" ? "waiting on you" : "questions") + "</h5>" +
        (qs ? "<pre>" + esc(qs) + "</pre>" : "") +
        '<textarea class="say" id="dsay" placeholder="the answer — numbered to ' +
        'match"></textarea><div class="row2">' +
        '<button id="danswer">answer &amp; reopen</button>' +
        '<span class="hint">writes ## Answers, sets state open</span></div></div>';
    const ans = section(d.body, "Answers");
    if (ans && t.state !== "question")
      h += "<h4>answers</h4><pre class=sec>" + esc(ans) + "</pre>";
    const rep2 = section(d.body, "Report");
    if (rep2)
      h += "<h4>report</h4><pre class=sec>" + esc(rep2.slice(0, 1500)) + "</pre>";
  }
  h += "<h4>body</h4><textarea id=dbodytext " +
       (d ? "" : "disabled") + ">" + esc(d ? d.body : "") + "</textarea>";
  if (d)
    h += '<h4>note</h4><textarea class="say" id="dnote" placeholder="a note for ' +
      'whoever picks this up"></textarea><div class="row2">' +
      '<button id="dnoteadd">append to ## Notes</button></div>';
  if (d && d.specs && d.specs.length)
    h += "<h4>specs · " + d.specs.length + "</h4>" + d.specs.map(sp =>
      `<div class="spec"><div>${esc(sp.title)}</div>` +
      `<div class="f">${esc(sp.file)}${sp.est ? " · " + esc(sp.est) : ""}` +
      `${sp.state ? " · " + esc(sp.state) : ""}</div></div>`).join("");
  h += '<h4>elsewhere</h4><div id=dlinks>' +
    (d ? `<a href="#" id="dcopy" data-p="${esc(d.file)}">${esc(d.path)}</a>` : "") +
    "</div>";
  $("dbody").innerHTML = h;
  for (const el of $("dbody").querySelectorAll("[data-go]"))
    el.onclick = () => { const x = byRel.get(el.dataset.go); if (x) focusTask(x); };
  const copy = $("dcopy");
  if (copy) copy.onclick = ev => {
    ev.preventDefault();
    navigator.clipboard && navigator.clipboard.writeText(copy.dataset.p);
    $("dmsg").textContent = "path copied";
  };
  const ansBtn = $("danswer");
  if (ansBtn) ansBtn.onclick = async () => {
    const text = $("dsay").value.trim();
    if (!text) return;
    $("dmsg").textContent = "answering…";
    const out = await save(dTask.rel, {append: text, heading: "Answers",
                                       fm: {state: "open"}});
    $("dmsg").textContent = out.error ? "not saved — " + out.error
      : "answered · the PRD is open again";
    if (!out.error) { dData = null; dDirty = false; openDrawer(dTask); }
  };
  const noteBtn = $("dnoteadd");
  if (noteBtn) noteBtn.onclick = async () => {
    const text = $("dnote").value.trim();
    if (!text) return;
    const out = await save(dTask.rel, {append: text, heading: "Notes"});
    $("dmsg").textContent = out.error ? "not saved — " + out.error : "noted";
    if (!out.error) { dData = null; dDirty = false; openDrawer(dTask); }
  };
  for (const id of ["dstate", "dprio", "dbodytext"]) {
    const el = $(id);
    if (el) el.oninput = () => { dDirty = true; $("dmsg").textContent = "unsaved"; };
  }
  $("dtitle").oninput = () => { dDirty = true; $("dmsg").textContent = "unsaved"; };
}

async function saveDrawer() {
  if (!dTask || !SERVED) return;
  const payload = {board: BOARD_KEY, prd: dTask.rel,
                   title: $("dtitle").value.trim(), fm: {}};
  const st = $("dstate"), pr = $("dprio"), bd = $("dbodytext");
  if (st) payload.fm.state = st.value;
  if (pr && pr.value !== "") payload.fm.priority = pr.value;
  if (bd && dData && bd.value !== dData.body) payload.body = bd.value;
  $("dmsg").textContent = "saving…";
  try {
    const r = await fetch(API + "/edit", {method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)});
    const out = await r.json();
    if (!r.ok) throw new Error(out.error || "failed");
    dDirty = false;
    $("dmsg").textContent = "saved " + (out.wrote || []).join(", ") +
      (out.claim ? " · note: " + out.claim + " holds this PRD" : "");
  } catch (e) {
    $("dmsg").textContent = "not saved — " + e.message;
  }
}

$("dclose").onclick = closeDrawer;
$("dgo").onclick = saveDrawer;
$("drevert").onclick = () => { dDirty = false; drawBody();
                               $("dmsg").textContent = "reverted"; };

function focusTask(t) {
  selected = t;
  openDrawer(t);
  const g = GROUPS[groupBy];
  collapsed.delete(g.key(t));
  build(); place();
  panTo((M.u0(t) + M.u1(t)) / 2);
  if (t.row) t.row.scrollIntoView({block: "center"});
  paint();
}

/* ── header, frontier, legend, table ─────────────────────────────────── */
{
  const c = DATA.counts;
  const bits = ["<b>" + tasks.length + "</b> left",
                '<span class="crit">' + fmtH(CPM.length) +
                " to the vision</span>",
                "Σ" + fmtH(CPM.total) + " of work"];
  // the two numbers a plan is actually steered by: how many agents the
  // fastest path wants at its widest, and what the configured worker count
  // costs instead. The gap between them is the decision.
  const cal = Math.max(...tasks.map(t => t.endDay), 0) * (DATA.dayHours || 8);
  bits.push("peak <b>" + CPM.peak + "</b> agents");
  if (cal > CPM.length * 1.05)
    bits.push("at " + DATA.workers + " workers: " + fmtH(cal));
  if (c.done) bits.push(c.done + " done");
  if (c.parked) bits.push(c.parked + " parked");
  if (c.containers) bits.push(c.containers + " parent(s) folded");
  if ((DATA.boards || []).length) bits.push(DATA.boards.length + " boards");
  $("stats").innerHTML = bits.join(" · ");
  $("corner").innerHTML = "<span>task</span>";
  if (DATA.vision && DATA.vision.purpose)
    $("purpose").textContent = DATA.vision.purpose;

  // the frontier: everything dispatchable now, biggest door first. This is
  // the dispatch order — take from the left and the vision arrives soonest.
  const ready = CPM.ready.map(r => byRel.get(r)).filter(Boolean);
  $("front").innerHTML = '<span class="h">ready now</span>' +
    (ready.length ? ready.slice(0, 14).map((t, i) =>
      `<span class="p${t.critical ? " crit" : ""}" data-r="${esc(t.rel)}">` +
      `${t.critical ? "★ " : ""}<b>${esc(t.name)}</b> ` +
      `<em>${fmtH(t.est)}${t.unblocks ? " ▸" + fmtH(t.unblocks) : ""}</em>` +
      "</span>").join("") +
      (ready.length > 14 ? `<span class="h">+${ready.length - 14} more</span>` : "")
      : '<span class="h">' + (tasks.length
          ? "nothing — every PRD left waits on another"
          : "nothing scheduled — run plan") + "</span>");
  for (const el of $("front").querySelectorAll(".p"))
    el.onclick = () => focusTask(byRel.get(el.dataset.r));

  const present = [...new Set(tasks.map(t => t.state))];
  const order = Object.keys(STATES);
  present.sort((p, q) => order.indexOf(p) - order.indexOf(q));
  $("legend").innerHTML = present.map(s => {
    const st = STATES[s];
    return "<span><i" + (st.hollow ? ' class="hollow"' : "") +
      ' style="background:' + (st.hollow ? "transparent" : st.c) +
      '"></i>' + s + "</span>";
  }).join("") +
    '<span><i class="crit"></i>critical chain</span>' +
    "<span><b></b>now · vision</span>" +
    '<span style="color:var(--muted)">click a row for arrows · ' +
    "<kbd>/</kbd> filter · <kbd>v</kbd> axis · <kbd>c</kbd> critical · " +
    "<kbd>r</kbd> ready · <kbd>f</kbd> fit · ctrl+wheel zoom</span>";

  if (DATA.unplanned.length)
    $("note").textContent = "not in the last plan (no bar): " +
      DATA.unplanned.join(", ") + " — re-run plan to schedule them";

  // the table that used to sit under the chart is now the list view
}

/* ── the other three views ────────────────────────────────────────────────
   One board, four readings. The timeline answers "what is in front of us";
   the board answers "what is where"; the list answers "show me all of it";
   the analytics answer "how is this going". They share the payload, the
   detail pane and the state colours, so nothing has to be learned twice.  */
const ALL = DATA.all || [];
const HIST = DATA.history || [];
const allByRel = new Map(ALL.map(r => [r.rel, r]));
const STATE_ORDER = ["open", "refine", "question", "analyzing", "specced",
                     "claimed", "blocked", "failed", "done"];
const stateColor = s => (STATES[s] || {}).c ||
  (s === "done" ? "var(--muted)" : "var(--roll)");

// a row from `all` can be opened in the detail pane too — it just has no
// place in the plan, so the plan facts are the ones that go missing
function taskFor(rel) {
  const t = byRel.get(rel);
  if (t) return t;
  const r = allByRel.get(rel);
  if (!r) return null;
  return Object.assign({}, r, {es: 0, ef: 0, slack: 0, critical: false,
    unblocks: 0, downstream: 0, startDay: 0, endDay: 0, wave: null,
    deps: [], feeds: [], plain: true});
}

let view = "timeline";
function setView(v) {
  view = v;
  for (const el of document.querySelectorAll("section[data-view]"))
    el.classList.toggle("on", el.dataset.view === v);
  for (const b of $("views").querySelectorAll("button"))
    b.classList.toggle("on", b.dataset.v === v);
  $("tcontrols").style.display = v === "timeline" ? "" : "none";
  $("inview").style.display = v === "timeline" ? "" : "none";
  if (v === "board") drawBoard();
  if (v === "list") drawList();
  if (v === "analytics") drawAnalytics();
  if (v === "memos") drawMemos();
  if (v === "timeline") { place(); syncWin(); }
  const h = v === "timeline" ? "" : "#view=" + v;
  if (!location.hash.startsWith("#prd=")) history.replaceState(null, "", h ||
    location.pathname + location.search);
}
for (const b of $("views").querySelectorAll("button"))
  b.onclick = () => setView(b.dataset.v);

/* ── board ─────────────────────────────────────────────────────────────── */
function drawBoard() {
  const cols = new Map();
  for (const s of STATE_ORDER) cols.set(s, []);
  for (const r of ALL) {
    if (!cols.has(r.state)) cols.set(r.state, []);   // a state of the user's own
    cols.get(r.state).push(r);
  }
  const el = $("board");
  el.innerHTML = "";
  for (const [st, rows] of cols) {
    if (!rows.length && !STATE_ORDER.includes(st)) continue;
    rows.sort((p, q) => q.prio - p.prio || p.rel.localeCompare(q.rel));
    const col = document.createElement("div");
    col.className = "col"; col.dataset.state = st;
    const hrs = rows.reduce((a, r) => a + r.est, 0);
    col.innerHTML = '<h3><i style="background:' + stateColor(st) + '"></i>' +
      esc(st) + '<span class="n">' + rows.length +
      (hrs ? " · " + fmtH(hrs) : "") + "</span></h3>";
    const box = document.createElement("div");
    box.className = "cards";
    const CAP = st === "done" ? 40 : 200;
    for (const r of rows.slice(0, CAP)) {
      const t = byRel.get(r.rel);
      const c = document.createElement("div");
      c.className = "card"; c.draggable = SERVED; c.dataset.rel = r.rel;
      c.innerHTML = '<div class="t">' + (t && t.critical ?
        '<span class="star">★ </span>' : "") + esc(r.title || r.name) +
        '</div><div class="m">' + (r.board ?
        '<span class="chip">' + esc(r.board) + "</span>" : "") +
        "<span>p" + r.prio + "</span>" + (r.est ? "<span>" + fmtH(r.est) +
        "</span>" : "") + (t && t.wave ? "<span>w" + t.wave + "</span>" : "") +
        "</div>";
      c.onclick = () => { const x = taskFor(r.rel); if (x) openDrawer(x); };
      c.addEventListener("dragstart", e => {
        e.dataTransfer.setData("text/plain", r.rel);
        c.classList.add("drag");
      });
      c.addEventListener("dragend", () => c.classList.remove("drag"));
      box.append(c);
    }
    if (rows.length > CAP) {
      const more = document.createElement("div");
      more.className = "card"; more.style.cursor = "default";
      more.innerHTML = '<div class="m">+' + (rows.length - CAP) +
        " more — the list view has all of them</div>";
      more.draggable = false;
      more.onclick = () => setView("list");
      box.append(more);
    }
    col.append(box);
    col.addEventListener("dragover", e => { e.preventDefault();
      col.classList.add("over"); });
    col.addEventListener("dragleave", () => col.classList.remove("over"));
    col.addEventListener("drop", async e => {
      e.preventDefault(); col.classList.remove("over");
      const rel = e.dataTransfer.getData("text/plain");
      const row = allByRel.get(rel);
      if (!row || row.state === st) return;
      row.state = st;                       // optimistic: the drop is the edit
      drawBoard();
      await save(rel, {fm: {state: st}});
    });
    el.append(col);
  }
}

async function save(rel, payload) {
  if (!SERVED) return {error: "no daemon — this file is read-only"};
  try {
    const r = await fetch(API + "/edit", {method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(Object.assign({board: BOARD_KEY, prd: rel}, payload))});
    return await r.json();
  } catch (e) { return {error: String(e)}; }
}

/* ── list ──────────────────────────────────────────────────────────────── */
let listBy = "prio", listDesc = true;
function drawList() {
  const cols = [["rel", "prd"], ["state", "state"], ["prio", "prio"],
                ["est", "est"], ["actual", "actual"], ["board", "board"],
                ["wave", "wave"]];
  const f = ($("lq").value || "").trim().toLowerCase();
  const rows = ALL.filter(r => !f || r.rel.toLowerCase().includes(f) ||
    (r.title || "").toLowerCase().includes(f) || r.state.includes(f) ||
    (r.board || "").includes(f)).sort((p, q) => {
    const k = listBy;
    const a = k === "wave" ? ((byRel.get(p.rel) || {}).wave || 0) : p[k];
    const b = k === "wave" ? ((byRel.get(q.rel) || {}).wave || 0) : q[k];
    const c = typeof a === "number" && typeof b === "number"
      ? a - b : String(a == null ? "" : a).localeCompare(String(b == null ? "" : b));
    return listDesc ? -c : c;
  });
  $("list").innerHTML = "<table><thead><tr>" + cols.map(([k, l]) =>
    `<th data-k="${k}" class="${listBy === k ? "by" : ""}">${l}` +
    (listBy === k ? (listDesc ? " ↓" : " ↑") : "") + "</th>").join("") +
    "</tr></thead><tbody>" + rows.map(r => {
      const t = byRel.get(r.rel) || {};
      return `<tr class="r" data-rel="${esc(r.rel)}"><td><i style="background:` +
        stateColor(r.state) + '"></i>' + esc(r.rel) + "</td><td>" +
        esc(r.state) + "</td><td>" + r.prio + "</td><td>" +
        (r.est ? fmtH(r.est) : "") + "</td><td>" +
        (r.actual ? fmtH(r.actual) : "") + "</td><td>" +
        esc(r.board || "") + "</td><td>" + (t.wave || "") + "</td></tr>";
    }).join("") + "</tbody></table>";
  $("lcount").textContent = rows.length + " of " + ALL.length +
    " · click a row for the PRD";
  for (const th of $("list").querySelectorAll("th"))
    th.onclick = () => { const k = th.dataset.k;
      listDesc = listBy === k ? !listDesc : true; listBy = k; drawList(); };
  for (const tr of $("list").querySelectorAll("tr.r"))
    tr.onclick = () => { const x = taskFor(tr.dataset.rel); if (x) openDrawer(x); };
}

$("lq").oninput = () => drawList();

/* ── memos: the board's decisions, read where the work is ─────────────── */
let memosLoaded = null;
async function drawMemos() {
  if (!SERVED) {
    $("memos").innerHTML = '<div class="chart"><div class="empty">memos are ' +
      "read live — open this board through the service to see them</div></div>";
    return;
  }
  if (!memosLoaded) {
    try {
      const r = await fetch(API + "/memos?board=" + encodeURIComponent(BOARD_KEY));
      memosLoaded = (await r.json()).memos || [];
    } catch (e) { memosLoaded = []; }
  }
  $("memos").innerHTML = memosLoaded.length ? memosLoaded.map(m =>
    '<div class="memo"><h3>' + esc(m.subject || m.slug) + "</h3>" +
    '<div class="f"><b>' + esc(m.slug) + "</b> · " + esc(m.kind || "") + " · " +
    esc(m.status || "") + " · " + esc(m.date || "") +
    (m.prds && m.prds.length ? " · governs " + esc(m.prds.join(", ")) : "") +
    "</div><pre>" + esc((m.body || "").slice(0, 3000)) + "</pre></div>").join("")
    : '<div class="chart"><div class="empty">no memos yet — a decision gets one ' +
      "when there is a decision</div></div>";
}

/* ── writing a PRD from the view ───────────────────────────────────────── */
$("newprd").onclick = () => { $("newbox").classList.add("on"); $("ntitle").focus(); };
$("ncancel").onclick = () => $("newbox").classList.remove("on");
$("newbox").onclick = e => {
  if (e.target.id === "newbox") $("newbox").classList.remove("on");
};
$("ncreate").onclick = async () => {
  const title = $("ntitle").value.trim();
  if (!title || !SERVED) return;
  try {
    const r = await fetch(API + "/new", {method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({board: BOARD_KEY, title: title,
        body: $("nbody").value, priority: $("nprio").value || 0,
        parent: $("nparent").value.trim()})});
    const out = await r.json();
    if (out.prd) {
      location.hash = "#prd=" + encodeURIComponent(out.prd);
      location.reload();     // the daemon rebuilds the page around it
    } else {
      alert(out.error || "not written");
    }
  } catch (e) {}
};

/* ── analytics ─────────────────────────────────────────────────────────────
   Four questions and a row of numbers. Every chart is one measure on one
   axis, direct-labelled, with the list view as its table. State keeps the
   colour it has everywhere else in this page; the by-board bars use the
   categorical slots in fixed order, never cycled.                          */
function tile(k, v, s) {
  return '<div class="tile"><div class="k">' + k + '</div><div class="v">' +
    v + '</div><div class="s">' + (s || "") + "</div></div>";
}

function bars(rows, color, fmt) {
  const max = Math.max(...rows.map(r => r.v), 1);
  return rows.map((r, i) =>
    '<div class="brow"><span class="lab" title="' + esc(r.k) + '">' +
    esc(r.k) + '</span><span class="track"><span class="fill" style="width:' +
    (r.v / max * 100).toFixed(1) + "%;background:" +
    (typeof color === "function" ? color(r, i) : color) +
    '"></span></span><span class="val">' + fmt(r) + "</span></div>").join("");
}

function drawAnalytics() {
  const live = ALL.filter(r => STATE_ORDER.includes(r.state) && r.state !== "done");
  const done = ALL.filter(r => r.state === "done");
  const parked = ALL.filter(r => !STATE_ORDER.includes(r.state));
  const hLeft = live.reduce((a, r) => a + r.est, 0);
  const hDone = done.reduce((a, r) => a + r.est, 0);
  const pct = Math.round(done.length / Math.max(ALL.length - parked.length, 1) * 100);
  const ready = tasks.filter(t => t.ready).length;
  const waiting = ALL.filter(r => r.state === "question").length;
  const blocked = ALL.filter(r => r.state === "blocked").length;
  $("tiles").innerHTML =
    tile("done", pct + "%", done.length + " of " +
         (ALL.length - parked.length) + " PRDs") +
    tile("left", live.length, fmtH(hLeft) + " estimated") +
    tile("to the vision", fmtH(CPM.length),
         "of " + fmtH(CPM.total) + " in the plan") +
    tile("peak agents", CPM.peak, "at " + DATA.workers + " workers: " +
         fmtH(Math.max(...tasks.map(t => t.endDay), 0) * (DATA.dayHours || 8))) +
    tile("ready now", ready, "dispatchable this second") +
    tile("waiting on you", waiting + blocked,
         waiting + " question · " + blocked + " blocked");

  // 1 — where the work sits
  const byState = [];
  for (const st of STATE_ORDER.concat(
        [...new Set(parked.map(r => r.state))])) {
    const rows = ALL.filter(r => r.state === st);
    if (rows.length) byState.push({k: st, v: rows.length,
      h: rows.reduce((a, r) => a + r.est, 0)});
  }
  // 2 — where the hours are: members on a master, top-level trees otherwise
  const key = (DATA.boards || []).length ? (r => r.board || DATA.board)
    : (r => r.rel.split("/")[0]);
  const groups = new Map();
  for (const r of live) groups.set(key(r), (groups.get(key(r)) || 0) + r.est);
  let byGroup = [...groups].map(([k, v]) => ({k: k, v: v}))
    .sort((p, q) => q.v - p.v);
  if (byGroup.length > 8) {
    const rest = byGroup.slice(8).reduce((a, r) => a + r.v, 0);
    byGroup = byGroup.slice(0, 8).concat([{k: "other", v: rest}]);
  }
  const CAT = ["var(--c1)", "var(--c2)", "var(--c3)", "var(--c4)", "var(--c5)"];

  const cal = done.filter(r => r.est > 0 && r.actual > 0);
  const ratios = cal.map(r => r.actual / r.est).sort((a, b) => a - b);
  const med = ratios.length ? ratios[Math.floor(ratios.length / 2)] : 0;

  $("charts").innerHTML =
    '<div class="chart"><h3>Where the work sits</h3>' +
    '<p class="sub">every PRD by state · bar is the count, the number is the hours</p>' +
    bars(byState, r => stateColor(r.k),
         r => r.v + (r.h ? " · " + fmtH(r.h) : "")) + "</div>" +

    '<div class="chart"><h3>Where the hours are</h3>' +
    '<p class="sub">' + ((DATA.boards || []).length ? "estimated hours left per member board"
      : "estimated hours left per top-level tree") + "</p>" +
    (byGroup.length ? bars(byGroup, (r, i) => CAT[i % CAT.length],
      r => fmtH(r.v)) : '<div class="empty">nothing left to weigh</div>') +
    "</div>" +

    '<div class="chart"><h3>Estimates against reality</h3>' +
    '<p class="sub">' + (cal.length
      ? cal.length + " done PRDs carry an <code>actual:</code> · median " +
        med.toFixed(2) + "× the estimate"
      : "no done PRD carries an <code>actual:</code> yet") + "</p>" +
    (cal.length >= 3 ? scatter(cal) :
      '<div class="empty">calibration needs a few finished PRDs with ' +
      "<code>actual:</code> written on them</div>") + "</div>" +

    '<div class="chart"><h3>Hours left over time</h3>' +
    '<p class="sub">one point a day, since the day the board started keeping ' +
    "count</p>" +
    (HIST.length >= 2 ? burndown(HIST) :
      '<div class="empty">collecting — ' + (HIST.length
        ? "one day so far (" + HIST[0].d + "), the line needs two"
        : "nothing recorded yet") + "</div>") + "</div>";
}

function scatter(rows) {
  const W = 460, H = 220, pad = 30;
  const mx = Math.max(...rows.map(r => Math.max(r.est, r.actual)), 1);
  const X = v => pad + v / mx * (W - pad - 8);
  const Y = v => H - pad - v / mx * (H - pad - 10);
  let g = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="estimate against actual">`;
  g += `<line class="ax" x1="${pad}" y1="${H - pad}" x2="${W - 4}" y2="${H - pad}"/>`;
  g += `<line class="ax" x1="${pad}" y1="8" x2="${pad}" y2="${H - pad}"/>`;
  g += `<line class="ref" x1="${X(0)}" y1="${Y(0)}" x2="${X(mx)}" y2="${Y(mx)}"/>`;
  g += `<text class="lbl" x="${X(mx)}" y="${Y(mx) - 5}" text-anchor="end">on the estimate</text>`;
  g += `<text class="lbl" x="${pad}" y="${H - 8}">0</text>`;
  g += `<text class="lbl" x="${W - 4}" y="${H - 8}" text-anchor="end">est ${fmtH(mx)}</text>`;
  g += `<text class="lbl" x="4" y="14">actual ${fmtH(mx)}</text>`;
  for (const r of rows)
    g += `<circle class="dot" cx="${X(r.est).toFixed(1)}" cy="${Y(r.actual).toFixed(1)}" r="4.5"` +
      ` data-rel="${esc(r.rel)}"><title>${esc(r.name)} — est ${fmtH(r.est)}, actual ${fmtH(r.actual)}</title></circle>`;
  return g + "</svg>";
}

function burndown(h) {
  const W = 460, H = 220, pad = 34;
  const vals = h.map(r => r.hleft || 0);
  const mx = Math.max(...vals, 1);
  const X = i => pad + (h.length < 2 ? 0 : i / (h.length - 1)) * (W - pad - 8);
  const Y = v => H - pad - v / mx * (H - pad - 12);
  const pts = h.map((r, i) => `${X(i).toFixed(1)},${Y(r.hleft || 0).toFixed(1)}`);
  let g = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="hours left over time">`;
  g += `<line class="ax" x1="${pad}" y1="${H - pad}" x2="${W - 4}" y2="${H - pad}"/>`;
  g += `<polygon class="area" points="${X(0).toFixed(1)},${H - pad} ${pts.join(" ")} ${X(h.length - 1).toFixed(1)},${H - pad}"/>`;
  g += `<polyline class="line" points="${pts.join(" ")}"/>`;
  h.forEach((r, i) => {
    g += `<circle class="dot" cx="${X(i).toFixed(1)}" cy="${Y(r.hleft || 0).toFixed(1)}" r="3.5">` +
      `<title>${esc(r.d)} — ${fmtH(r.hleft || 0)} left, ${r.done} done</title></circle>`;
  });
  g += `<text class="lbl" x="${pad}" y="${H - 10}">${esc(h[0].d)}</text>`;
  g += `<text class="lbl" x="${W - 4}" y="${H - 10}" text-anchor="end">${esc(h[h.length - 1].d)}</text>`;
  g += `<text class="lbl" x="4" y="14">${fmtH(mx)}</text>`;
  return g + "</svg>";
}

setMode("vision");
if (location.hash.startsWith("#view=")) setView(location.hash.slice(6));
if (location.hash.startsWith("#prd=")) {
  const back = taskFor(decodeURIComponent(location.hash.slice(5)));
  if (back) back.plain ? openDrawer(back) : focusTask(back);
}
addEventListener("hashchange", () => {
  const r = location.hash.startsWith("#prd=")
    && taskFor(decodeURIComponent(location.hash.slice(5)));
  if (r && r !== dTask) r.plain ? openDrawer(r) : focusTask(r);
});
setInterval(() => { if (mode === "dates") markers(); }, 60000);
</script>
</body>
</html>
"""
