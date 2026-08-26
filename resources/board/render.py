#!/usr/bin/env python3
"""pearde gantt — the plan as distance to the vision, not as a calendar.

One self-contained HTML file: `plan.py gantt` writes it to `prds/.view.html`
from the schedule `plan` saved in `.plan.json`, and the live service
serves the same render at `/board/<name>`.

**Why the x axis is not time.** The workers are agents. They start when the
work is dispatchable and there are as many of them as the board can usefully
run, so a calendar date on a bar is a guess about staffing, not a fact about
the plan. What is a fact is the dependency structure: how much work has to
finish, in sequence, before the vision is reached. That is the axis — weight
along the critical path, zero at *now*, and the right edge is the vision.

Read off it directly:

  · **critical** bars are the ones that set the finish. Shorten one and the
    vision moves left; shorten anything else and nothing happens
  · **float** is drawn as a tail: how late a task may start before it becomes
    critical. A long tail is slack you can spend
  · **ready now** is the frontier at x=0 — everything dispatchable this second,
    ordered by how much work each one unblocks. That ordering IS the dispatch
    order for the fastest path to the vision
  · a **footprint clash** is a pairwise `after` edge — the two PRDs are
    serialized, and nothing else waits with them. No rounds, no barriers

`dates` mode is one click away for a human who wants a calendar — it draws
the same bars on the worker-limited schedule `plan` computed.

The critical-path arithmetic happens here, in Python (`cpm`), so the numbers
the page draws and the numbers an agent reads out of it are the same numbers.
plan.py builds the payload — it owns the scan, the map and the settings. This
module enriches it, renders it and writes it.
"""
import base64
import json
import os
import re

VIEW_FILE = ".view.html"


def cpm(tasks):
    """Critical-path method over the plan's dependency graph, in weight.

    Forward pass with no worker limit — the question is not "when will three
    workers get to it" but "how soon could this possibly be reached", which
    is the only bound agents cannot argue with. Backward pass from the finish
    gives every task its float. Returns (tasks, meta). Tasks gain:

        es ef      earliest start / finish, weight from now
        ls lf      latest start / finish that still hits the finish
        slack      ls - es. 0 means critical
        critical   on a longest chain
        ready      dispatchable now — starts at zero, no dependency and no
                   footprint edge in front of it, and nobody already holding it
        unblocks   weight of work waiting downstream, transitively. The
                   frontier sorts by this: it is the size of the door the
                   task opens
        downstream how many PRDs that weight spans

    A `needs` naming a PRD outside the plan (done, parked, never scheduled) is
    already satisfied and drops out — `plan` resolved it, the graph only holds
    what is left to do.

    `after` is the plan's footprint serialization — two PRDs touching one
    path, ordered pairwise so two agents never edit one file together. It is
    an edge like any dependency, and ONLY an edge: the pair is ordered, and
    nothing else on the board waits with it — agents start the moment their
    own gates clear, so a round barrier would hold every PRD in the round for
    its slowest member.

    The track does not start at now. Tasks with `past: true` are done work,
    laid out by the same dependency arithmetic and shifted so the last of
    them ENDS at zero — the axis runs from the first landed PRD to the
    vision, and now is a place on it. Tasks with `parked: true` (failed,
    deferred, the user's own states) sit at zero with no float and no
    downstream: visible, weighed, and scheduled by nothing."""
    past = {t["rel"]: t for t in tasks if t.get("past")}
    parked = {t["rel"]: t for t in tasks if t.get("parked") and
              t["rel"] not in past}
    by = {t["rel"]: t for t in tasks
          if t["rel"] not in past and t["rel"] not in parked}
    deps = {r: sorted({d for d in ((t.get("needs") or []) +
                                   (t.get("after") or []))
                       if d in by and d != r})
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
    # forward pass: earliest start is the last gate to clear — a `needs` or an
    # `after`, the graph does not care which — and nothing else holds a bar
    es, ef = {}, {}
    for r in order:
        es[r] = max([ef.get(d, 0.0) for d in deps[r]] or [0.0])
        ef[r] = es[r] + est[r]
    length = max(ef.values()) if ef else 0.0

    ls, lf = {}, {}
    for r in reversed(order):
        lf[r] = min([ls[s] for s in feeds[r] if s in ls] or [length])
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
        # A PRD a worker already holds is not a PRD to dispatch. The frontier
        # is the dispatch order, so anything in flight belongs in `collect`
        # below or nowhere — offering it twice is how one PRD gets two workers.
        t["ready"] = es[r] < 0.01 and not t.get("held")
        t["unblocks"] = round(sum(est[s] for s in down[r]), 2)
        t["downstream"] = len(down[r])
        t["blocks"] = sorted(feeds[r])

    # the past: the same forward pass over the done graph, then shifted left
    # so the last landed PRD ends at zero. The order within it is dependency
    # truth. The exact day each one landed is history the burn-down keeps.
    pdeps = {r: [d for d in (t.get("needs") or []) if d in past and d != r]
             for r, t in past.items()}
    pindeg = {r: len(pdeps[r]) for r in past}
    pq = sorted(r for r in past if not pindeg[r])
    porder = []
    pfeeds = {r: [] for r in past}
    for r, ds in pdeps.items():
        for d in ds:
            pfeeds[d].append(r)
    while pq:
        r = pq.pop(0)
        porder.append(r)
        for s in sorted(pfeeds[r]):
            pindeg[s] -= 1
            if not pindeg[s]:
                pq.append(s)
    porder += sorted(r for r in past if r not in set(porder))
    pes, pef = {}, {}
    for r in porder:
        pes[r] = max([pef.get(d, 0.0) for d in pdeps[r]] or [0.0])
        pef[r] = pes[r] + float(past[r].get("est") or 0.0)
    shift = max(pef.values()) if pef else 0.0
    for r, t in past.items():
        t["es"] = round(pes[r] - shift, 3)
        t["ef"] = round(pef[r] - shift, 3)
        t["ls"], t["lf"] = t["es"], t["ef"]
        t["slack"] = 0
        t["critical"] = False
        t["ready"] = False
        t["unblocks"] = 0
        t["downstream"] = 0
        t["blocks"] = []
    for r, t in parked.items():
        t["es"], t["ef"] = 0, round(float(t.get("est") or 0.0), 3)
        t["ls"], t["lf"] = t["es"], t["ef"]
        t["slack"] = 0
        t["critical"] = False
        t["ready"] = False
        t["unblocks"] = 0
        t["downstream"] = 0
        t["blocks"] = []

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
        # the whole track: what already landed (drawn left of now), what is
        # parked at now, and where zero sits between them and the vision
        "landed": round(shift, 2),
        "landedCount": len(past),
        "parkedWeight": round(sum(float(t.get("est") or 0.0)
                                  for t in parked.values()), 2),
        "parkedCount": len(parked),
        "peak": peak,
        "chain": chain,
        "ready": sorted((r for r in by if by[r]["ready"]),
                        key=lambda r: (-by[r]["unblocks"], -by[r]["prio"], r)),
        # finished work, still open on the board. Ordered by what closing it
        # releases, because that is the whole reason to close it first
        "collect": sorted((r for r in by if by[r].get("collect")),
                          key=lambda r: (-by[r]["unblocks"], -by[r]["prio"], r)),
    }
    return tasks, meta


def enrich(payload):
    p = dict(payload)
    tasks, meta = cpm([dict(t) for t in payload.get("tasks", [])])
    # past and parked bars carry no worker schedule. On the calendar they sit
    # where the weight axis puts them, at the board's own weight-per-day
    day_h = float(payload.get("dayHours") or 8.0)
    for t in tasks:
        if (t.get("past") or t.get("parked")) and "startDay" not in t:
            t["startDay"] = round(t["es"] / day_h, 4)
            t["endDay"] = round(t["ef"] / day_h, 4)
    p["tasks"], p["cpm"] = tasks, meta
    return p


def asset(name):
    """One of this module's siblings, inlined at render time. They are the
    page's real source — `.css` and `.js` an editor understands — and the
    output stays one self-contained file because the read happens here."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), name),
              encoding="utf-8") as fh:
        return fh.read()


LIT_FILE = "lit-core.min.js"
USER_CSS = "view.user.css"
USER_JS = "view.user.js"


def lit_map():
    """Lit as an import map, inlined. The page opens over `file://` with no
    network, so the module is carried as a data: URL rather than fetched. The
    name it binds is `lit`, so a board's own `view.user.js` imports it exactly
    as any Lit code does."""
    src = asset(LIT_FILE).encode("utf-8")
    url = "data:text/javascript;base64," + base64.b64encode(src).decode("ascii")
    return ('<script type="importmap">'
            + json.dumps({"imports": {"lit": url}})
            + "</script>")


def user_asset(board, name):
    """A board's own stylesheet or script, or "". It lives on the board, not
    in this skill, so it survives a skill upgrade and differs per board."""
    if not board:
        return ""
    try:
        with open(os.path.join(board, name), encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def untag(text, tag):
    """`</script` inside the text would close the tag it is inlined into.
    `<\\/` is the same character sequence to both a JS string and a CSS
    escape, so the page reads what the author wrote."""
    return re.sub(r"</(?=%s)" % tag, r"<\\/", text, flags=re.I)


def render(payload, board=None):
    p = enrich(payload)
    data = json.dumps(p, sort_keys=True).replace("</", "<\\/")
    # the assets first: `let DATA = __PAYLOAD__` lives inside view.js
    html = (TEMPLATE
            .replace("__LIT__", lit_map())
            .replace("__CSS__", asset("view.css"))
            .replace("__JS__", asset("view.js"))
            .replace("__TITLE__", p["board"])
            .replace("__PAYLOAD__", data))
    # the board's own last, so a user rule wins the cascade and a user script
    # sees a built page. A module, so it can `import ... from "lit"` the way
    # the page itself does.
    css, js = user_asset(board, USER_CSS), user_asset(board, USER_JS)
    tail = ((f"<style>\n{untag(css, 'style')}\n</style>\n" if css else "")
            + (f'<script type="module">\n{untag(js, "script")}\n</script>\n'
               if js else ""))
    return html.replace("</body>", tail + "</body>") if tail else html


def write(board, payload):
    path = os.path.join(board, VIEW_FILE)
    with open(path, "w", encoding="utf-8") as f:
        f.write(render(payload, board))
    return path



# ── the look ──────────────────────────────────────────────────────────────────
# Greyscale carries the plan; colour is spent only where a person is needed.
#
#   · state-as-progress is a ramp of ink weight, not of hue: open is a whisper,
#     claimed is full ink (full white in the dark theme — furthest along is
#     always the brightest thing on the surface)
#   · five hues, and no sixth. Each means one thing, each is sparse by
#     construction, and a coloured mark anywhere on the page is worth looking
#     at because of it:
#       red     blocked or failed — a wall a person has to take down
#       orange  a question — the board is waiting on a person to answer it
#       purple  a worker is holding this right now. The only state bounded by
#               the worker count, which is what keeps it rare
#       green   finished and only waiting to be taken: every acceptance box
#               closed while a worker still holds it, or a lane main has not
#               seen. The act wanted is to close it, not to work it
#       blue    the chain that sets the finish. The one hue that is not a
#               request for an act: it says shortening this bar moves the
#               vision left and shortening any other does nothing
#   · they rank when they collide: red over green over purple. A wall with
#     every box closed is still a wall; a finished PRD is worth taking before
#     it is worth knowing who holds it
#   · everything else is graphite, which is what keeps those five findable.
#     Progress below `claimed` stays a ramp of ink weight; a hue is never
#     spent on ranking, on categories, or on decoration
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
<link rel="icon" href="data:,">
<style>
__CSS__</style>
</head>
<body>
<header id="titlebar">
  <div class="ident">
    <button id="pick" aria-haspopup="listbox" aria-expanded="false"
            title="switch board (B)"><h1>__TITLE__</h1><svg id="chev"
      width="9" height="6" viewBox="0 0 9 6" aria-hidden="true"><path
      d="M1 1.2 4.5 4.7 8 1.2" fill="none" stroke="currentColor"
      stroke-width="1.5" stroke-linecap="round"
      stroke-linejoin="round"/></svg></button>
    <span id="sub">the plan</span>
    <div id="picks" role="listbox" aria-label="boards" hidden></div>
  </div>
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
<div class="seam" id="seam-toolbar"></div>
<div id="purpose"></div>
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
  <button id="ce" title="collapse every group or branch">collapse all</button>
  <input type="search" id="q" placeholder="filter  /" autocomplete="off">
  <button id="onlycrit" title="only the tasks that set the finish">critical</button>
  <button id="onlyready" title="only what is dispatchable now">ready</button>
  <button id="onlycollect" title="only finished work waiting to be closed">collect</button>
  <button id="landtog" title="the column: what to collect, dispatch and land (L)">column</button>
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
  <pearde-frontier id="land" aria-label="waiting to land in main"></pearde-frontier>
</div>
<div id="legend"></div>
<div id="note"></div>
</section>
<section data-view="board"><pearde-board id="board"></pearde-board></section>
<section data-view="asks"><div id="asks"></div></section>
<section data-view="list">
  <div id="listbar"><input type="search" id="lq" placeholder="filter  /">
    <span class="tokens" id="ltokens"></span>
    <span class="n" id="lcount"></span></div>
  <pearde-list id="list"></pearde-list>
</section>
<section data-view="analytics">
  <div id="tiles"></div><div id="charts"></div>
</section>
<section data-view="memos"><pearde-memos id="memos"></pearde-memos></section>
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
<div class="seam" id="seam-sidebar"></div>
<aside id="drawer">
  <div id="dhead">
    <div class="who">
      <input type="text" id="dtitle" placeholder="title">
      <div class="rel" id="drel"></div>
    </div>
    <button id="dclose" title="close (Esc)">✕</button>
  </div>
  <div id="dbody"></div>
  <div class="seam" id="seam-inspector"></div>
  <div id="dsave">
    <button class="go" id="dgo">save</button>
    <button id="drevert">revert</button>
    <span class="msg" id="dmsg"></span>
  </div>
</aside>
__LIT__
<script type="module">
__JS__</script>
</body>
</html>
"""
