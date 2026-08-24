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



# ── the look ──────────────────────────────────────────────────────────────────
# Greyscale carries the plan; colour is spent only where a person is needed.
#
#   · state-as-progress is a ramp of ink weight, not of hue: open is a whisper,
#     claimed is full ink (full white in the dark theme — furthest along is
#     always the brightest thing on the surface)
#   · the two exception states that mean "a human has to act" are the only
#     coloured marks on the page: question wears amber, blocked/failed wear red
#   · the critical chain is ink outline plus a soft glow — the strongest mark
#     available in a world with no second hue
#   · every row, column and legend entry names its state in text, so nothing
#     is carried by colour alone
#
# The timeline is one <canvas>, drawn virtualised: frozen header and frozen
# task column come free, only the visible rows are ever touched, and gradients
# and glows cost nothing per frame. Everything else on the page is DOM, because
# everything else is text you should be able to select.
TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ — plan</title>
<style>
/* ─────────────────────────────────────────────────────────────────────────
   The board, as a Mac app in graphite.

   Four rules the whole sheet follows:

   1. CONTENT LEADS, CHROME FLOATS. Toolbars, the inspector and the overlay
      are glass — translucent, blurred, hairline-bordered — and the work
      underneath shows through them. Nothing chrome-coloured is opaque.
   2. HIERARCHY BY DEPTH AND WEIGHT, NEVER BY HUE. Elevation, translucency
      and ink weight do the ranking. There is no accent colour: the accent
      IS ink, the way macOS looks with the Graphite highlight selected.
   3. COLOUR IS A SIGNAL, NOT A DECORATION. Amber and red appear only on the
      states that are waiting for a person. If the page has colour on it,
      something wants you.
   4. EVERY NUMBER IS A DOOR. A count, a swatch, a bar, a column head — if it
      names a set of PRDs, clicking it takes you to that set. Nothing on this
      page is a dead end.

   Spacing is the 4/8 grid. Radii are concentric: a control inside a card is
   the card's radius minus its padding. Motion is 150ms for a hover, 280ms on
   Apple's own curve for anything that travels, and none at all when the
   reader asked for none.                                                    */

:root{
  color-scheme:light;
  /* surfaces */
  --bg:#f4f4f6; --content:#ffffff; --content-2:#f8f8fa; --sunk:#ededf0;
  --glass:rgba(251,251,253,.72); --glass-brd:rgba(0,0,0,.10);
  --glass-hi:rgba(255,255,255,.80);
  /* ink — Apple's label hierarchy, with the hue taken out */
  --ink:#101013; --ink2:rgba(0,0,0,.56); --ink3:rgba(0,0,0,.32);
  --ink4:rgba(0,0,0,.14);
  /* fills + separators */
  --fill:rgba(0,0,0,.05); --fill-2:rgba(0,0,0,.09);
  --sep:rgba(0,0,0,.11); --sep-2:rgba(0,0,0,.055);
  --hover:rgba(0,0,0,.038); --sel:rgba(0,0,0,.065);
  --shadow:0 1px 2px rgba(0,0,0,.05), 0 8px 24px -8px rgba(0,0,0,.12);
  --shadow-lg:0 2px 8px rgba(0,0,0,.08), 0 24px 60px -12px rgba(0,0,0,.28);
  /* the accent is ink: a graphite system */
  --accent:#101013; --accent-ink:#ffffff; --accent-wash:rgba(0,0,0,.06);
  /* the only two hues on the page — both mean "a person is needed" */
  --warn:#bd8408; --warn-wash:rgba(189,132,8,.10);
  --danger:#cf332b; --danger-wash:rgba(207,51,43,.09);
  /* the state ramp: one ink, light→dark. Progress is weight. */
  --st-open:rgba(0,0,0,.23); --st-analyzing:rgba(0,0,0,.43);
  --st-specced:rgba(0,0,0,.63); --st-claimed:#18181b;
  --st-question:var(--warn); --st-blocked:var(--danger);
  --st-failed:var(--danger); --st-done:rgba(0,0,0,.11);
  --crit:#0a0a0c;
  --float:rgba(0,0,0,.20); --link:rgba(0,0,0,.30);
  --grid:rgba(0,0,0,.055); --gridw:rgba(0,0,0,.10); --axis:rgba(0,0,0,.16);
  --wash:rgba(0,0,0,.022);
  /* categorical series: ink levels, direct-labelled, never cycled by hue */
  --c1:rgba(0,0,0,.82); --c2:rgba(0,0,0,.62); --c3:rgba(0,0,0,.46);
  --c4:rgba(0,0,0,.32); --c5:rgba(0,0,0,.20);
  /* the canvas asks for these by name */
  --hi:rgba(255,255,255,.30); --lo:rgba(0,0,0,.13);
  /* shape + motion */
  --r-lg:12px; --r-md:10px; --r-sm:7px; --r-xs:5px;
  --dur-fast:.15s; --dur:.28s; --ease:cubic-bezier(.32,.72,0,1);
}
@media (prefers-color-scheme: dark){
  :root:where(:not([data-theme="light"])){ color-scheme:dark;
    --bg:#0b0b0c; --content:#17171a; --content-2:#1e1e21; --sunk:#101012;
    --glass:rgba(28,28,31,.70); --glass-brd:rgba(255,255,255,.11);
    --glass-hi:rgba(255,255,255,.08);
    --ink:#f7f7f8; --ink2:rgba(255,255,255,.63); --ink3:rgba(255,255,255,.34);
    --ink4:rgba(255,255,255,.16);
    --fill:rgba(255,255,255,.07); --fill-2:rgba(255,255,255,.13);
    --sep:rgba(255,255,255,.12); --sep-2:rgba(255,255,255,.07);
    --hover:rgba(255,255,255,.055); --sel:rgba(255,255,255,.10);
    --shadow:0 1px 2px rgba(0,0,0,.5), 0 8px 24px -8px rgba(0,0,0,.6);
    --shadow-lg:0 2px 10px rgba(0,0,0,.6), 0 28px 64px -12px rgba(0,0,0,.8);
    --accent:#f7f7f8; --accent-ink:#0b0b0c; --accent-wash:rgba(255,255,255,.10);
    --warn:#f0b429; --warn-wash:rgba(240,180,41,.13);
    --danger:#ff6259; --danger-wash:rgba(255,98,89,.13);
    --st-open:rgba(255,255,255,.24); --st-analyzing:rgba(255,255,255,.45);
    --st-specced:rgba(255,255,255,.66); --st-claimed:#f7f7f8;
    --st-done:rgba(255,255,255,.13);
    --crit:#ffffff;
    --float:rgba(255,255,255,.22); --link:rgba(255,255,255,.32);
    --grid:rgba(255,255,255,.055); --gridw:rgba(255,255,255,.11);
    --axis:rgba(255,255,255,.18); --wash:rgba(255,255,255,.028);
    --c1:rgba(255,255,255,.86); --c2:rgba(255,255,255,.64);
    --c3:rgba(255,255,255,.47); --c4:rgba(255,255,255,.33);
    --c5:rgba(255,255,255,.21);
    --hi:rgba(255,255,255,.16); --lo:rgba(0,0,0,.22);
  }
}
:root[data-theme="dark"]{ color-scheme:dark;
  --bg:#0b0b0c; --content:#17171a; --content-2:#1e1e21; --sunk:#101012;
  --glass:rgba(28,28,31,.70); --glass-brd:rgba(255,255,255,.11);
  --glass-hi:rgba(255,255,255,.08);
  --ink:#f7f7f8; --ink2:rgba(255,255,255,.63); --ink3:rgba(255,255,255,.34);
  --ink4:rgba(255,255,255,.16);
  --fill:rgba(255,255,255,.07); --fill-2:rgba(255,255,255,.13);
  --sep:rgba(255,255,255,.12); --sep-2:rgba(255,255,255,.07);
  --hover:rgba(255,255,255,.055); --sel:rgba(255,255,255,.10);
  --shadow:0 1px 2px rgba(0,0,0,.5), 0 8px 24px -8px rgba(0,0,0,.6);
  --shadow-lg:0 2px 10px rgba(0,0,0,.6), 0 28px 64px -12px rgba(0,0,0,.8);
  --accent:#f7f7f8; --accent-ink:#0b0b0c; --accent-wash:rgba(255,255,255,.10);
  --warn:#f0b429; --warn-wash:rgba(240,180,41,.13);
  --danger:#ff6259; --danger-wash:rgba(255,98,89,.13);
  --st-open:rgba(255,255,255,.24); --st-analyzing:rgba(255,255,255,.45);
  --st-specced:rgba(255,255,255,.66); --st-claimed:#f7f7f8;
  --st-done:rgba(255,255,255,.13);
  --crit:#ffffff;
  --float:rgba(255,255,255,.22); --link:rgba(255,255,255,.32);
  --grid:rgba(255,255,255,.055); --gridw:rgba(255,255,255,.11);
  --axis:rgba(255,255,255,.18); --wash:rgba(255,255,255,.028);
  --c1:rgba(255,255,255,.86); --c2:rgba(255,255,255,.64);
  --c3:rgba(255,255,255,.47); --c4:rgba(255,255,255,.33);
  --c5:rgba(255,255,255,.21);
  --hi:rgba(255,255,255,.16); --lo:rgba(0,0,0,.22);
}
/* the reader's own settings win over the aesthetic */
@media (prefers-reduced-transparency: reduce){
  :root{ --glass:var(--content); }
}
@media (prefers-contrast: more){
  :root{ --sep:rgba(0,0,0,.4); --ink2:rgba(0,0,0,.86);
         --st-open:rgba(0,0,0,.34); }
  :root[data-theme="dark"],:root:where(:not([data-theme="light"])){
    --sep:rgba(255,255,255,.45); --ink2:rgba(255,255,255,.9);
    --st-open:rgba(255,255,255,.38); }
}
@media (prefers-reduced-motion: reduce){
  *,*::before,*::after{ transition-duration:.01ms !important;
    animation-duration:.01ms !important }
}

*{box-sizing:border-box;margin:0}
html{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}
body{background:var(--bg);color:var(--ink);
  font:13px/1.45 -apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",
    system-ui,sans-serif;
  padding:0 16px 20px;-webkit-tap-highlight-color:transparent}
::selection{background:var(--accent-wash)}
:focus{outline:none}
:focus-visible{outline:2.5px solid var(--ink3);outline-offset:1px;
  border-radius:var(--r-xs)}
/* scrollbars: present when used, invisible when not */
*{scrollbar-width:thin;scrollbar-color:var(--fill-2) transparent}
::-webkit-scrollbar{width:11px;height:11px}
::-webkit-scrollbar-thumb{background:var(--fill-2);border-radius:99px;
  border:3px solid transparent;background-clip:content-box}
::-webkit-scrollbar-thumb:hover{background:var(--ink3);background-clip:content-box}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-corner{background:transparent}

/* ── the toolbar: one glass bar, the app's identity and its views ───────── */
#titlebar{position:sticky;top:0;z-index:30;display:flex;align-items:center;
  gap:14px;margin:0 -16px;padding:9px 16px;
  background:var(--glass);backdrop-filter:saturate(180%) blur(24px);
  -webkit-backdrop-filter:saturate(180%) blur(24px);
  border-bottom:.5px solid var(--glass-brd);
  box-shadow:inset 0 1px 0 var(--glass-hi)}
#titlebar .ident{display:flex;align-items:baseline;gap:8px;min-width:0}
#titlebar h1{font-size:15px;font-weight:640;letter-spacing:-.014em;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#sub{font-size:12px;color:var(--ink2);white-space:nowrap}
#titlebar .right{margin-left:auto;display:flex;gap:8px;align-items:center}

/* segmented control — the sliding pill is one transform, not six repaints */
#views{position:relative;display:flex;background:var(--fill);
  border-radius:9px;padding:2px;gap:0}
#segpill{position:absolute;top:2px;bottom:2px;left:0;width:0;
  background:var(--content);border-radius:7px;
  box-shadow:0 1px 2px rgba(0,0,0,.12),0 0 0 .5px rgba(0,0,0,.05);
  transition:transform var(--dur) var(--ease),width var(--dur) var(--ease);
  pointer-events:none}
:root[data-theme="dark"] #segpill,
:root:where(:not([data-theme="light"])) #segpill{
  box-shadow:0 1px 2px rgba(0,0,0,.5),0 0 0 .5px rgba(255,255,255,.07)}
#views button{position:relative;z-index:1;background:none;border:none;
  color:var(--ink2);font:500 12.5px/1 -apple-system,system-ui,sans-serif;
  padding:6px 13px;border-radius:7px;cursor:pointer;display:flex;gap:6px;
  align-items:center;transition:color var(--dur-fast) ease}
#views button:hover{color:var(--ink)}
#views button.on{color:var(--ink);font-weight:590}
/* a badge is a count that wants you, so it is allowed a hue */
#views .badge{font:600 10px/14px -apple-system,system-ui,sans-serif;
  min-width:16px;height:15px;padding:0 4px;border-radius:99px;
  background:var(--warn);color:#fff;letter-spacing:-.01em;
  font-variant-numeric:tabular-nums;display:none}
:root[data-theme="dark"] #views .badge,
:root:where(:not([data-theme="light"])) #views .badge{color:#1a1400}
#views .badge.on{display:block}

/* controls */
button,select,input[type=text],input[type=search],input[type=number],textarea{
  font:13px/1.3 -apple-system,system-ui,sans-serif;color:var(--ink)}
.btn,#tcontrols button,#newprd,#dclose,#dgo,#drevert,
#ncreate,#ncancel,#danswer,#dnoteadd,.pillbtn,.act{
  background:var(--content);color:var(--ink);
  border:.5px solid var(--sep);border-radius:var(--r-sm);
  padding:5px 11px;min-height:26px;cursor:pointer;font-weight:500;
  box-shadow:0 1px 1.5px rgba(0,0,0,.05);
  transition:background var(--dur-fast) ease,transform var(--dur-fast) ease,
    border-color var(--dur-fast) ease}
.btn:hover,#tcontrols button:hover,#newprd:hover,#dclose:hover,#dgo:hover,
#drevert:hover,#ncreate:hover,#ncancel:hover,#danswer:hover,#dnoteadd:hover,
.act:hover{background:var(--content-2);border-color:var(--ink4)}
#tcontrols button:active,#newprd:active,#dgo:active,#ncreate:active,
.act:active{transform:scale(.97)}
button.on,#tcontrols button.on{background:var(--accent);color:var(--accent-ink);
  border-color:transparent;box-shadow:0 1px 2px rgba(0,0,0,.22)}
button.primary,#newprd.primary,#ncreate.primary,#dgo{background:var(--accent);
  color:var(--accent-ink);border-color:transparent;font-weight:590;
  box-shadow:0 1px 2px rgba(0,0,0,.22)}
button.primary:hover,#newprd.primary:hover,#ncreate.primary:hover,
#dgo:hover{background:var(--accent);opacity:.86}
select{background:var(--content);border:.5px solid var(--sep);
  border-radius:var(--r-sm);padding:5px 24px 5px 9px;min-height:26px;
  cursor:pointer;appearance:none;
  background-image:linear-gradient(45deg,transparent 50%,var(--ink2) 50%),
    linear-gradient(135deg,var(--ink2) 50%,transparent 50%);
  background-position:calc(100% - 13px) 12px,calc(100% - 9px) 12px;
  background-size:4px 4px,4px 4px;background-repeat:no-repeat}
input[type=search],input[type=text],input[type=number]{
  background:var(--content);border:.5px solid var(--sep);
  border-radius:var(--r-sm);padding:5px 10px;min-height:26px}
input::placeholder,textarea::placeholder{color:var(--ink3)}
input:focus-visible,select:focus-visible,textarea:focus-visible{
  border-color:var(--ink3);outline-offset:0}
.seg{display:flex;background:var(--fill);border-radius:8px;padding:2px;gap:2px}
#tcontrols .seg button,.seg button{background:none;border:none;box-shadow:none;
  color:var(--ink2);padding:4px 11px;min-height:22px;border-radius:6px;
  font-weight:500}
#tcontrols .seg button:hover,.seg button:hover{background:var(--hover);
  color:var(--ink)}
#tcontrols .seg button.on,.seg button.on{background:var(--content);
  color:var(--ink);font-weight:590;box-shadow:0 1px 2px rgba(0,0,0,.14)}
label.lab{color:var(--ink2);font-size:12px}

/* ── every number is a door ────────────────────────────────────────────────
   .lnk is the whole grammar of this page: a count, a swatch, a bar or a
   column head that names a set of PRDs, and takes you to that set. It looks
   like text until you approach it.                                         */
.lnk{background:none;border:none;padding:1px 5px;margin:0 -3px;
  border-radius:var(--r-xs);color:inherit;font:inherit;cursor:pointer;
  text-align:left;
  transition:background var(--dur-fast) ease,color var(--dur-fast) ease}
.lnk:hover{background:var(--hover);color:var(--ink)}
.lnk:active{background:var(--fill-2)}
.lnk.hot{color:var(--warn)}
.lnk.hot:hover{background:var(--warn-wash)}

/* the numbers under the toolbar */
#statsbar{display:flex;flex-wrap:wrap;gap:2px 6px;align-items:baseline;
  padding:9px 0 7px;font-size:12.5px;color:var(--ink2)}
#stats{display:flex;flex-wrap:wrap;gap:2px 4px;align-items:baseline}
#stats .sep{color:var(--ink4);pointer-events:none;padding:0 1px}
#stats b{font-weight:620;color:var(--ink);font-variant-numeric:tabular-nums}
#stats .crit b,#stats .crit{color:var(--ink)}
#inview{margin-left:auto;color:var(--ink3);font-size:12px;
  display:flex;gap:4px;align-items:baseline}
#purpose{color:var(--ink2);font-size:12.5px;padding:0 2px 10px;
  max-width:76ch;line-height:1.5}

/* the frontier — what to pick up, in order */
#front{display:flex;gap:6px;flex-wrap:wrap;align-items:center;
  padding:8px 10px;margin:0 0 10px;background:var(--content);
  border:.5px solid var(--sep);border-radius:var(--r-md);font-size:12px;
  box-shadow:var(--shadow)}
#front .h{color:var(--ink3);font-weight:590;margin-right:2px;
  text-transform:uppercase;letter-spacing:.045em;font-size:10.5px}
#front .p{background:var(--fill);border:.5px solid transparent;
  border-radius:99px;padding:3px 11px;cursor:pointer;white-space:nowrap;
  font-size:12px;color:var(--ink2);
  transition:background var(--dur-fast) ease,transform var(--dur-fast) ease,
    color var(--dur-fast) ease}
#front .p:hover{background:var(--fill-2);transform:translateY(-1px);
  color:var(--ink)}
#front .p:active{transform:none}
#front .p b{font-weight:560;color:var(--ink)}
#front .p.crit{border-color:var(--ink4);background:var(--content)}
#front .p em{color:var(--ink3);font-style:normal;font-variant-numeric:tabular-nums}

.bar-controls{display:flex;flex-wrap:wrap;gap:8px;align-items:center;
  padding:0 2px 10px}
section[data-view]{display:none}
section[data-view].on{display:block;animation:rise var(--dur) var(--ease)}
@keyframes rise{from{opacity:0;transform:translateY(4px)}
                to{opacity:1;transform:none}}

/* ── timeline: one canvas, and the frame it lives in ─────────────────────── */
#mini{display:block;width:100%;height:40px;border:.5px solid var(--sep);
  border-radius:var(--r-lg) var(--r-lg) 0 0;border-bottom:none;
  background:var(--sunk);cursor:crosshair}
#frame{position:relative;border:.5px solid var(--sep);
  border-radius:0 0 var(--r-lg) var(--r-lg);background:var(--content);
  overflow:hidden;box-shadow:var(--shadow)}
#plot{position:relative;height:min(70vh,calc(100vh - 330px));min-height:280px}
#cv{position:absolute;inset:0;width:100%;height:100%;display:block}
/* the scroller is a transparent sheet over the canvas: native momentum,
   native scrollbars, native overscroll — the canvas just reads its offsets */
#scroll{position:absolute;inset:0;overflow:auto;overscroll-behavior-x:contain;
  outline:none}
#scroll:focus-visible{box-shadow:inset 0 0 0 2px var(--ink3)}
#spacer{width:1px;height:1px}
#empty{position:absolute;inset:44px 0 0 0;display:none;flex-direction:column;
  gap:10px;align-items:center;justify-content:center;color:var(--ink3);
  font-size:13px;z-index:5;text-align:center;padding:0 20px}
#legend{display:flex;flex-wrap:wrap;gap:4px 10px;font-size:11.5px;
  color:var(--ink2);padding:10px 0 0;align-items:center}
#legend .lnk{display:flex;align-items:center;gap:6px;padding:2px 7px}
#legend .lnk.on{background:var(--fill-2);color:var(--ink)}
#legend i{display:inline-block;width:8px;height:8px;border-radius:3px;
  flex:none}
#legend i.ring{background:transparent !important;
  box-shadow:inset 0 0 0 1.5px currentColor}
#legend i.crit{background:transparent;box-shadow:inset 0 0 0 1.5px var(--crit)}
#legend b{display:inline-block;width:10px;height:2px;background:var(--ink);
  border-radius:1px;flex:none}
#legend .keys{color:var(--ink3)}
#note{margin-top:10px;color:var(--ink3);font-size:11.5px;padding:0 2px}
kbd{font:10.5px ui-monospace,SFMono-Regular,monospace;background:var(--fill);
  border-radius:4px;padding:1.5px 5px;color:var(--ink2)}

/* ── board ──────────────────────────────────────────────────────────────── */
#board{display:flex;gap:12px;overflow-x:auto;padding:2px 2px 10px;
  align-items:flex-start}
.col{flex:0 0 262px;background:var(--content);border:.5px solid var(--sep);
  border-radius:var(--r-lg);display:flex;flex-direction:column;
  max-height:calc(100vh - 250px);box-shadow:var(--shadow);
  transition:box-shadow var(--dur-fast) ease,border-color var(--dur-fast) ease,
    flex-basis var(--dur) var(--ease),opacity var(--dur-fast) ease}
.col.over{border-color:var(--ink3);
  box-shadow:0 0 0 3px var(--accent-wash),var(--shadow)}
.col.bare{flex:0 0 150px;opacity:.66}
.col.bare:hover,.col.bare.over{opacity:1}
.col h3{font-size:11px;font-weight:620;padding:4px 4px 6px;margin:6px 8px 2px;
  display:flex;align-items:center;gap:7px;text-transform:uppercase;
  letter-spacing:.045em;color:var(--ink2);border-radius:var(--r-xs);
  cursor:pointer;transition:background var(--dur-fast) ease}
.col h3:hover{background:var(--hover);color:var(--ink)}
.col h3 i{width:8px;height:8px;border-radius:3px;flex:none}
.col h3 i.ring{background:transparent !important;
  box-shadow:inset 0 0 0 1.5px currentColor}
.col h3 .n{margin-left:auto;color:var(--ink3);font-weight:530;
  letter-spacing:normal;text-transform:none;font-variant-numeric:tabular-nums}
.col .cards{overflow-y:auto;padding:0 8px 8px;display:flex;
  flex-direction:column;gap:6px}
.card{background:var(--content-2);border:.5px solid var(--sep-2);
  border-radius:var(--r-md);padding:8px 10px;font-size:12px;cursor:grab;
  line-height:1.4;transition:transform var(--dur-fast) var(--ease),
    box-shadow var(--dur-fast) ease,border-color var(--dur-fast) ease}
.card:hover{border-color:var(--sep);box-shadow:var(--shadow);
  transform:translateY(-1px)}
.card:active{cursor:grabbing}
.card.drag{opacity:.35;transform:scale(.98)}
.card .t{font-weight:530;overflow:hidden;text-overflow:ellipsis;
  display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical}
.card .m{color:var(--ink3);margin-top:5px;display:flex;gap:7px;
  font-size:11px;font-variant-numeric:tabular-nums;align-items:center}
.card .m .chip{background:var(--fill);border-radius:var(--r-xs);padding:0 5px}
.card .star{color:var(--ink)}

/* ── list ───────────────────────────────────────────────────────────────── */
#listbar{display:flex;gap:8px;align-items:center;margin:0 2px 10px;
  flex-wrap:wrap}
#listbar .n{color:var(--ink3);font-size:12px}
/* a filter you arrived at by clicking a number, and can drop by clicking it */
.tokens{display:flex;gap:6px;align-items:center}
.token{display:flex;gap:6px;align-items:center;background:var(--fill);
  border:.5px solid transparent;border-radius:99px;padding:3px 6px 3px 10px;
  font-size:11.5px;color:var(--ink2);cursor:pointer;
  transition:background var(--dur-fast) ease}
.token:hover{background:var(--fill-2);color:var(--ink)}
.token b{font-weight:590;color:var(--ink)}
.token .x{color:var(--ink3);font-size:10px}
#list{background:var(--content);border:.5px solid var(--sep);
  border-radius:var(--r-lg);overflow:hidden;box-shadow:var(--shadow)}
#list table{width:100%;border-collapse:separate;border-spacing:0}
#list th{cursor:pointer;user-select:none;white-space:nowrap;
  position:sticky;top:0;z-index:2;background:var(--glass);
  backdrop-filter:saturate(180%) blur(20px);
  -webkit-backdrop-filter:saturate(180%) blur(20px);
  border-bottom:.5px solid var(--sep);font-size:11px;font-weight:590;
  color:var(--ink3);text-transform:uppercase;letter-spacing:.04em;
  padding:9px 12px;text-align:left}
#list th:hover{color:var(--ink2)}
#list th.by{color:var(--ink)}
#list td{padding:6px 12px;border-bottom:.5px solid var(--sep-2);
  font-variant-numeric:tabular-nums;font-size:12px}
#list tbody tr:last-child td{border-bottom:none}
#list tr.r{cursor:pointer}
#list tr.r:hover td{background:var(--hover)}
#list td i{display:inline-block;width:8px;height:8px;border-radius:3px;
  margin-right:8px}
#list td i.ring{background:transparent !important;
  box-shadow:inset 0 0 0 1.5px currentColor}
#list td .st{color:var(--ink2)}
#list td .st.warn{color:var(--warn)}
#list td .st.danger{color:var(--danger)}
#list .none{padding:26px;text-align:center;color:var(--ink3);font-size:12.5px}

/* ── asks: the board waiting on a person, and the place to answer ───────── */
#asks{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(430px,1fr));
  align-items:start}
.ask2{background:var(--content);border:.5px solid var(--sep);
  border-radius:var(--r-lg);box-shadow:var(--shadow);overflow:hidden;
  transition:opacity var(--dur) var(--ease),transform var(--dur) var(--ease)}
.ask2.gone{opacity:0;transform:scale(.97)}
.ask2 .hd{display:flex;gap:9px;align-items:flex-start;padding:12px 14px 8px;
  cursor:pointer}
.ask2 .hd:hover .ttl{text-decoration:underline;text-decoration-color:var(--ink4)}
.ask2 .ttl{font-size:13.5px;font-weight:600;letter-spacing:-.01em;flex:1;
  min-width:0}
.ask2 .rel{font:10.5px ui-monospace,SFMono-Regular,monospace;color:var(--ink3);
  margin-top:3px}
.ask2 .flag{flex:none;font-size:10px;font-weight:620;text-transform:uppercase;
  letter-spacing:.05em;border-radius:99px;padding:2px 8px;
  background:var(--warn-wash);color:var(--warn)}
.ask2 .flag.blocked{background:var(--danger-wash);color:var(--danger)}
.ask2 .q{margin:0 14px;padding:10px 12px;background:var(--content-2);
  border:.5px solid var(--sep-2);border-radius:var(--r-md);
  white-space:pre-wrap;font:12px/1.6 ui-monospace,SFMono-Regular,monospace;
  color:var(--ink);max-height:280px;overflow:auto}
.ask2 .q.skel{color:var(--ink3);font-style:italic}
.ask2 .foot{padding:10px 14px 12px}
.ask2 textarea{width:100%;background:var(--content);border:.5px solid var(--sep);
  border-radius:var(--r-sm);padding:8px 10px;min-height:76px;resize:vertical;
  font:12.5px/1.5 -apple-system,system-ui,sans-serif;white-space:pre-wrap}
.ask2 .row2{display:flex;gap:8px;align-items:center;margin-top:8px}
.ask2 .row2 .hint{font-size:11px;color:var(--ink3);margin-left:auto}
.blank{background:var(--content);border:.5px solid var(--sep);
  border-radius:var(--r-lg);box-shadow:var(--shadow);padding:34px 20px;
  text-align:center;color:var(--ink3);font-size:12.5px;grid-column:1/-1;
  display:flex;flex-direction:column;gap:10px;align-items:center}
.blank .big{font-size:14px;color:var(--ink2);font-weight:560}

/* ── analytics ──────────────────────────────────────────────────────────── */
#tiles{display:grid;gap:10px;
  grid-template-columns:repeat(auto-fit,minmax(158px,1fr));margin-bottom:12px}
.tile{background:var(--content);border:.5px solid var(--sep);
  border-radius:var(--r-lg);padding:12px 14px;box-shadow:var(--shadow);
  text-align:left;cursor:pointer;display:block;width:100%;
  transition:transform var(--dur-fast) var(--ease),
    box-shadow var(--dur-fast) ease,border-color var(--dur-fast) ease}
.tile:hover{transform:translateY(-1px);border-color:var(--ink4);
  box-shadow:var(--shadow-lg)}
.tile:active{transform:none}
.tile .k{font-size:10.5px;color:var(--ink3);font-weight:590;
  text-transform:uppercase;letter-spacing:.045em}
.tile .v{font-size:26px;font-weight:620;letter-spacing:-.025em;
  font-variant-numeric:tabular-nums;line-height:1.18;margin:2px 0 1px}
.tile.hot .v{color:var(--warn)}
.tile .s{font-size:11.5px;color:var(--ink2)}
#charts{display:grid;gap:12px;
  grid-template-columns:repeat(auto-fit,minmax(360px,1fr))}
.chart{background:var(--content);border:.5px solid var(--sep);
  border-radius:var(--r-lg);padding:14px 16px 16px;box-shadow:var(--shadow)}
.chart h3{font-size:13px;font-weight:600;letter-spacing:-.01em}
.chart p.sub{font-size:11.5px;color:var(--ink3);margin:2px 0 12px;
  line-height:1.45}
.chart .empty{color:var(--ink3);font-size:12px;padding:18px 0;text-align:center}
.brow{display:grid;grid-template-columns:112px 1fr auto;gap:10px;
  align-items:center;font-size:12px;padding:1px 0;border-radius:var(--r-xs);
  cursor:pointer;transition:background var(--dur-fast) ease}
.brow:hover{background:var(--hover)}
.brow .lab{color:var(--ink2);overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap;padding-left:4px}
.brow:hover .lab{color:var(--ink)}
.brow .track{background:var(--fill);border-radius:5px;height:14px;
  position:relative}
.brow .fill{position:absolute;left:0;top:0;bottom:0;border-radius:5px;
  min-width:3px;transition:width var(--dur) var(--ease)}
.brow .val{color:var(--ink2);font-variant-numeric:tabular-nums;
  text-align:right;min-width:66px;font-size:11.5px;padding-right:4px}
.chart svg{display:block;width:100%;overflow:visible}
.chart svg .ax{stroke:var(--sep);stroke-width:1}
.chart svg .lbl{fill:var(--ink3);font-size:10px}
.chart svg .dot{fill:var(--ink);stroke:var(--content);stroke-width:2;
  cursor:pointer}
.chart svg .dot:hover{fill:var(--ink);stroke:var(--ink3)}
.chart svg .ref{stroke:var(--ink3);stroke-dasharray:3 3;stroke-width:1}
.chart svg .line{fill:none;stroke:var(--ink);stroke-width:2;
  stroke-linejoin:round;stroke-linecap:round}
.chart svg .area{fill:var(--ink);opacity:.08}

/* ── memos ──────────────────────────────────────────────────────────────── */
#memos{display:grid;gap:12px;
  grid-template-columns:repeat(auto-fit,minmax(340px,1fr))}
.memo{background:var(--content);border:.5px solid var(--sep);
  border-radius:var(--r-lg);padding:14px 16px;box-shadow:var(--shadow)}
.memo h3{font-size:13px;font-weight:600;margin-bottom:4px;letter-spacing:-.01em}
.memo .f{font-size:11px;color:var(--ink3);margin-bottom:8px;display:flex;
  flex-wrap:wrap;gap:4px 6px;align-items:baseline}
.memo .f b{color:var(--ink2);font-weight:590}
.memo pre{white-space:pre-wrap;font:11.5px/1.55 ui-monospace,SFMono-Regular,
  monospace;color:var(--ink2);max-height:240px;overflow:auto}

/* ── the inspector: a glass sheet, not a page ───────────────────────────── */
#drawer{position:fixed;top:12px;right:12px;bottom:12px;
  width:min(540px,46vw);z-index:40;background:var(--glass);
  backdrop-filter:saturate(180%) blur(30px);
  -webkit-backdrop-filter:saturate(180%) blur(30px);
  border:.5px solid var(--glass-brd);border-radius:14px;
  box-shadow:var(--shadow-lg);display:flex;flex-direction:column;
  transform:translateX(calc(100% + 24px));opacity:0;pointer-events:none;
  transition:transform var(--dur) var(--ease),opacity var(--dur) var(--ease)}
#drawer.open{transform:none;opacity:1;pointer-events:auto}
#dhead{padding:12px 14px 10px;border-bottom:.5px solid var(--sep);display:flex;
  gap:10px;align-items:flex-start}
#dhead .who{flex:1;min-width:0}
#drawer #dtitle{width:100%;background:transparent;border:.5px solid transparent;
  font-size:14.5px;font-weight:610;letter-spacing:-.014em;padding:3px 6px;
  margin-left:-6px;border-radius:var(--r-xs)}
#dtitle:hover{background:var(--fill)}
#dtitle:focus{background:var(--content);border-color:var(--sep)}
#dhead .rel{font:11px ui-monospace,SFMono-Regular,monospace;color:var(--ink3);
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding-left:0}
#dclose{width:26px;height:26px;padding:0;display:flex;align-items:center;
  justify-content:center;border-radius:99px;font-size:11px;color:var(--ink2)}
#dbody{overflow:auto;padding:12px 14px 18px;flex:1}
#drawer h4{font-size:10.5px;font-weight:620;color:var(--ink3);
  margin:16px 0 6px;text-transform:uppercase;letter-spacing:.05em}
#drawer h4:first-child{margin-top:0}
#drawer input[type=text],#drawer textarea,#drawer select,
#drawer input[type=number]{width:100%;background:var(--content);
  border:.5px solid var(--sep);border-radius:var(--r-sm);padding:6px 9px}
#drawer textarea{font:12px/1.6 ui-monospace,SFMono-Regular,monospace;
  resize:vertical;min-height:240px;white-space:pre}
#drawer .fields{display:grid;grid-template-columns:1fr 96px;gap:8px}
#drawer .facts{display:flex;flex-wrap:wrap;gap:5px 14px;font-size:12px;
  color:var(--ink2)}
#drawer .facts b{color:var(--ink);font-weight:590;
  font-variant-numeric:tabular-nums}
#drawer .chips{display:flex;flex-wrap:wrap;gap:5px}
#drawer .chip2{font-size:11.5px;background:var(--fill);border-radius:99px;
  padding:2px 10px;cursor:pointer;border:.5px solid transparent;
  transition:background var(--dur-fast) ease}
#drawer .chip2:hover{background:var(--fill-2);color:var(--ink)}
#drawer .spec{border:.5px solid var(--sep);border-radius:var(--r-sm);
  padding:8px 10px;margin:6px 0;font-size:12px;background:var(--content)}
#drawer .spec .f{font:10.5px ui-monospace,monospace;color:var(--ink3);
  margin-top:2px}
#drawer pre.sec{white-space:pre-wrap;font:11.5px/1.6 ui-monospace,monospace;
  color:var(--ink2);background:var(--content);border:.5px solid var(--sep);
  border-radius:var(--r-sm);padding:9px 11px;max-height:260px;overflow:auto}
.ask{border:.5px solid color-mix(in srgb,var(--warn) 42%,transparent);
  background:var(--warn-wash);border-radius:var(--r-md);padding:11px 12px;
  margin:14px 0}
.ask h5{font-size:10.5px;font-weight:620;color:var(--warn);margin-bottom:6px;
  text-transform:uppercase;letter-spacing:.05em}
.ask pre{white-space:pre-wrap;font:12px/1.55 ui-monospace,monospace;
  color:var(--ink);margin-bottom:9px}
#drawer .say{width:100%;min-height:70px;
  font:12.5px/1.5 -apple-system,system-ui,sans-serif !important;
  white-space:pre-wrap !important}
#drawer .row2{display:flex;gap:8px;align-items:center;margin-top:7px}
#drawer .row2 .hint{font-size:11px;color:var(--ink3);margin-left:auto}
#dsave{display:flex;gap:8px;align-items:center;padding:10px 14px;
  border-top:.5px solid var(--sep)}
#dsave .msg{font-size:11.5px;color:var(--ink3);margin-left:auto}
#dlinks a{color:var(--ink);font-size:12px;text-decoration:underline;
  text-decoration-color:var(--ink4);text-underline-offset:2px;margin-right:14px}
#dlinks a:hover{text-decoration-color:var(--ink)}

/* ── overlay + toast ────────────────────────────────────────────────────── */
#newbox{position:fixed;inset:0;z-index:50;background:rgba(0,0,0,.28);
  backdrop-filter:blur(2px);display:none;align-items:flex-start;
  justify-content:center;padding-top:14vh}
#newbox.on{display:flex;animation:fade var(--dur-fast) ease}
@keyframes fade{from{opacity:0}to{opacity:1}}
#newbox .card2{background:var(--glass);
  backdrop-filter:saturate(180%) blur(30px);
  -webkit-backdrop-filter:saturate(180%) blur(30px);
  border:.5px solid var(--glass-brd);border-radius:14px;padding:18px;
  width:min(580px,92vw);box-shadow:var(--shadow-lg);
  animation:pop var(--dur) var(--ease)}
@keyframes pop{from{opacity:0;transform:translateY(-8px) scale(.98)}
               to{opacity:1;transform:none}}
#newbox h3{font-size:15px;font-weight:620;margin-bottom:12px;
  letter-spacing:-.014em}
#newbox input,#newbox textarea{width:100%;background:var(--content);
  border:.5px solid var(--sep);border-radius:var(--r-sm);padding:7px 10px;
  margin-bottom:8px}
#newbox textarea{min-height:130px;
  font:12px/1.6 ui-monospace,SFMono-Regular,monospace}
#toast{position:fixed;left:50%;bottom:26px;transform:translate(-50%,14px);
  z-index:60;background:var(--glass);
  backdrop-filter:saturate(180%) blur(24px);
  -webkit-backdrop-filter:saturate(180%) blur(24px);
  border:.5px solid var(--glass-brd);border-radius:99px;padding:8px 16px;
  font-size:12.5px;font-weight:500;box-shadow:var(--shadow-lg);opacity:0;
  pointer-events:none;transition:opacity var(--dur) var(--ease),
    transform var(--dur) var(--ease)}
#toast.on{opacity:1;transform:translate(-50%,0)}
#toast .ok{color:var(--ink);margin-right:6px}
#toast .no{color:var(--danger);margin-right:6px}

#tip{position:fixed;z-index:70;display:none;max-width:390px;
  background:var(--glass);backdrop-filter:saturate(180%) blur(24px);
  -webkit-backdrop-filter:saturate(180%) blur(24px);
  border:.5px solid var(--glass-brd);border-radius:var(--r-md);
  box-shadow:var(--shadow-lg);padding:10px 12px;font-size:11.5px;
  line-height:1.5;pointer-events:none}
#tip .t{font-weight:610;margin-bottom:3px;letter-spacing:-.01em}
#tip .r{color:var(--ink2)}
#tip .k{color:var(--ink3)}
#tip .warn{color:var(--warn)}
</style>
</head>
<body>
<header id="titlebar">
  <div class="ident"><h1>__TITLE__</h1><span id="sub">the plan</span></div>
  <nav id="views" role="tablist" aria-label="views">
    <span id="segpill" aria-hidden="true"></span>
    <button data-v="timeline" role="tab" class="on" aria-selected="true">timeline</button
    ><button data-v="board" role="tab">board</button
    ><button data-v="asks" role="tab">asks<span class="badge" id="askbadge"></span></button
    ><button data-v="list" role="tab">list</button
    ><button data-v="analytics" role="tab">analytics</button
    ><button data-v="memos" role="tab">memos</button>
  </nav>
  <div class="right">
    <button id="newprd" class="primary" title="write a PRD (N)">＋ PRD</button>
  </div>
</header>
<div id="statsbar"><span id="stats"></span><span id="inview"></span></div>
<div id="purpose"></div>
<div id="front"></div>
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
<canvas id="mini" aria-hidden="true"></canvas>
<div id="frame">
  <div id="plot">
    <canvas id="cv" role="img"></canvas>
    <div id="scroll" tabindex="0" aria-label="the plan — arrow keys move the
      selection, return opens it, the list view is the same data as a table">
      <div id="spacer"></div>
    </div>
    <div id="empty"></div>
  </div>
</div>
<div id="legend"></div>
<div id="note"></div>
</section>
<section data-view="board"><div id="board"></div></section>
<section data-view="asks"><div id="asks"></div></section>
<section data-view="list">
  <div id="listbar"><input type="search" id="lq" placeholder="filter  /">
    <span class="tokens" id="ltokens"></span>
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
    <button id="ncreate" class="primary">write it</button>
    <button id="ncancel">cancel</button>
  </div>
</div></div>
<div id="tip"></div>
<div id="toast" role="status" aria-live="polite"></div>
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
/* ═══════════════════════════════════════════════════════════════════════════
   The page has one datum — the enriched payload — and five readings of it.
   Everything below is arranged in that order: the data and the tokens, the
   router that makes every number a door, the canvas that draws the plan, the
   inspector, and then the four other views.
   ═══════════════════════════════════════════════════════════════════════════ */

let DATA = __PAYLOAD__;
let CPM = DATA.cpm;

/* States are ink weights, not hues. `ring` draws the mark hollow: a PRD in
   `refine` is an open question about scope, a `blocked` one is a wall — both
   are outlines, because neither is work in progress. */
const STATES = {
  open:      {tok:"st-open"},
  refine:    {tok:"st-open",      ring:true},
  analyzing: {tok:"st-analyzing"},
  specced:   {tok:"st-specced"},
  claimed:   {tok:"st-claimed"},
  question:  {tok:"warn"},
  blocked:   {tok:"danger",       ring:true},
  failed:    {tok:"danger"},
};
const stTok = s => (STATES[s] || {}).tok ||
  (s === "done" ? "st-done" : "ink3");
const stRing = s => !!(STATES[s] || {}).ring;
const stVar = s => "var(--" + stTok(s) + ")";
const HOT = {question:1, blocked:1, failed:1};   // the states with a hue

const $ = id => document.getElementById(id);
const cv = $("cv"), scroll = $("scroll"), spacer = $("spacer"),
      plot = $("plot"), tip = $("tip"), mini = $("mini");
const ctx = cv.getContext("2d"), mctx = mini.getContext("2d");
const ROW = 26, HEAD = 44, PAD = 5, MS = 86400000;
let LEFT = Math.min(360, Math.max(210, Math.round(innerWidth * 0.24)));
let dpr = 1;

/* ── tokens ───────────────────────────────────────────────────────────────
   The stylesheet is the only place a colour is written down. The canvas reads
   the resolved values out of it once, and again whenever the theme changes —
   so light, dark, more-contrast and reduced-transparency all just work, and
   nothing is defined twice. */
const TOKENS = ["bg","content","content-2","sunk","ink","ink2","ink3","ink4",
  "fill","fill-2","sep","sep-2","hover","sel","accent","accent-ink",
  "accent-wash","warn","danger","st-open","st-analyzing","st-specced",
  "st-claimed","st-done","crit","float","link","grid","gridw","axis","wash",
  "hi","lo"];
let T = {};
function readTokens() {
  const cs = getComputedStyle(document.documentElement);
  for (const k of TOKENS) T[k] = cs.getPropertyValue("--" + k).trim();
}
readTokens();
const col = s => T[stTok(s)];
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  readTokens(); draw(); drawMini(); if (view !== "timeline") repaintView();
});

const a = DATA.anchor.split("-").map(Number);
const anchor = new Date(a[0], a[1] - 1, a[2]);
const nowDay = () => (Date.now() - anchor.getTime()) / MS;
const dayDate = d => new Date(a[0], a[1] - 1, a[2] + Math.floor(d));
const fmtD = d => dayDate(d).toLocaleDateString(undefined,
  {month:"short", day:"numeric"});
const fmtH = h => h >= 40 ? Math.round(h) + "h"
  : (Math.round(h * 10) / 10 + "h").replace(".0h", "h");
const esc = s => String(s).replace(/[&<>"']/g,
  c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

let tasks = [], byRel = new Map(), ALL = [], allByRel = new Map(), HIST = [];
function hydrate() {
  CPM = DATA.cpm;
  tasks = DATA.tasks;
  byRel = new Map(tasks.map(t => [t.rel, t]));
  for (const t of tasks) {
    t.deps = (t.needs || []).map(r => byRel.get(r)).filter(Boolean);
    t.feeds = (t.blocks || []).map(r => byRel.get(r)).filter(Boolean);
  }
  ALL = DATA.all || [];
  allByRel = new Map(ALL.map(r => [r.rel, r]));
  HIST = DATA.history || [];
}
hydrate();

/* ── two axes, one geometry ───────────────────────────────────────────────
   vision: hours along the critical path. 0 is now, the right edge is the
   vision reached, and a bar's position is the soonest it could possibly run.
   dates:  the worker-limited calendar `plan` computed, for a human who wants
   a date. Everything downstream of MODE — grid, bars, minimap, arrows —
   reads u0/u1 and never knows which one it is drawing. */
let MODE, mode = "vision", M, ppu;
function remode() {
  MODE = {
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
  M = MODE[mode];
}
remode();
ppu = M.ppu;
const span = () => M.hi - M.lo;
const x = u => LEFT + (u - M.lo) * ppu - scroll.scrollLeft;

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
let stateSel = new Set();          // set by clicking the legend
let hover = -1;                    // row index under the pointer

$("grp").innerHTML = Object.entries(GROUPS)
  .map(([k, g]) => `<option value="${k}">${g.label}</option>`).join("");
$("grp").value = groupBy;

function matches(t) {
  if (critOnly && !t.critical) return false;
  if (readyOnly && !t.ready) return false;
  if (stateSel.size && !stateSel.has(t.state)) return false;
  if (!filter) return true;
  const f = filter.toLowerCase();
  return t.rel.toLowerCase().includes(f) || t.state.includes(f) ||
    (t.title || "").toLowerCase().includes(f) || ("wave " + t.wave) === f;
}
const anyFilter = () => filter || critOnly || readyOnly || stateSel.size;

/* ── the row list ─────────────────────────────────────────────────────────
   One flat array, rebuilt on grouping, filter and collapse — never on scroll
   and never on zoom. A row that moves under the pointer as you scroll is what
   makes a big chart unreadable, so the order is stable: group, then earliest
   start, then how much the task unblocks. */
let rows = [];
function build() {
  rows = [];
  const g = GROUPS[groupBy];
  const buckets = new Map();
  for (const t of tasks) {
    if (!matches(t)) continue;
    const k = g.key(t);
    if (!buckets.has(k)) buckets.set(k, []);
    buckets.get(k).push(t);
  }
  for (const k of [...buckets.keys()].sort(g.sort)) {
    const items = buckets.get(k).sort((p, q) =>
      M.u0(p) - M.u0(q) || (q.critical - p.critical) ||
      q.unblocks - p.unblocks || q.est - p.est || p.rel.localeCompare(q.rel));
    if (k !== "") {
      rows.push({kind:"group", key:k, n:items.length,
        sum:items.reduce((s, t) => s + t.est, 0),
        ncrit:items.filter(t => t.critical).length,
        lo:Math.min(...items.map(M.u0)), hi:Math.max(...items.map(M.u1)),
        open:!collapsed.has(k)});
      if (collapsed.has(k)) continue;
    }
    for (const t of items) rows.push({kind:"task", t:t, key:k});
  }
  const hidden = tasks.length - tasks.filter(matches).length;
  $("inview").innerHTML = tasks.length + " scheduled" +
    (hidden ? lnk(`${hidden} filtered out`, {clear:1}, "clear every filter",
                  "· ") : "") +
    (collapsed.size ? lnk(`${collapsed.size} collapsed`, {expand:1},
                          "open every group", "· ") : "");
  $("empty").style.display = rows.length ? "none" : "flex";
  $("empty").innerHTML = tasks.length
    ? '<div>nothing matches</div>' + btn("clear the filter", {clear:1})
    : '<div>nothing scheduled — run <kbd>pearde plan</kbd></div>';
  place();
}

/* ── the router: every number is a door ───────────────────────────────────
   One function moves the page: which view, which filter, which PRD. Chips,
   counts, swatches, bars and column heads all describe their destination as
   data and hand it here, so there is exactly one place where navigation
   happens and exactly one way to write a link. */
function lnk(html, dest, title, before) {
  return (before || "") + '<button class="lnk' +
    (dest.hot ? " hot" : "") + '" data-go="' + esc(JSON.stringify(dest)) +
    '"' + (title ? ' title="' + esc(title) + '"' : "") + ">" + html +
    "</button>";
}
function btn(label, dest, cls) {
  return '<button class="act ' + (cls || "") + '" data-go="' +
    esc(JSON.stringify(dest)) + '">' + label + "</button>";
}
document.addEventListener("click", e => {
  const el = e.target.closest("[data-go]");
  if (!el) return;
  e.preventDefault();
  go(JSON.parse(el.dataset.go));
});

/* A destination is any subset of:
     view   timeline | board | asks | list | analytics | memos
     prd    a rel — opens the inspector, and focuses the row if it has one
     state  a state, or the pseudo-states live / parked / hot
     board  a member board's name
     q      free text for the view's own filter
     crit ready group mode   the timeline's own controls
     clear expand            the two undo-doors filters need           */
function go(d) {
  if (d.clear) {
    filter = ""; $("q").value = ""; critOnly = readyOnly = false;
    stateSel.clear(); syncToggles(); build();
    return toast("filters cleared");
  }
  if (d.expand) { collapsed.clear(); build(); return; }
  if (d.mode && d.mode !== mode) setMode(d.mode);
  if (d.group && GROUPS[d.group]) {
    groupBy = d.group; $("grp").value = d.group; collapsed.clear(); build();
  }
  if (d.crit !== undefined) { critOnly = !!d.crit; syncToggles(); build(); }
  if (d.ready !== undefined) { readyOnly = !!d.ready; syncToggles(); build(); }
  if (d.tstate !== undefined) {                    // the legend's own filter
    if (d.tstate === null) stateSel.clear();
    else stateSel.has(d.tstate) ? stateSel.delete(d.tstate)
                                : stateSel.add(d.tstate);
    build(); drawLegend();
  }
  if (d.state !== undefined) { listState = d.state; }
  if (d.board !== undefined) { listBoard = d.board; }
  if (d.q !== undefined) {
    if ((d.view || view) === "list") { listQ = d.q; $("lq").value = d.q; }
    else { filter = d.q; $("q").value = d.q; build(); }
  }
  if (d.view) setView(d.view);
  else repaintView();
  if (d.prd) {
    const t = taskFor(d.prd);
    if (t) t.plain || (d.view && d.view !== "timeline")
      ? openDrawer(t) : focusTask(t);
  }
  syncHash();
}

/* ═══ the canvas ══════════════════════════════════════════════════════════
   One surface, drawn virtualised. The frozen task column and the frozen
   header are just draw order — the expensive part of a DOM gantt (a few
   thousand absolutely positioned elements that all re-layout on a zoom) does
   not exist here. Only the rows in front of the reader are ever touched, so
   a 40-row board and a 4000-row board cost the same per frame, and gradients,
   inner highlights and the critical chain's glow are free.

   The scroller is a transparent DOM sheet on top: native momentum, native
   scrollbars, native overscroll. The canvas reads its offsets and never
   invents a scrollbar of its own.                                         */
const FONT = ",BlinkMacSystemFont,'SF Pro Text',system-ui,sans-serif";
const F = {
  cell:  '500 12px -apple-system' + FONT,
  grp:   '620 12px -apple-system' + FONT,
  meta:  '11.5px -apple-system' + FONT,
  tick:  '600 10.5px -apple-system' + FONT,
  small: '530 10px -apple-system' + FONT,
  tag:   '590 10.5px -apple-system' + FONT,
};

function rr(x0, y, w, h, r) {                      // one rounded rect, pathed
  r = Math.max(0, Math.min(r, w / 2, h / 2));
  ctx.beginPath();
  ctx.moveTo(x0 + r, y);
  ctx.arcTo(x0 + w, y, x0 + w, y + h, r);
  ctx.arcTo(x0 + w, y + h, x0, y + h, r);
  ctx.arcTo(x0, y + h, x0, y, r);
  ctx.arcTo(x0, y, x0 + w, y, r);
  ctx.closePath();
}
const hair = 0.5;                                  // a real hairline, any dpr
function line(x1, y1, x2, y2, c, w) {
  ctx.strokeStyle = c; ctx.lineWidth = w || hair;
  ctx.beginPath();
  const sn = (w || hair) < 1.2 ? 0.5 : 0;          // sit on the pixel grid
  ctx.moveTo(Math.round(x1) + (x1 === x2 ? sn : 0), Math.round(y1) + (y1 === y2 ? sn : 0));
  ctx.lineTo(Math.round(x2) + (x1 === x2 ? sn : 0), Math.round(y2) + (y1 === y2 ? sn : 0));
  ctx.stroke();
}
const tw = new Map();                              // measured-width cache
function fit(s, max, font) {
  s = String(s == null ? "" : s);
  const k = font + "|" + s + "|" + Math.round(max);
  if (tw.has(k)) return tw.get(k);
  ctx.font = font;
  let out = s;
  if (ctx.measureText(s).width > max) {
    let lo = 0, hi = s.length;
    while (lo < hi) {
      const m = (lo + hi + 1) >> 1;
      if (ctx.measureText(s.slice(0, m) + "…").width <= max) lo = m; else hi = m - 1;
    }
    out = s.slice(0, lo) + "…";
  }
  if (tw.size > 4000) tw.clear();
  tw.set(k, out);
  return out;
}
function text(s, x0, y, c, font, right) {
  ctx.font = font; ctx.fillStyle = c;
  ctx.textAlign = right ? "right" : "left";
  ctx.textBaseline = "middle";
  ctx.fillText(s, x0, y);
  ctx.textAlign = "left";
}

/* a bar: the fill, a highlight down its top, a shade at its foot, and — for
   the chain that sets the finish — an ink outline with a glow behind it */
function drawBar(x0, w, y, h, c, o) {
  o = o || {};
  const r = Math.min(5, h / 2);
  ctx.save();
  if (o.dim) ctx.globalAlpha = 0.5;
  if (o.ring) {
    rr(x0 + 0.75, y + 0.75, Math.max(2, w - 1.5), h - 1.5, r);
    ctx.strokeStyle = c; ctx.lineWidth = 1.5; ctx.stroke();
  } else {
    rr(x0, y, w, h, r);
    if (!o.flat) {
      ctx.shadowColor = T.lo; ctx.shadowBlur = 2.5; ctx.shadowOffsetY = 1;
    }
    ctx.fillStyle = c; ctx.fill();
    ctx.shadowColor = "transparent"; ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;
    const g = ctx.createLinearGradient(0, y, 0, y + h);
    g.addColorStop(0, T.hi);
    g.addColorStop(0.5, "rgba(0,0,0,0)");
    g.addColorStop(1, T.lo);
    ctx.fillStyle = g; ctx.fill();
  }
  if (o.crit) {
    rr(x0 - 0.5, y - 0.5, w + 1, h + 1, r + 0.5);
    ctx.shadowColor = T.crit; ctx.shadowBlur = 6;
    ctx.strokeStyle = T.crit; ctx.lineWidth = 1.25; ctx.stroke();
    ctx.shadowColor = "transparent"; ctx.shadowBlur = 0;
  }
  ctx.restore();
}

function resize() {
  dpr = Math.min(3, window.devicePixelRatio || 1);
  const W = plot.clientWidth, H = plot.clientHeight;
  cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
  cv.style.width = W + "px"; cv.style.height = H + "px";
  mini.width = Math.round((mini.clientWidth || 1) * dpr);
  mini.height = Math.round(40 * dpr);
  tw.clear();
}

/* place = the geometry changed (zoom, mode, row count, column width): tell
   the scroller how big the world is, then draw it */
function place() {
  spacer.style.width = Math.max(plot.clientWidth,
    LEFT + span() * ppu + 24) + "px";
  spacer.style.height = (HEAD + PAD + rows.length * ROW + 14) + "px";
  draw(); drawMini();
}

let queued = false;
function schedule() {
  if (queued) return;
  queued = true;
  requestAnimationFrame(() => { queued = false; draw(); syncWin(); });
}

function niceStep(pxPerUnit, unit) {
  const want = 90 / pxPerUnit;                       // ~90px between labels
  const steps = unit === "h" ? [.5,1,2,4,8,12,24,48,96,168,336]
                             : [1,2,7,14,28,56,112];
  return steps.find(s => s >= want) || steps[steps.length - 1];
}

function draw() {
  const W = plot.clientWidth, H = plot.clientHeight;
  if (!W || !H) return;
  const sx = scroll.scrollLeft, sy = scroll.scrollTop;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = T.content; ctx.fillRect(0, 0, W, H);
  const rowY = i => HEAD + PAD + i * ROW - sy;
  const first = Math.max(0, Math.floor((sy - PAD) / ROW));
  const last = Math.min(rows.length - 1,
                        Math.ceil((sy + H - HEAD - PAD) / ROW));
  const kin = selected
    ? new Set([selected, ...selected.deps, ...selected.feeds]) : null;

  /* 1 — the field: washes, then grid */
  ctx.save();
  ctx.beginPath(); ctx.rect(LEFT, 0, W - LEFT, H); ctx.clip();
  const step = niceStep(ppu, M.unit);
  if (mode === "vision") {
    // the waves are read off the header pills; down here they are one
    // hairline apiece, so the field stays a field and not a barcode
    for (const [w, [lo, hi]] of Object.entries(CPM.waves || {}))
      line(x(hi), HEAD, x(hi), H, T.gridw);
    for (let v = 0; v <= M.hi + step; v += step) {
      const wide = Math.abs(v % (step * 4)) < 1e-9;
      line(x(v), HEAD, x(v), H, wide ? T.gridw : T.grid);
    }
  } else {
    for (let d = Math.floor(M.lo); d <= M.hi; d++) {
      const dow = dayDate(d).getDay();
      if (dow === 6) { ctx.fillStyle = T.wash;
                       ctx.fillRect(x(d), HEAD, 2 * ppu, H); }
      if (ppu >= 24 || dow === 1)
        line(x(d), HEAD, x(d), H, dow === 1 ? T.gridw : T.grid);
    }
  }
  ctx.restore();

  /* 2 — row bands: hover and selection run the full width, under everything */
  for (let i = first; i <= last; i++) {
    const r = rows[i], y = rowY(i);
    if (!r || y + ROW < HEAD) continue;
    const sel = r.kind === "task" && r.t === selected;
    if (r.kind === "group") ctx.fillStyle = T["content-2"];
    else if (sel) ctx.fillStyle = T.sel;
    else if (i === hover) ctx.fillStyle = T.hover;
    else continue;
    ctx.fillRect(0, Math.max(HEAD, y), W, ROW - Math.max(0, HEAD - y));
  }

  /* 3 — the work itself */
  ctx.save();
  ctx.beginPath(); ctx.rect(LEFT, HEAD, W - LEFT, H - HEAD); ctx.clip();
  for (let i = first; i <= last; i++) {
    const r = rows[i], y = rowY(i);
    if (!r || y + ROW < HEAD) continue;
    if (r.kind === "group") {
      const x0 = x(r.lo), w = Math.max(5, (r.hi - r.lo) * ppu);
      drawBar(x0, w, y + 9, 8, T["st-done"], {flat:true});
      continue;
    }
    const t = r.t, dim = kin ? !kin.has(t) : false;
    const s = M.u0(t), e = M.u1(t);
    const x0 = x(s), w = Math.max(5, (e - s) * ppu);
    // float: how far this bar may slide before it becomes critical. Drawn
    // only in vision mode — on a calendar the worker slots already spent it.
    const slack = mode === "vision" ? t.slack : 0;
    if (slack > 0.05) {
      ctx.save();
      ctx.globalAlpha = dim ? 0.2 : (t === selected || i === hover ? 0.95 : 0.4);
      ctx.fillStyle = T.float;
      rr(x(e), y + 12, Math.max(2, slack * ppu), 2, 1); ctx.fill();
      ctx.restore();
    }
    drawBar(x0, w, y + 6, 14, col(t.state),
            {ring:stRing(t.state), crit:t.critical, dim:dim});
  }
  if (selected) arrows(rowY);
  ctx.restore();

  /* 4 — now and the vision, over the field, under the chrome */
  const nowU = mode === "vision" ? 0 : nowDay();
  const visU = mode === "vision" ? CPM.length
    : Math.max(...tasks.map(t => t.endDay), 0);
  ctx.save();
  ctx.beginPath(); ctx.rect(LEFT, HEAD, W - LEFT, H - HEAD); ctx.clip();
  ctx.setLineDash([3, 3]);
  line(x(nowU), HEAD, x(nowU), H, T.ink3, 1.25);
  ctx.setLineDash([]);
  line(x(visU), HEAD, x(visU), H, T.ink, 1.5);
  ctx.restore();

  /* 5 — the header: waves as bands, then the scale */
  ctx.save();
  ctx.beginPath(); ctx.rect(LEFT, 0, W - LEFT, HEAD); ctx.clip();
  ctx.fillStyle = T.content; ctx.fillRect(LEFT, 0, W - LEFT, HEAD);
  if (mode === "vision") {
    for (const [w, [lo, hi]] of Object.entries(CPM.waves || {})) {
      const x0 = x(lo), wpx = Math.max(18, (hi - lo) * ppu);
      rr(x0, 6, wpx, 16, 5); ctx.fillStyle = T.fill; ctx.fill();
      if (wpx >= 52)
        text(fit("wave " + w, wpx - 12, F.small), x0 + 6, 14.5, T.ink2, F.small);
      else if (wpx >= 26) text("w" + w, x0 + 5, 14.5, T.ink3, F.small);
    }
    for (let v = 0; v <= M.hi + step; v += step) {
      text(v === 0 ? "now" : "+" + fmtH(v), x(v) + 4, 33, T.ink3, F.tick);
      line(x(v), 26, x(v), HEAD, T.grid);
    }
  } else {
    let m = -1;
    const everyDay = ppu >= 24, weekly = ppu >= 5;
    for (let d = Math.floor(M.lo); d <= M.hi; d++) {
      const dt = dayDate(d), dow = dt.getDay();
      if (dt.getMonth() !== m) {
        m = dt.getMonth();
        line(x(d), 4, x(d), 18, T.axis);
        text(dt.toLocaleDateString(undefined, {month:"short", year:"numeric"}),
             x(d) + 5, 12, T.ink2, F.tick);
      }
      if (everyDay || (weekly && dow === 1))
        text(everyDay ? String(dt.getDate())
             : dt.toLocaleDateString(undefined, {month:"short", day:"numeric"}),
             x(d) + 4, 33, T.ink3, F.tick);
    }
  }
  // the two tags that name the ends of the axis
  if (mode !== "vision") tag("now · " + new Date().toLocaleDateString(undefined,
      {weekday:"short", month:"short", day:"numeric"}), x(nowU), "mid");
  tag(mode === "vision" ? "vision · " + fmtH(CPM.length) + " of work in front"
      : "vision · " + fmtD(visU), x(visU), "end");
  ctx.restore();
  line(LEFT, HEAD, W, HEAD, T.sep);

  /* 6 — the frozen column, and the shadow that says it is frozen */
  ctx.save();
  ctx.beginPath(); ctx.rect(0, 0, LEFT, H); ctx.clip();
  ctx.fillStyle = T.content; ctx.fillRect(0, 0, LEFT, H);
  for (let i = first; i <= last; i++) {
    const r = rows[i], y = rowY(i);
    if (!r || y + ROW < HEAD) continue;
    const mid = y + ROW / 2;
    if (r.kind === "group") {
      ctx.fillStyle = T["content-2"]; ctx.fillRect(0, Math.max(HEAD, y), LEFT,
        ROW - Math.max(0, HEAD - y));
      text(r.open ? "▾" : "▸", 11, mid, T.ink3, F.small);
      const meta = r.n + " · " + fmtH(r.sum) + (r.ncrit ? " · " + r.ncrit + "★" : "");
      ctx.font = F.meta;
      const mw = ctx.measureText(meta).width;
      text(fit(r.key, LEFT - 34 - mw, F.grp), 26, mid, T.ink, F.grp);
      text(meta, LEFT - 12, mid, T.ink3, F.meta, true);
      continue;
    }
    const t = r.t, dim = kin ? !kin.has(t) : false;
    ctx.save();
    if (dim) ctx.globalAlpha = 0.62;
    const sel = t === selected;
    if (sel) { ctx.fillStyle = T.sel; ctx.fillRect(0, Math.max(HEAD, y), LEFT,
      ROW - Math.max(0, HEAD - y)); }
    else if (i === hover) { ctx.fillStyle = T.hover;
      ctx.fillRect(0, Math.max(HEAD, y), LEFT, ROW - Math.max(0, HEAD - y)); }
    let cx = 12;
    if (stRing(t.state)) {
      rr(cx + 0.75, mid - 3.25, 6.5, 6.5, 2.5);
      ctx.strokeStyle = col(t.state); ctx.lineWidth = 1.5; ctx.stroke();
    } else {
      rr(cx, mid - 4, 8, 8, 3); ctx.fillStyle = col(t.state); ctx.fill();
    }
    cx += 15;
    if (t.critical) { text("★", cx, mid, T.ink, F.small); cx += 12; }
    const meta = fmtH(t.est) + (t.unblocks ? " ▸" + fmtH(t.unblocks) : "");
    ctx.font = F.meta;
    const mw = ctx.measureText(meta).width;
    text(fit(t.name, LEFT - cx - mw - 20, F.cell), cx, mid,
         sel ? T.ink : T.ink, F.cell);
    text(meta, LEFT - 12, mid, T.ink3, F.meta, true);
    ctx.restore();
    if (y + ROW > HEAD) line(12, y + ROW, LEFT, y + ROW, T["sep-2"]);
  }
  ctx.fillStyle = T.content; ctx.fillRect(0, 0, LEFT, HEAD);
  text("TASK", 12, HEAD / 2, T.ink3, F.small);
  ctx.restore();
  line(LEFT, 0, LEFT, H, T.sep);
  if (sx > 0) {
    const g = ctx.createLinearGradient(LEFT, 0, LEFT + 12, 0);
    g.addColorStop(0, T.lo); g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g; ctx.fillRect(LEFT, HEAD, 12, H - HEAD);
  }
  if (sy > 2) {
    const g = ctx.createLinearGradient(0, HEAD, 0, HEAD + 10);
    g.addColorStop(0, T.lo); g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g; ctx.fillRect(0, HEAD, W, 10);
  }
  cv.setAttribute("aria-label", rows.length + " rows — " +
    tasks.length + " scheduled PRDs, " + fmtH(CPM.length) +
    " of work to the vision. The list view is the same data as a table.");
}

/* a pill on the header: "now", "vision" */
function tag(label, atX, align) {
  ctx.font = F.tag;
  const w = ctx.measureText(label).width + 16;
  let x0 = atX - (align === "mid" ? w / 2 : align === "end" ? w : 0);
  x0 = Math.max(LEFT + 4, Math.min(x0, plot.clientWidth - w - 4));
  rr(x0, 4, w, 17, 8.5);
  ctx.fillStyle = T.accent; ctx.fill();
  text(label, x0 + 8, 13, T["accent-ink"], F.tag);
}

/* arrows for the selected row only — never the whole web. The web is what
   makes a dependency graph unreadable; one row's kin is a fact you can hold. */
function arrows(rowY) {
  const at = new Map();
  rows.forEach((r, i) => { if (r.kind === "task") at.set(r.t, i); });
  const arrow = (from, to) => {
    if (!at.has(from) || !at.has(to)) return;
    const both = from.critical && to.critical;
    const c = both ? T.crit : T.link;
    const x1 = x(M.u1(from)), y1 = rowY(at.get(from)) + ROW / 2,
          x2 = x(M.u0(to)), y2 = rowY(at.get(to)) + ROW / 2;
    const mx = Math.max(x1 + 10, x2 - 12);
    ctx.save();
    ctx.strokeStyle = c; ctx.lineWidth = 1.4; ctx.lineJoin = "round";
    if (x2 < x1) ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(x1, y1); ctx.lineTo(mx, y1); ctx.lineTo(mx, y2);
    ctx.lineTo(x2 - 4, y2); ctx.stroke();
    ctx.setLineDash([]);
    ctx.beginPath();
    ctx.moveTo(x2 - 4, y2); ctx.lineTo(x2 - 9, y2 - 3.2);
    ctx.lineTo(x2 - 9, y2 + 3.2); ctx.closePath();
    ctx.fillStyle = c; ctx.fill();
    ctx.restore();
  };
  for (const d of selected.deps) arrow(d, selected);
  for (const f of selected.feeds) arrow(selected, f);
}

/* ── the overview strip: the whole plan, always ─────────────────────────── */
function drawMini() {
  const W = mini.clientWidth || 1, H = 40;
  mctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  mctx.clearRect(0, 0, W, H);
  mctx.fillStyle = T.sunk; mctx.fillRect(0, 0, W, H);
  const mx = u => (u - M.lo) / span() * W;
  const lanes = 9, used = new Array(lanes).fill(-1e9);
  for (const t of [...tasks].sort((p, q) => M.u0(p) - M.u0(q))) {
    const l0 = mx(M.u0(t)), l1 = Math.max(l0 + 2, mx(M.u1(t)));
    let lane = used.findIndex(u => u < l0 - 1);
    if (lane < 0) lane = lanes - 1;
    used[lane] = l1;
    mctx.fillStyle = col(t.state);
    mctx.globalAlpha = t.critical ? 1 : 0.5;
    mctx.fillRect(l0, 3 + lane * 3.8, l1 - l0, t.critical ? 2.6 : 2);
  }
  mctx.globalAlpha = 1;
  for (const u of (mode === "vision" ? [0, CPM.length]
                                     : [nowDay(), M.hi - 3])) {
    mctx.fillStyle = T.ink3;
    mctx.fillRect(Math.round(mx(u)), 0, 1, H);
  }
  // the viewport, as a window you can grab
  const v0 = scroll.scrollLeft / ppu + M.lo,
        v1 = (scroll.scrollLeft + plot.clientWidth - LEFT) / ppu + M.lo;
  const wx = mx(v0), ww = Math.max(8, mx(v1) - mx(v0));
  mctx.fillStyle = T["accent-wash"]; mctx.fillRect(wx, 0, ww, H);
  mctx.strokeStyle = T.ink3; mctx.lineWidth = 1;
  mctx.strokeRect(Math.round(wx) + .5, .5, Math.round(ww) - 1, H - 1);
}
const syncWin = () => drawMini();

/* ── hit testing: geometry in, meaning out ─────────────────────────────── */
function at(ev) {
  const r = plot.getBoundingClientRect();
  const px = ev.clientX - r.left, py = ev.clientY - r.top;
  const i = Math.floor((py + scroll.scrollTop - HEAD - PAD) / ROW);
  const row = py < HEAD ? null : (rows[i] || null);
  return {px:px, py:py, i:row ? i : -1, row:row,
          zone:py < HEAD ? "head" : px < LEFT - 3 ? "cell"
               : px <= LEFT + 3 ? "grip" : "plot"};
}

let drag = null;
scroll.addEventListener("mousemove", ev => {
  const h = at(ev);
  if (drag) return;
  scroll.style.cursor = h.zone === "grip" ? "col-resize"
    : h.row ? "pointer" : h.zone === "head" ? "default" : "grab";
  if (h.i !== hover) { hover = h.i; schedule(); }
  if (h.row && h.row.kind === "task") showTip(ev, h.row.t);
  else tip.style.display = "none";
});
scroll.addEventListener("mouseleave", () => {
  tip.style.display = "none";
  if (hover !== -1) { hover = -1; schedule(); }
});
scroll.addEventListener("mousedown", ev => {
  if (ev.button) return;
  const h = at(ev);
  if (h.zone === "grip") {
    drag = {kind:"grip", x:ev.clientX, from:LEFT};
    scroll.style.cursor = "col-resize";
  } else if (h.zone === "plot" || h.zone === "head") {
    drag = {kind:"pan", x:ev.clientX, y:ev.clientY,
            sx:scroll.scrollLeft, sy:scroll.scrollTop, moved:0, hit:h};
  } else {
    drag = {kind:"tap", hit:h, moved:0};
  }
  ev.preventDefault();
  tip.style.display = "none";
});
addEventListener("mousemove", ev => {
  if (!drag) return;
  if (drag.kind === "grip") {
    LEFT = Math.max(150, Math.min(560, drag.from + ev.clientX - drag.x));
    tw.clear(); place();
    return;
  }
  if (drag.kind !== "pan") return;
  drag.moved = Math.max(drag.moved, Math.abs(ev.clientX - drag.x) +
                                    Math.abs(ev.clientY - drag.y));
  if (drag.moved > 3) {
    scroll.style.cursor = "grabbing";
    scroll.scrollLeft = drag.sx - (ev.clientX - drag.x);
    scroll.scrollTop = drag.sy - (ev.clientY - drag.y);
  }
});
addEventListener("mouseup", ev => {
  if (!drag) return;
  const d = drag; drag = null;
  scroll.style.cursor = "default";
  if (d.kind === "grip") return;
  if (d.moved > 3) return;                       // that was a pan, not a click
  const h = d.hit && d.hit.row ? d.hit : at(ev);
  if (!h.row) { if (selected) { selected = null; draw(); } return; }
  if (h.row.kind === "group") {
    const k = h.row.key;
    collapsed.has(k) ? collapsed.delete(k) : collapsed.add(k);
    build();
  } else {
    selected = h.row.t; draw(); openDrawer(h.row.t);
  }
});
scroll.addEventListener("scroll", () => schedule(), {passive:true});
scroll.addEventListener("wheel", ev => {
  if (ev.ctrlKey || ev.metaKey) {
    ev.preventDefault();
    setZoom(ppu * (ev.deltaY < 0 ? 1.12 : 1 / 1.12),
      ev.clientX - plot.getBoundingClientRect().left - LEFT);
  }
}, {passive:false});
scroll.addEventListener("dblclick", ev => {
  const h = at(ev);
  if (h.zone === "grip") { LEFT = 260; tw.clear(); place(); }
  else if (h.row && h.row.kind === "task") focusTask(h.row.t);
});

function showTip(e, t) {
  const when = mode === "vision"
    ? `+${fmtH(t.es)} → +${fmtH(t.ef)} from now`
    : `${fmtD(t.startDay)} → ${fmtD(t.endDay)}`;
  tip.innerHTML =
    '<div class="t"></div><div class="r rel"></div>' +
    '<div class="r"><span class="k">state</span> <span class="' +
      (HOT[t.state] ? "warn" : "") + '">' + esc(t.state) + "</span>" +
    ' · <span class="k">prio</span> ' + t.prio +
    ' · <span class="k">est</span> ' + fmtH(t.est) +
    (t.wave ? ' · <span class="k">wave</span> ' + t.wave : "") +
    (t.board ? ' · <span class="k">board</span> ' + esc(t.board) : "") +
    "</div>" +
    '<div class="r">' + when + "</div>" +
    '<div class="r">' + (t.critical
      ? "★ critical — every hour cut here moves the vision closer"
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

function panTo(u, smooth) {
  const left = (u - M.lo) * ppu - (plot.clientWidth - LEFT) / 2;
  if (smooth && !reduced) scroll.scrollTo({left:left, behavior:"smooth"});
  else scroll.scrollLeft = left;
  schedule();
}

/* ── zoom: interpolated, because a jump loses the reader's place ────────── */
let zoomAnim = 0;
function setZoom(next, keepPx) {
  const at = keepPx === undefined ? (plot.clientWidth - LEFT) / 2 : keepPx;
  const u = (scroll.scrollLeft + at) / ppu + M.lo;
  ppu = Math.min(M.max, Math.max(M.min, next));
  spacer.style.width = Math.max(plot.clientWidth,
    LEFT + span() * ppu + 24) + "px";
  scroll.scrollLeft = (u - M.lo) * ppu - at;
  draw(); drawMini();
}
function glide(target, keepPx) {
  cancelAnimationFrame(zoomAnim);
  target = Math.min(M.max, Math.max(M.min, target));
  if (reduced) return setZoom(target, keepPx);
  const from = ppu, t0 = performance.now(), ms = 220;
  const step = now => {
    const k = Math.min(1, (now - t0) / ms);
    const e = 1 - Math.pow(1 - k, 3);             // ease out, Apple-ish
    setZoom(from + (target - from) * e, keepPx);
    if (k < 1) zoomAnim = requestAnimationFrame(step);
  };
  zoomAnim = requestAnimationFrame(step);
}
function fitAll() {
  glide((plot.clientWidth - LEFT - 16) / span(), 0);
  scroll.scrollLeft = 0;
}

function zoomButtons() {
  $("zooms").innerHTML = M.zooms
    .map(([n, v]) => `<button data-z="${v}">${n}</button>`).join("") +
    '<button id="fit" title="fit the whole plan (f)">fit</button>';
  for (const b of $("zooms").querySelectorAll("[data-z]"))
    b.onclick = () => glide(+b.dataset.z);
  $("fit").onclick = fitAll;
}

function setMode(next) {
  mode = next; remode(); M = MODE[mode]; ppu = M.ppu;
  $("mVision").classList.toggle("on", mode === "vision");
  $("mDates").classList.toggle("on", mode === "dates");
  $("sub").textContent = mode === "vision"
    ? "distance to the vision" : "the worker-limited calendar";
  zoomButtons();
  build();
  ppu = Math.max(M.min, Math.min(M.max,
    (plot.clientWidth - LEFT - 16) / span()));
  scroll.scrollLeft = 0;
  place();
}

function syncToggles() {
  $("onlycrit").classList.toggle("on", critOnly);
  $("onlyready").classList.toggle("on", readyOnly);
}

/* ── controls ─────────────────────────────────────────────────────────── */
$("mVision").onclick = () => setMode("vision");
$("mDates").onclick = () => setMode("dates");
$("zi").onclick = () => glide(ppu * 1.4);
$("zo").onclick = () => glide(ppu / 1.4);
$("ce").onclick = () => {
  const g = GROUPS[groupBy];
  if (collapsed.size) collapsed.clear();
  else for (const t of tasks) if (matches(t) && g.key(t) !== "")
    collapsed.add(g.key(t));
  build();
};
$("grp").onchange = () => { groupBy = $("grp").value; collapsed.clear();
                            build(); };
$("q").oninput = () => { filter = $("q").value.trim(); build(); };
$("onlycrit").onclick = () => { critOnly = !critOnly; syncToggles(); build(); };
$("onlyready").onclick = () => { readyOnly = !readyOnly; syncToggles(); build(); };

let rt = 0;
addEventListener("resize", () => {
  clearTimeout(rt);
  rt = setTimeout(() => { resize(); place(); movePill(); }, 60);
});

/* the canvas is focusable, and the selection moves by key — a chart nobody
   can reach with a keyboard is a picture, not a control */
function move(delta) {
  const idx = rows.findIndex(r => r.kind === "task" && r.t === selected);
  let i = idx < 0 ? (delta > 0 ? -1 : rows.length) : idx;
  for (i += delta; i >= 0 && i < rows.length; i += delta)
    if (rows[i].kind === "task") break;
  if (i < 0 || i >= rows.length) return;
  selected = rows[i].t;
  const y = HEAD + PAD + i * ROW;
  if (y - scroll.scrollTop < HEAD + 4) scroll.scrollTop = y - HEAD - 4;
  if (y - scroll.scrollTop > plot.clientHeight - ROW - 4)
    scroll.scrollTop = y - plot.clientHeight + ROW + 4;
  draw();
  if ($("drawer").classList.contains("open")) openDrawer(selected);
}

addEventListener("keydown", e => {
  // ⌘1..⌘6 — the way a Mac app switches tabs
  if ((e.metaKey || e.ctrlKey) && e.key >= "1" && e.key <= "6") {
    const b = $("views").querySelectorAll("button")[+e.key - 1];
    if (b) { e.preventDefault(); b.click(); }
    return;
  }
  if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") {
    if (e.key === "Escape") {
      if (e.target.id === "q") { $("q").value = ""; filter = ""; build(); }
      if (e.target.id === "lq") { $("lq").value = ""; listQ = ""; drawList(); }
      e.target.blur();
    }
    return;
  }
  if (e.key === "n" || e.key === "N") { e.preventDefault(); $("newprd").click(); }
  else if (e.key === "/") { e.preventDefault();
    (view === "list" ? $("lq") : $("q")).focus(); }
  else if (e.key === "ArrowDown" || e.key === "j") { e.preventDefault(); move(1); }
  else if (e.key === "ArrowUp" || e.key === "k") { e.preventDefault(); move(-1); }
  else if (e.key === "Enter" && selected) openDrawer(selected);
  else if (e.key === "f") fitAll();
  else if (e.key === "v") setMode(mode === "vision" ? "dates" : "vision");
  else if (e.key === "c") $("onlycrit").click();
  else if (e.key === "r") $("onlyready").click();
  else if (e.key === "+" || e.key === "=") glide(ppu * 1.4);
  else if (e.key === "-") glide(ppu / 1.4);
  else if (e.key === "Escape") {
    if ($("drawer").classList.contains("open")) closeDrawer();
    else if (anyFilter()) go({clear:1});
    else { selected = null; draw(); }
  }
});

function focusTask(t) {
  selected = t;
  openDrawer(t);
  if (byRel.has(t.rel)) {
    if (view !== "timeline") setView("timeline");
    collapsed.delete(GROUPS[groupBy].key(t));
    if (!matches(t)) {                 // a filter is hiding it — drop the filter
      filter = ""; $("q").value = ""; critOnly = readyOnly = false;
      stateSel.clear(); syncToggles(); drawLegend();
    }
    build();
    const i = rows.findIndex(r => r.kind === "task" && r.t === t);
    if (i >= 0) {
      const y = HEAD + PAD + i * ROW - plot.clientHeight / 2;
      if (reduced) scroll.scrollTop = y;
      else scroll.scrollTo({top:Math.max(0, y), behavior:"smooth"});
    }
    panTo((M.u0(t) + M.u1(t)) / 2, true);
  }
  draw();
}

/* ── the numbers, and where each one leads ─────────────────────────────── */
function drawHeader() {
  const c = DATA.counts, live = liveRows(), asks = askRows();
  const cal = Math.max(...tasks.map(t => t.endDay), 0) * (DATA.dayHours || 8);
  const bits = [];
  const S = '<span class="sep">·</span>';
  bits.push(lnk("<b>" + tasks.length + "</b> left", {view:"list", state:"live"},
                "every PRD still to do, as a table"));
  bits.push(lnk('<span class="crit"><b>' + fmtH(CPM.length) +
                "</b> to the vision</span>",
                {view:"timeline", crit:1, mode:"vision"},
                "the chain that sets the finish — nothing else moves it"));
  bits.push(lnk("Σ" + fmtH(CPM.total) + " of work", {view:"analytics"},
                "how the work is distributed"));
  bits.push(lnk("peak <b>" + CPM.peak + "</b> agents",
                {view:"timeline", mode:"dates"},
                "the fastest path wants this many at its widest — " +
                "the calendar is what " + DATA.workers + " workers costs"));
  if (cal > CPM.length * 1.05)
    bits.push(lnk("at " + DATA.workers + " workers: " + fmtH(cal),
                  {view:"timeline", mode:"dates"}));
  if (asks.length)
    bits.push(lnk("<b>" + asks.length + "</b> waiting on you",
                  {view:"asks", hot:1}, "answer them"));
  if (c.done)
    bits.push(lnk(c.done + " done", {view:"list", state:"done"}));
  if (c.parked)
    bits.push(lnk(c.parked + " parked", {view:"list", state:"parked"},
                  "PRDs in a state the loop does not work"));
  if (c.containers)
    bits.push("<span>" + c.containers + " parent(s) folded</span>");
  if ((DATA.boards || []).length)
    bits.push(lnk(DATA.boards.length + " boards",
                  {view:"timeline", group:"board"}));
  $("stats").innerHTML = bits.join(S);
  if (DATA.vision && DATA.vision.purpose)
    $("purpose").textContent = DATA.vision.purpose;

  // the frontier: everything dispatchable now, biggest door first. This is
  // the dispatch order — take from the left and the vision arrives soonest.
  const ready = (CPM.ready || []).map(r => byRel.get(r)).filter(Boolean);
  $("front").innerHTML = '<button class="lnk h" data-go="' +
    esc(JSON.stringify({view:"timeline", ready:1})) +
    '" title="keep only these on the timeline">ready now</button>' +
    (ready.length ? ready.slice(0, 14).map(t =>
      '<button class="p' + (t.critical ? " crit" : "") + '" data-go="' +
      esc(JSON.stringify({prd:t.rel})) + '" title="' +
      esc(t.title || t.name) + '">' +
      (t.critical ? "★ " : "") + "<b>" + esc(t.name) + "</b> " +
      "<em>" + fmtH(t.est) + (t.unblocks ? " ▸" + fmtH(t.unblocks) : "") +
      "</em></button>").join("") +
      (ready.length > 14 ? lnk("+" + (ready.length - 14) + " more",
        {view:"timeline", ready:1}) : "")
      : '<span class="h">' + (tasks.length
          ? "nothing — every PRD left waits on another"
          : "nothing scheduled — run plan") + "</span>");

  $("note").innerHTML = (DATA.unplanned || []).length
    ? "not in the last plan (no bar): " +
      DATA.unplanned.map(r => lnk(esc(r), {prd:r, view:"board"})).join(", ") +
      " — re-run plan to schedule them" : "";
  const badge = $("askbadge");
  badge.textContent = asks.length;
  badge.classList.toggle("on", asks.length > 0);
  movePill();
}

function drawLegend() {
  const present = [...new Set(tasks.map(t => t.state))];
  const order = Object.keys(STATES);
  present.sort((p, q) => order.indexOf(p) - order.indexOf(q));
  $("legend").innerHTML = present.map(s =>
    '<button class="lnk' + (stateSel.has(s) ? " on" : "") + '" data-go="' +
    esc(JSON.stringify({tstate:s})) + '" title="' +
    (stateSel.has(s) ? "stop filtering by " : "show only ") + s + '">' +
    '<i class="' + (stRing(s) ? "ring" : "") + '" style="' +
    (stRing(s) ? "color:" : "background:") + stVar(s) + '"></i>' + s +
    "</button>").join("") +
    (stateSel.size ? lnk("all states", {tstate:null}) : "") +
    '<span><i class="crit"></i>critical chain</span>' +
    "<span><b></b>now · vision</span>" +
    '<span class="keys">drag to pan · ctrl+wheel zoom · ' +
    "<kbd>/</kbd> filter · <kbd>v</kbd> axis · <kbd>c</kbd> critical · " +
    "<kbd>r</kbd> ready · <kbd>f</kbd> fit · <kbd>↑↓</kbd> select</span>";
}

/* ── the inspector ────────────────────────────────────────────────────────
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
// the live page updates itself on every board change; it must not do that
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

const prdCache = new Map();
async function fetchPrd(rel, fresh) {
  if (!SERVED) return null;
  if (!fresh && prdCache.has(rel)) return prdCache.get(rel);
  const r = await fetch(API + "/prd?board=" + encodeURIComponent(BOARD_KEY) +
                        "&rel=" + encodeURIComponent(rel));
  if (!r.ok) throw new Error(await r.text());
  const d = await r.json();
  prdCache.set(rel, d);
  return d;
}

async function openDrawer(t) {
  dTask = t; dDirty = false; dData = prdCache.get(t.rel) || null;
  $("drawer").classList.add("open");
  $("dtitle").value = t.title || t.name;
  $("drel").textContent = t.rel + (t.board ? "  ·  " + t.board : "");
  $("dmsg").textContent = SERVED ? (dData ? "" : "loading…")
                                 : "read-only — no daemon";
  drawBody();
  // the open PRD lives in the URL: a deep link to one task, and the thing
  // that survives the page updating itself
  syncHash();
  if (!SERVED) return;
  try {
    dData = await fetchPrd(t.rel, true);
    if (dTask !== t) return;                    // the reader moved on
    $("dmsg").textContent = "";
    drawBody();
  } catch (e) {
    $("dmsg").textContent = "could not load the PRD";
  }
}

function closeDrawer() {
  $("drawer").classList.remove("open");
  dTask = null; dDirty = false;
  syncHash();
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
      t.deps.map(x => `<span class="chip2" data-go="${esc(JSON.stringify({prd:x.rel}))}">◂ ${esc(x.name)}</span>`).join("") +
      t.feeds.map(x => `<span class="chip2" data-go="${esc(JSON.stringify({prd:x.rel}))}">${esc(x.name)} ▸</span>`).join("") +
      "</div>";
  }
  if (d && d.fm) {
    const skip = {state: 1, priority: 1};
    const rows2 = Object.entries(d.fm).filter(([k, v]) => !skip[k] &&
      !Array.isArray(v) && v !== "");
    if (rows2.length)
      h += "<h4>frontmatter</h4><div class=facts>" + rows2.map(([k, v]) =>
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
  const copy = $("dcopy");
  if (copy) copy.onclick = ev => {
    ev.preventDefault();
    navigator.clipboard && navigator.clipboard.writeText(copy.dataset.p);
    $("dmsg").textContent = "path copied";
  };
  const ansBtn = $("danswer");
  if (ansBtn) ansBtn.onclick = () => answer(dTask.rel, $("dsay").value);
  const noteBtn = $("dnoteadd");
  if (noteBtn) noteBtn.onclick = async () => {
    const txt = $("dnote").value.trim();
    if (!txt) return;
    const out = await save(dTask.rel, {append: txt, heading: "Notes"});
    toast(out.error ? "Not saved — " + out.error : "Noted", !!out.error);
    if (!out.error) { dDirty = false; prdCache.delete(dTask.rel);
                      openDrawer(dTask); }
  };
  for (const id of ["dstate", "dprio", "dbodytext"]) {
    const el = $(id);
    if (el) el.oninput = () => { dDirty = true; $("dmsg").textContent = "unsaved"; };
  }
  $("dtitle").oninput = () => { dDirty = true; $("dmsg").textContent = "unsaved"; };
}

/* the one write the board is actually waiting for */
async function answer(rel, text) {
  text = (text || "").trim();
  if (!text) return {error: "nothing to say"};
  const out = await save(rel, {append: text, heading: "Answers",
                               fm: {state: "open"}});
  toast(out.error ? "Not saved — " + out.error
                  : "Answered — " + rel.split("/").pop() + " is open again",
        !!out.error);
  if (!out.error) {
    prdCache.delete(rel);
    const row = allByRel.get(rel);
    if (row) row.state = "open";               // optimistic, until /data lands
    dDirty = false;
    refresh();
  }
  return out;
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
    $("dmsg").textContent = "";
    prdCache.delete(dTask.rel);
    if (st) { const row = allByRel.get(dTask.rel);
              if (row) row.state = st.value; }
    toast(out.claim ? "Saved — " + out.claim + " holds this PRD" : "Saved");
    refresh();
  } catch (e) {
    $("dmsg").textContent = "";
    toast("Not saved — " + e.message, true);
  }
}

$("dclose").onclick = closeDrawer;
$("dgo").onclick = saveDrawer;
$("drevert").onclick = () => { dDirty = false; drawBody();
                               $("dmsg").textContent = "reverted"; };

async function save(rel, payload) {
  if (!SERVED) return {error: "no daemon — this file is read-only"};
  try {
    const r = await fetch(API + "/edit", {method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(Object.assign({board: BOARD_KEY, prd: rel}, payload))});
    return await r.json();
  } catch (e) { return {error: String(e)}; }
}

/* ═══ the other four views ═══════════════════════════════════════════════
   One board, five readings. The timeline answers "what is in front of us";
   the board answers "what is where"; asks answers "what is waiting on me";
   the list answers "show me all of it"; the analytics answer "how is this
   going". They share the payload, the inspector, the state ink and the
   router, so nothing has to be learned twice.                            */
const STATE_ORDER = ["open", "refine", "question", "analyzing", "specced",
                     "claimed", "blocked", "failed", "done"];
const isLive = r => STATE_ORDER.includes(r.state) && r.state !== "done";
const liveRows = () => ALL.filter(isLive);
const askRows = () => ALL.filter(r => r.state === "question" ||
                                      r.state === "blocked");
let view = "timeline";
let listQ = "", listState = null, listBoard = null;
let listBy = "prio", listDesc = true;

// a row from `all` can be opened in the inspector too — it just has no place
// in the plan, so the plan facts are the ones that go missing
function taskFor(rel) {
  const t = byRel.get(rel);
  if (t) return t;
  const r = allByRel.get(rel);
  if (!r) return null;
  return Object.assign({}, r, {es: 0, ef: 0, slack: 0, critical: false,
    unblocks: 0, downstream: 0, startDay: 0, endDay: 0, wave: null,
    deps: [], feeds: [], plain: true});
}

/* the segmented control's selection is one element that travels, the way a
   Mac segmented control moves — six buttons repainting is a different,
   cheaper-looking thing */
function movePill() {
  const on = $("views").querySelector("button.on");
  const pill = $("segpill");
  if (!on || !pill) return;
  pill.style.width = on.offsetWidth + "px";
  pill.style.transform = "translateX(" + on.offsetLeft + "px)";
}

let toastT = 0;
function toast(msg, bad) {
  const t = $("toast");
  t.innerHTML = '<span class="' + (bad ? "no" : "ok") + '">' +
    (bad ? "⚠" : "✓") + "</span>" + esc(msg);
  t.classList.add("on");
  clearTimeout(toastT);
  toastT = setTimeout(() => t.classList.remove("on"), bad ? 4000 : 1800);
}

function repaintView() {
  if (view === "board") drawBoard();
  else if (view === "list") drawList();
  else if (view === "asks") drawAsks();
  else if (view === "analytics") drawAnalytics();
  else if (view === "memos") drawMemos();
  else { resize(); place(); }
}

function setView(v) {
  if (!document.querySelector('section[data-view="' + v + '"]')) v = "timeline";
  view = v;
  for (const el of document.querySelectorAll("section[data-view]"))
    el.classList.toggle("on", el.dataset.view === v);
  for (const b of $("views").querySelectorAll("button")) {
    const on = b.dataset.v === v;
    b.classList.toggle("on", on);
    b.setAttribute("aria-selected", on ? "true" : "false");
  }
  movePill();
  $("tcontrols").style.display = v === "timeline" ? "" : "none";
  $("front").style.display = v === "timeline" ? "" : "none";
  $("inview").style.display = v === "timeline" ? "" : "none";
  repaintView();
  syncHash();
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
  for (const [st, rowsIn] of cols) {
    if (!rowsIn.length && !STATE_ORDER.includes(st)) continue;
    rowsIn.sort((p, q) => q.prio - p.prio || p.rel.localeCompare(q.rel));
    const col2 = document.createElement("div");
    col2.className = "col" + (rowsIn.length ? "" : " bare");
    col2.dataset.state = st;
    const hrs = rowsIn.reduce((a, r) => a + r.est, 0);
    col2.innerHTML = '<h3 data-go="' +
      esc(JSON.stringify({view:"list", state:st})) + '" title="' + esc(st) +
      ' as a table"><i class="' + (stRing(st) ? "ring" : "") + '" style="' +
      (stRing(st) ? "color:" : "background:") + stVar(st) + '"></i>' +
      esc(st) + '<span class="n">' + rowsIn.length +
      (hrs ? " · " + fmtH(hrs) : "") + "</span></h3>";
    const box = document.createElement("div");
    box.className = "cards";
    const CAP = st === "done" ? 40 : 200;
    for (const r of rowsIn.slice(0, CAP)) {
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
      c.onclick = () => { const x2 = taskFor(r.rel); if (x2) openDrawer(x2); };
      c.addEventListener("dragstart", e => {
        e.dataTransfer.setData("text/plain", r.rel);
        c.classList.add("drag");
      });
      c.addEventListener("dragend", () => c.classList.remove("drag"));
      box.append(c);
    }
    if (rowsIn.length > CAP) {
      const more = document.createElement("div");
      more.className = "card"; more.style.cursor = "pointer";
      more.dataset.go = JSON.stringify({view:"list", state:st});
      more.innerHTML = '<div class="m">+' + (rowsIn.length - CAP) +
        " more — the list has all of them</div>";
      more.draggable = false;
      box.append(more);
    }
    col2.append(box);
    col2.addEventListener("dragover", e => { e.preventDefault();
      col2.classList.add("over"); });
    col2.addEventListener("dragleave", () => col2.classList.remove("over"));
    col2.addEventListener("drop", async e => {
      e.preventDefault(); col2.classList.remove("over");
      const rel = e.dataTransfer.getData("text/plain");
      const row = allByRel.get(rel);
      if (!row || row.state === st) return;
      row.state = st;                       // optimistic: the drop is the edit
      drawBoard();
      const out = await save(rel, {fm: {state: st}});
      if (out.error) toast("Not saved — " + out.error, true);
      else { prdCache.delete(rel); refresh(); }
    });
    el.append(col2);
  }
}

/* ── asks: the board waiting on a person ──────────────────────────────────
   `question` means an agent stopped and wants an answer; `blocked` means it
   hit a wall. Both are the board waiting on you, and both used to be a state
   you had to go find. This is the inbox: the question as it was written, and
   the box that answers it — the same two edits (`## Answers`, state back to
   open) the orchestrator makes when the answer is typed at a terminal.     */
async function drawAsks() {
  const asks = askRows().sort((p, q) =>
    (p.state === q.state ? 0 : p.state === "question" ? -1 : 1) ||
    q.prio - p.prio || p.rel.localeCompare(q.rel));
  const el = $("asks");
  if (!asks.length) {
    el.innerHTML = '<div class="blank"><div class="big">nothing is waiting ' +
      "on you</div><div>every PRD is either moving or done — the board will " +
      "put a question here the moment it has one</div>" +
      btn("back to the plan", {view:"timeline"}) + "</div>";
    return;
  }
  el.innerHTML = asks.map(r => {
    const t = byRel.get(r.rel) || {};
    const blocked = r.state === "blocked";
    return '<div class="ask2" data-rel="' + esc(r.rel) + '">' +
      '<div class="hd" data-go="' + esc(JSON.stringify({prd:r.rel})) + '">' +
      '<div style="flex:1;min-width:0"><div class="ttl">' +
        esc(r.title || r.name) + "</div>" +
      '<div class="rel">' + esc(r.rel) + (r.board ? " · " + esc(r.board) : "") +
        " · p" + r.prio + (t.critical ? " · ★ critical" : "") +
        (r.est ? " · " + fmtH(r.est) : "") + "</div></div>" +
      '<span class="flag' + (blocked ? " blocked" : "") + '">' +
        (blocked ? "blocked" : "question") + "</span></div>" +
      '<div class="q skel">reading the PRD…</div>' +
      (SERVED ? '<div class="foot"><textarea placeholder="' +
        (blocked ? "what unblocks it — this goes in as the answer"
                 : "the answer — numbered to match") + '"></textarea>' +
      '<div class="row2"><button class="act send primary">answer &amp; reopen' +
      '</button>' + (blocked
        ? '<button class="act reopen">just reopen</button>' : "") +
      '<span class="hint">writes ## Answers · sets state open</span>' +
      "</div></div>"
        : '<div class="foot"><span class="hint">read-only — open this board ' +
          "through the service to answer here</span></div>") + "</div>";
  }).join("");
  for (const card of el.querySelectorAll(".ask2")) {
    const rel = card.dataset.rel;
    const box = card.querySelector("textarea");
    const send = card.querySelector(".send");
    if (!SERVED) {
      card.querySelector(".q").textContent =
        "the question is in the PRD — open this board through the service to " +
        "read and answer it here";
      continue;
    }
    const fire = async only => {
      send.disabled = true;
      const out = only === "reopen"
        ? await save(rel, {fm: {state: "open"}})
        : await answer(rel, box.value);
      send.disabled = false;
      if (out && out.error) { if (only === "reopen") toast(out.error, true); return; }
      if (only === "reopen") { toast("Reopened"); prdCache.delete(rel);
                               refresh(); }
      card.classList.add("gone");
      setTimeout(() => { if (view === "asks") drawAsks(); }, reduced ? 0 : 280);
    };
    send.onclick = () => fire();
    const re = card.querySelector(".reopen");
    if (re) re.onclick = () => fire("reopen");
    box.addEventListener("keydown", e => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") fire();
    });
    // the question text itself, read live out of the PRD
    fetchPrd(rel).then(d => {
      const q = card.querySelector(".q");
      const txt = section(d.body, "Questions") || section(d.body, "Blocked") ||
        section(d.body, "Notes") || (d.body || "").slice(0, 700);
      q.classList.remove("skel");
      q.textContent = txt || "(the PRD says nothing yet)";
    }).catch(() => {
      const q = card.querySelector(".q");
      q.textContent = "could not read the PRD";
    });
  }
}

/* ── list ──────────────────────────────────────────────────────────────── */
function listRows() {
  const f = listQ.trim().toLowerCase();
  return ALL.filter(r => {
    if (listState === "live" && !isLive(r)) return false;
    if (listState === "parked" && (STATE_ORDER.includes(r.state))) return false;
    if (listState === "hot" && !(r.state === "question" ||
        r.state === "blocked" || r.state === "failed")) return false;
    if (listState && !["live","parked","hot"].includes(listState) &&
        r.state !== listState) return false;
    if (listBoard && (r.board || DATA.board) !== listBoard) return false;
    return !f || r.rel.toLowerCase().includes(f) ||
      (r.title || "").toLowerCase().includes(f) || r.state.includes(f) ||
      (r.board || "").includes(f);
  });
}

function drawList() {
  const cols = [["rel", "prd"], ["state", "state"], ["prio", "prio"],
                ["est", "est"], ["actual", "actual"], ["board", "board"],
                ["wave", "wave"]];
  const rowsOut = listRows().sort((p, q) => {
    const k = listBy;
    const A = k === "wave" ? ((byRel.get(p.rel) || {}).wave || 0) : p[k];
    const B = k === "wave" ? ((byRel.get(q.rel) || {}).wave || 0) : q[k];
    const c = typeof A === "number" && typeof B === "number"
      ? A - B : String(A == null ? "" : A).localeCompare(String(B == null ? "" : B));
    return listDesc ? -c : c;
  });
  $("ltokens").innerHTML =
    (listState ? '<button class="token" data-go="' +
      esc(JSON.stringify({state:null})) + '">state <b>' + esc(listState) +
      '</b><span class="x">✕</span></button>' : "") +
    (listBoard ? '<button class="token" data-go="' +
      esc(JSON.stringify({board:null})) + '">board <b>' + esc(listBoard) +
      '</b><span class="x">✕</span></button>' : "");
  $("list").innerHTML = rowsOut.length
    ? "<table><thead><tr>" + cols.map(([k, l]) =>
        `<th data-k="${k}" class="${listBy === k ? "by" : ""}">${l}` +
        (listBy === k ? (listDesc ? " ↓" : " ↑") : "") + "</th>").join("") +
      "</tr></thead><tbody>" + rowsOut.map(r => {
        const t = byRel.get(r.rel) || {};
        return `<tr class="r" data-rel="${esc(r.rel)}"><td><i class="` +
          (stRing(r.state) ? "ring" : "") + '" style="' +
          (stRing(r.state) ? "color:" : "background:") + stVar(r.state) +
          '"></i>' + esc(r.rel) + '</td><td><span class="st ' +
          (r.state === "question" ? "warn" : HOT[r.state] ? "danger" : "") +
          '">' + esc(r.state) + "</span></td><td>" + r.prio + "</td><td>" +
          (r.est ? fmtH(r.est) : "") + "</td><td>" +
          (r.actual ? fmtH(r.actual) : "") + "</td><td>" +
          esc(r.board || "") + "</td><td>" + (t.wave || "") + "</td></tr>";
      }).join("") + "</tbody></table>"
    : '<div class="none">nothing matches' +
      (listState || listBoard || listQ ? " — " +
        lnk("clear the filters", {state:null, board:null, q:""}) : "") + "</div>";
  $("lcount").textContent = rowsOut.length + " of " + ALL.length +
    " · click a row for the PRD";
  for (const th of $("list").querySelectorAll("th"))
    th.onclick = () => { const k = th.dataset.k;
      listDesc = listBy === k ? !listDesc : true; listBy = k; drawList(); };
  for (const tr of $("list").querySelectorAll("tr.r"))
    tr.onclick = () => { const x2 = taskFor(tr.dataset.rel);
                         if (x2) openDrawer(x2); };
}
$("lq").oninput = () => { listQ = $("lq").value; drawList(); };

/* ── memos: the board's decisions, read where the work is ─────────────── */
let memosLoaded = null;
async function drawMemos() {
  if (!SERVED) {
    $("memos").innerHTML = '<div class="blank">memos are read live — open ' +
      "this board through the service to see them</div>";
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
    (m.prds && m.prds.length ? " · governs " + m.prds.map(p =>
      lnk(esc(p), {prd:p})).join(" ") : "") +
    "</div><pre>" + esc((m.body || "").slice(0, 3000)) + "</pre></div>").join("")
    : '<div class="blank">no memos yet — a decision gets one when there is ' +
      "a decision</div>";
}

/* ── analytics ─────────────────────────────────────────────────────────────
   Six numbers and four questions. Every chart is one measure on one axis,
   direct-labelled, with the list view as its table — and every tile, bar and
   dot is a door into the set of PRDs it counts. State keeps the ink it has
   everywhere else in this page; the by-board bars use ink levels in a fixed
   order, never cycled.                                                     */
function tile(k, v, s, dest, hot) {
  return '<button class="tile' + (hot ? " hot" : "") + '" data-go="' +
    esc(JSON.stringify(dest)) + '"><div class="k">' + k + '</div><div class="v">' +
    v + '</div><div class="s">' + (s || "") + "</div></button>";
}

function bars(rowsIn, color, fmt, dest) {
  const max = Math.max(...rowsIn.map(r => r.v), 1);
  return rowsIn.map((r, i) =>
    '<div class="brow"' + (dest ? ' data-go="' + esc(JSON.stringify(dest(r))) +
    '"' : "") + '><span class="lab" title="' + esc(r.k) + '">' +
    esc(r.k) + '</span><span class="track"><span class="fill" style="width:' +
    (r.v / max * 100).toFixed(1) + "%;background:" +
    (typeof color === "function" ? color(r, i) : color) +
    '"></span></span><span class="val">' + fmt(r) + "</span></div>").join("");
}

function drawAnalytics() {
  const live = liveRows();
  const done = ALL.filter(r => r.state === "done");
  const parked = ALL.filter(r => !STATE_ORDER.includes(r.state));
  const hLeft = live.reduce((a, r) => a + r.est, 0);
  const pct = Math.round(done.length /
    Math.max(ALL.length - parked.length, 1) * 100);
  const ready = tasks.filter(t => t.ready).length;
  const waiting = ALL.filter(r => r.state === "question").length;
  const blocked = ALL.filter(r => r.state === "blocked").length;
  const cal = Math.max(...tasks.map(t => t.endDay), 0) * (DATA.dayHours || 8);
  $("tiles").innerHTML =
    tile("done", pct + "%", done.length + " of " +
         (ALL.length - parked.length) + " PRDs", {view:"list", state:"done"}) +
    tile("left", live.length, fmtH(hLeft) + " estimated",
         {view:"list", state:"live"}) +
    tile("to the vision", fmtH(CPM.length),
         "of " + fmtH(CPM.total) + " in the plan",
         {view:"timeline", crit:1, mode:"vision"}) +
    tile("peak agents", CPM.peak, "at " + DATA.workers + " workers: " +
         fmtH(cal), {view:"timeline", mode:"dates"}) +
    tile("ready now", ready, "dispatchable this second",
         {view:"timeline", ready:1, mode:"vision"}) +
    tile("waiting on you", waiting + blocked,
         waiting + " question · " + blocked + " blocked", {view:"asks"},
         waiting + blocked > 0);

  // 1 — where the work sits
  const byState = [];
  for (const st of STATE_ORDER.concat(
        [...new Set(parked.map(r => r.state))])) {
    const rowsIn = ALL.filter(r => r.state === st);
    if (rowsIn.length) byState.push({k: st, v: rowsIn.length,
      h: rowsIn.reduce((a, r) => a + r.est, 0)});
  }
  // 2 — where the hours are: members on a master, top-level trees otherwise
  const master = (DATA.boards || []).length;
  const key = master ? (r => r.board || DATA.board)
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

  const calib = done.filter(r => r.est > 0 && r.actual > 0);
  const ratios = calib.map(r => r.actual / r.est).sort((A, B) => A - B);
  const med = ratios.length ? ratios[Math.floor(ratios.length / 2)] : 0;

  $("charts").innerHTML =
    '<div class="chart"><h3>Where the work sits</h3>' +
    '<p class="sub">every PRD by state · bar is the count, the number is the ' +
    "hours · click a state for its list</p>" +
    bars(byState, r => stVar(r.k), r => r.v + (r.h ? " · " + fmtH(r.h) : ""),
         r => ({view:"list", state:r.k})) + "</div>" +

    '<div class="chart"><h3>Where the hours are</h3>' +
    '<p class="sub">' + (master ? "estimated hours left per member board"
      : "estimated hours left per top-level tree") + "</p>" +
    (byGroup.length ? bars(byGroup, (r, i) => CAT[i % CAT.length],
      r => fmtH(r.v), r => master ? {view:"list", board:r.k, state:"live"}
                                  : {view:"list", q:r.k, state:"live"})
      : '<div class="empty">nothing left to weigh</div>') +
    "</div>" +

    '<div class="chart"><h3>Estimates against reality</h3>' +
    '<p class="sub">' + (calib.length
      ? calib.length + " done PRDs carry an <code>actual:</code> · median " +
        med.toFixed(2) + "× the estimate"
      : "no done PRD carries an <code>actual:</code> yet") + "</p>" +
    (calib.length >= 3 ? scatter(calib) :
      '<div class="empty">calibration needs a few finished PRDs with ' +
      "<code>actual:</code> written on them</div>") + "</div>" +

    '<div class="chart"><h3>Hours left over time</h3>' +
    '<p class="sub">one point a day, since the day the board started keeping ' +
    "count</p>" +
    (HIST.length >= 2 ? burndown(HIST) :
      '<div class="empty">collecting — ' + (HIST.length
        ? "one day so far (" + HIST[0].d + "), the line needs two"
        : "nothing recorded yet") + "</div>") + "</div>";
  for (const c of $("charts").querySelectorAll("circle[data-rel]"))
    c.onclick = () => { const t = taskFor(c.dataset.rel); if (t) openDrawer(t); };
}

function scatter(rowsIn) {
  const W = 460, H = 220, pad = 30;
  const mx = Math.max(...rowsIn.map(r => Math.max(r.est, r.actual)), 1);
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
  for (const r of rowsIn)
    g += `<circle class="dot" cx="${X(r.est).toFixed(1)}" cy="${Y(r.actual).toFixed(1)}" r="4.5"` +
      ` data-rel="${esc(r.rel)}"><title>${esc(r.name)} — est ${fmtH(r.est)}, actual ${fmtH(r.actual)}</title></circle>`;
  return g + "</svg>";
}

function burndown(h) {
  const W = 460, H = 220, pad = 34;
  const mx = Math.max(...h.map(r => r.hleft || 0), 1);
  const X = i => pad + (h.length < 2 ? 0 : i / (h.length - 1)) * (W - pad - 8);
  const Y = v => H - pad - v / mx * (H - pad - 12);
  const pts = h.map((r, i) => `${X(i).toFixed(1)},${Y(r.hleft || 0).toFixed(1)}`);
  let g = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="hours left over time">`;
  g += `<line class="ax" x1="${pad}" y1="${H - pad}" x2="${W - 4}" y2="${H - pad}"/>`;
  if (h.length >= 4)
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

/* ── writing a PRD from the view ───────────────────────────────────────── */
$("newprd").onclick = () => { $("newbox").classList.add("on"); $("ntitle").focus(); };
$("ncancel").onclick = () => $("newbox").classList.remove("on");
$("newbox").onclick = e => {
  if (e.target.id === "newbox") $("newbox").classList.remove("on");
};
$("ncreate").onclick = async () => {
  const title = $("ntitle").value.trim();
  if (!title) return;
  if (!SERVED) return toast("no daemon — this file is read-only", true);
  try {
    const r = await fetch(API + "/new", {method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({board: BOARD_KEY, title: title,
        body: $("nbody").value, priority: $("nprio").value || 0,
        parent: $("nparent").value.trim()})});
    const out = await r.json();
    if (!out.prd) return toast(out.error || "not written", true);
    $("newbox").classList.remove("on");
    $("ntitle").value = ""; $("nbody").value = ""; $("nparent").value = "";
    toast("Wrote " + out.prd);
    await refresh();                     // no reload: the page just grows a row
    const t = taskFor(out.prd);
    if (t) openDrawer(t);
  } catch (e) { toast("not written — " + e.message, true); }
};

/* ═══ live, in place ══════════════════════════════════════════════════════
   The board is files, and files change under us — an agent claims a PRD, a
   worker reports, the planner re-waves. The old page reloaded itself for
   that, which threw away the scroll, the zoom, the selection and whatever was
   half-typed. Now the daemon's change notice fetches the payload and swaps it
   in: the rows move, nothing else does.                                    */
let refreshing = null;
async function refresh() {
  if (!SERVED) return;
  if (refreshing) return refreshing;
  refreshing = (async () => {
    try {
      const r = await fetch(API + "/data?board=" + encodeURIComponent(BOARD_KEY));
      const out = await r.json();
      if (out.payload) apply(out.payload);
    } catch (e) { /* the daemon went away; the page still reads fine */ }
    refreshing = null;
  })();
  return refreshing;
}

function apply(payload) {
  if (!payload || !payload.cpm) return;      // an unenriched payload is stale
  const keepRel = selected ? selected.rel : null;
  const sx = scroll.scrollLeft, sy = scroll.scrollTop;
  DATA = payload;
  hydrate();
  remode(); M = MODE[mode];
  if (!GROUPS[groupBy]) groupBy = "wave";
  selected = keepRel ? byRel.get(keepRel) || null : null;
  build();
  scroll.scrollLeft = sx; scroll.scrollTop = sy;
  drawHeader(); drawLegend();
  memosLoaded = null;
  if (view !== "timeline") repaintView();
  if (dTask) {                                  // keep the inspector honest
    const t = taskFor(dTask.rel);
    if (t && !dDirty) { dTask = t; drawBody(); }
  }
}
// the daemon's live loop calls this when the board's sequence moves
window.__pearde_apply = apply;
window.__pearde_refresh = refresh;

/* ── the URL is the view ──────────────────────────────────────────────────
   Where you are is a link you can send: which view, which filter, which PRD.
   Every door writes it; a reload lands in the same place.                  */
let hashLock = false;
function syncHash() {
  const p = [];
  if (view !== "timeline") p.push("view=" + view);
  if (dTask) p.push("prd=" + encodeURIComponent(dTask.rel));
  if (view === "list" && listState) p.push("state=" + listState);
  if (view === "list" && listBoard) p.push("board=" + encodeURIComponent(listBoard));
  if (view === "timeline" && critOnly) p.push("crit=1");
  if (view === "timeline" && readyOnly) p.push("ready=1");
  const h = p.length ? "#" + p.join("&") : "";
  if (location.hash === h) return;
  hashLock = true;
  history.replaceState(null, "", h || location.pathname + location.search);
  setTimeout(() => { hashLock = false; }, 0);
}

function readHash() {
  const h = location.hash.replace(/^#/, "");
  if (!h) return;
  const d = {};
  for (const part of h.split("&")) {
    const i = part.indexOf("=");
    if (i < 0) continue;
    const k = part.slice(0, i), v = decodeURIComponent(part.slice(i + 1));
    if (k === "view") d.view = v;
    else if (k === "prd") d.prd = v;
    else if (k === "state") { d.state = v; d.view = d.view || "list"; }
    else if (k === "board") { d.board = v; d.view = d.view || "list"; }
    else if (k === "crit") d.crit = 1;
    else if (k === "ready") d.ready = 1;
    else if (k === "q") d.q = v;
  }
  if (Object.keys(d).length) go(d);
}
addEventListener("hashchange", () => { if (!hashLock) readHash(); });

/* ── boot ──────────────────────────────────────────────────────────────── */
resize();
syncToggles();
setMode("vision");
drawHeader();
drawLegend();
readHash();
setInterval(() => { if (mode === "dates") draw(); }, 60000);
if (SERVED) setInterval(refresh, 90000);   // a floor under the live loop
</script>
</body>
</html>
"""
