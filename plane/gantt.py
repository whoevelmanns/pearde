#!/usr/bin/env python3
"""pearde gantt — render the last plan as a self-contained adaptive timeline.

One HTML file, no server, no dependencies: `sync.py gantt` writes it to
`prds/.gantt.html` from the schedule `plan` saved in `.plane-map.json`.

The view is condensed and adaptive: a vertical line marks *now*, and the row
list holds only the tasks whose bars cross the visible window — scroll left or
right and rows appear, drop out, and re-sort by priority, so what you see is
always the work that matters around the time under your eyes. Rows without a
visible bar do not exist; empty vertical space is never scrolled past.

sync.py builds the payload (it owns the scan, the map, and the settings);
this module only renders and writes.
"""
import json
import os

GANTT_FILE = ".gantt.html"


def render(payload):
    data = json.dumps(payload, sort_keys=True).replace("</", "<\\/")
    return (TEMPLATE
            .replace("__TITLE__", payload["board"])
            .replace("__PAYLOAD__", data))


def write(board, payload):
    path = os.path.join(board, GANTT_FILE)
    with open(path, "w", encoding="utf-8") as f:
        f.write(render(payload))
    return path


# The chart follows the board's data-viz conventions: state-as-progress is an
# ordinal one-hue ramp (open → analyzing → specced → claimed, light→dark on a
# light surface, mirrored for dark), exception states wear the reserved status
# colors (question=warning, blocked=serious, failed=critical), and every row
# names its state in text so color never carries identity alone. The now-line
# is magenta — a hue no state uses, so it never impersonates one.
TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ — gantt</title>
<style>
:root{
  color-scheme:light;
  --page:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e;
  --muted:#898781; --grid:#e1e0d9; --axis:#c3c2b7;
  --border:rgba(11,11,11,.10); --wash:rgba(11,11,11,.03);
  --st-open:#86b6ef; --st-analyzing:#3987e5; --st-specced:#1c5cab;
  --st-claimed:#104281; --st-question:#fab219; --st-blocked:#ec835a;
  --st-failed:#d03b3b; --now:#d55181;
}
@media (prefers-color-scheme: dark){
  :root:where(:not([data-theme="light"])){
    color-scheme:dark;
    --page:#0d0d0d; --surface:#1a1a19; --ink:#ffffff; --ink2:#c3c2b7;
    --muted:#898781; --grid:#2c2c2a; --axis:#383835;
    --border:rgba(255,255,255,.10); --wash:rgba(255,255,255,.035);
    --st-open:#184f95; --st-analyzing:#2a78d6; --st-specced:#5598e7;
    --st-claimed:#9ec5f4; --now:#e87ba4;
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --page:#0d0d0d; --surface:#1a1a19; --ink:#ffffff; --ink2:#c3c2b7;
  --muted:#898781; --grid:#2c2c2a; --axis:#383835;
  --border:rgba(255,255,255,.10); --wash:rgba(255,255,255,.035);
  --st-open:#184f95; --st-analyzing:#2a78d6; --st-specced:#5598e7;
  --st-claimed:#9ec5f4; --now:#e87ba4;
}
*{box-sizing:border-box;margin:0}
body{background:var(--page);color:var(--ink);
  font:13px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;padding:14px}
header{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:baseline;
  padding:2px 4px 10px}
header h1{font-size:15px;font-weight:650}
header h1 small{color:var(--muted);font-weight:400;margin-left:6px}
#stats{color:var(--ink2);font-size:12px}
#inview{color:var(--ink2);font-size:12px;margin-left:auto}
#legend{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:11.5px;
  color:var(--ink2);padding:0 4px 8px}
#legend i{display:inline-block;width:9px;height:9px;border-radius:2px;
  margin-right:5px;vertical-align:-1px;border:1px solid var(--border)}
#legend i.hollow{background:transparent !important;
  border:1.5px solid var(--st-open)}
#legend b{display:inline-block;width:9px;height:2px;background:var(--now);
  margin-right:5px;vertical-align:2px}
#controls{display:flex;gap:6px}
#controls button{background:var(--surface);color:var(--ink2);
  border:1px solid var(--border);border-radius:5px;padding:2px 9px;
  font:12px system-ui,sans-serif;cursor:pointer}
#controls button:hover{color:var(--ink)}
#frame{position:relative;border:1px solid var(--border);border-radius:8px;
  background:var(--surface);overflow:hidden}
#wrap{overflow:auto;max-height:calc(100vh - 165px);min-height:220px}
#canvas{position:relative}
#axis{position:sticky;top:0;z-index:6;height:36px;background:var(--surface);
  border-bottom:1px solid var(--grid)}
#axis .m{position:absolute;top:2px;font-size:10.5px;font-weight:600;
  color:var(--ink2);border-left:1px solid var(--axis);padding-left:5px;
  height:14px;white-space:nowrap;overflow:hidden}
#axis .d{position:absolute;top:19px;font-size:10px;color:var(--muted);
  font-variant-numeric:tabular-nums;white-space:nowrap}
#grid .v{position:absolute;top:0;bottom:0;width:1px;background:var(--grid)}
#grid .w{position:absolute;top:0;bottom:0;background:var(--wash)}
#now{position:absolute;top:0;bottom:0;width:2px;background:var(--now);
  z-index:4;pointer-events:none}
#nowtag{position:absolute;top:38px;transform:translateX(-50%);z-index:6;
  background:var(--surface);border:1px solid var(--now);border-radius:4px;
  padding:0 6px;font-size:10px;color:var(--ink);white-space:nowrap;
  pointer-events:none}
#rows{position:relative;padding:44px 0 10px}
.row{position:absolute;left:0;width:100%;height:26px;display:flex;
  align-items:center;transition:top .18s ease,opacity .15s ease}
.row.off{opacity:0;pointer-events:none}
.bar{position:absolute;top:6px;height:14px;border-radius:4px;min-width:6px;
  border:1px solid var(--border);cursor:default}
.bar.st-refine{background:transparent;border:1.5px solid var(--st-open)}
.lbl{position:sticky;left:6px;z-index:3;max-width:46%;display:flex;
  align-items:center;gap:6px;background:var(--surface);opacity:.94;
  border:1px solid var(--border);border-radius:4px;padding:1px 7px;
  font-size:11px;white-space:nowrap;pointer-events:none}
.lbl i{flex:none;width:8px;height:8px;border-radius:2px;
  border:1px solid var(--border)}
.lbl i.hollow{background:transparent !important;
  border:1.5px solid var(--st-open)}
.lbl .n{overflow:hidden;text-overflow:ellipsis;font-weight:550}
.lbl .s{color:var(--ink2)}
.lbl .e{color:var(--muted);font-variant-numeric:tabular-nums}
.pill{position:absolute;bottom:14px;z-index:7;
  background:var(--surface);border:1px solid var(--border);border-radius:99px;
  padding:3px 10px;font-size:11px;color:var(--ink2);cursor:pointer;
  box-shadow:0 1px 4px rgba(0,0,0,.08)}
.pill:hover{color:var(--ink)}
#pillL{left:10px}#pillR{right:10px}
#empty{position:absolute;inset:0;display:none;align-items:center;z-index:5;
  justify-content:center;color:var(--muted);font-size:12.5px;
  pointer-events:none}
#tip{position:fixed;z-index:20;display:none;max-width:340px;
  background:var(--surface);border:1px solid var(--border);border-radius:6px;
  box-shadow:0 2px 10px rgba(0,0,0,.14);padding:7px 10px;font-size:11.5px}
#tip .t{font-weight:600;margin-bottom:2px}
#tip .r{color:var(--ink2)}
#tip .k{color:var(--muted)}
details{margin-top:12px;color:var(--ink2);font-size:12px}
summary{cursor:pointer;color:var(--muted)}
table{border-collapse:collapse;margin-top:8px;width:100%}
th,td{text-align:left;padding:3px 10px 3px 0;border-bottom:1px solid var(--grid);
  font-variant-numeric:tabular-nums}
th{color:var(--muted);font-weight:500;font-size:11px}
#note{margin-top:8px;color:var(--muted);font-size:11.5px;padding:0 4px}
</style>
</head>
<body>
<header>
  <h1>__TITLE__<small>adaptive gantt</small></h1>
  <span id="stats"></span>
  <span id="inview"></span>
  <div id="controls">
    <button id="zo" title="zoom out">−</button>
    <button id="zi" title="zoom in">+</button>
    <button id="fit" title="fit the whole plan">fit</button>
    <button id="go" title="center the now line">now</button>
  </div>
</header>
<div id="legend"></div>
<div id="frame">
  <div id="wrap"><div id="canvas">
    <div id="axis"></div>
    <div id="grid"></div>
    <div id="now"></div><div id="nowtag"></div>
    <div id="rows"></div>
  </div></div>
  <button class="pill" id="pillL"></button>
  <button class="pill" id="pillR"></button>
  <div id="empty"></div>
</div>
<div id="note"></div>
<details><summary>table view</summary><table id="tbl"></table></details>
<div id="tip"></div>
<script>
"use strict";
const DATA = __PAYLOAD__;
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
const wrap = $("wrap"), canvas = $("canvas"), rows = $("rows"),
      axis = $("axis"), grid = $("grid"), tip = $("tip");
const ROW = 26, TOP = 44, MS = 86400000;
const a = DATA.anchor.split("-").map(Number);
const anchor = new Date(a[0], a[1] - 1, a[2]);
const nowDay = () => (Date.now() - anchor.getTime()) / MS;
const dayDate = d => new Date(a[0], a[1] - 1, a[2] + Math.floor(d));
const fmtD = d => dayDate(d).toLocaleDateString(undefined,
  {month:"short", day:"numeric"});
const fmtH = h => (Math.round(h * 10) / 10 + "h").replace(".0h", "h");
const tasks = DATA.tasks.slice();

// fixed domain: every bar plus the now line, padded so both ends scroll
const d0 = Math.floor(Math.min(0, nowDay(),
  ...tasks.map(t => t.startDay))) - 3;
const d1 = Math.ceil(Math.max(nowDay(),
  ...tasks.map(t => t.endDay), d0 + 7)) + 4;
const span = d1 - d0;
let ppd = 40;                                    // px per day, set by fit()
const x = day => (day - d0) * ppd;

// one element per task, created once; scroll only moves and hides them
for (const t of tasks) {
  const st = STATES[t.state] || STATES.open;
  const row = document.createElement("div");
  row.className = "row off";
  const bar = document.createElement("div");
  bar.className = "bar st-" + t.state;
  if (!st.hollow) bar.style.background = st.c;
  const lbl = document.createElement("div");
  lbl.className = "lbl";
  const dot = "<i" + (st.hollow ? ' class="hollow"' : "") +
    ' style="background:' + (st.hollow ? "transparent" : st.c) + '"></i>';
  lbl.innerHTML = dot + '<span class="n"></span><span class="s">' +
    t.state + '</span><span class="e">p' + t.prio + " · " +
    fmtH(t.est) + "</span>";
  lbl.querySelector(".n").textContent = t.name;
  row.append(lbl, bar);
  bar.addEventListener("mousemove", e => showTip(e, t));
  bar.addEventListener("mouseleave", () => tip.style.display = "none");
  rows.append(row);
  t.el = row; t.bar = bar;
}

function showTip(e, t) {
  tip.innerHTML = '<div class="t"></div><div class="r"></div>' +
    '<div class="r"><span class="k">state</span> ' + t.state +
    ' · <span class="k">prio</span> ' + t.prio +
    ' · <span class="k">est</span> ' + fmtH(t.est) +
    (t.wave ? ' · <span class="k">wave</span> ' + t.wave : "") + "</div>" +
    '<div class="r">' + fmtD(t.startDay) + " → " + fmtD(t.endDay) + "</div>" +
    (t.needs.length ? '<div class="r n"><span class="k">needs</span> ' +
      '<span class="v"></span></div>' : "");
  tip.querySelector(".t").textContent = t.title;
  tip.querySelectorAll(".r")[0].textContent = t.rel;
  // needs is frontmatter the user wrote — a dir name carrying < or & must
  // render as itself, not as markup. Every other field above is either a
  // number or one of the fixed state words, so only this one needs a node.
  if (t.needs.length)
    tip.querySelector(".n .v").textContent = t.needs.join(", ");
  tip.style.display = "block";
  const w = tip.offsetWidth, h = tip.offsetHeight;
  tip.style.left = Math.min(e.clientX + 14, innerWidth - w - 8) + "px";
  tip.style.top = Math.min(e.clientY + 14, innerHeight - h - 8) + "px";
}

function buildChrome() {
  canvas.style.width = span * ppd + "px";
  axis.innerHTML = ""; grid.innerHTML = "";
  const everyDay = ppd >= 26, weekly = ppd >= 7;
  let m = -1;
  for (let d = d0; d <= d1; d++) {
    const dt = dayDate(d), dow = dt.getDay();
    if (dt.getMonth() !== m) {                       // month rule
      m = dt.getMonth();
      const el = document.createElement("div");
      el.className = "m";
      el.style.left = x(d) + "px";
      el.textContent = dt.toLocaleDateString(undefined,
        {month: "short", year: "numeric"});
      axis.append(el);
    }
    if (everyDay || (weekly && dow === 1)) {          // day / monday ticks
      const el = document.createElement("div");
      el.className = "d";
      el.style.left = x(d) + 3 + "px";
      el.textContent = everyDay ? dt.getDate()
        : dt.toLocaleDateString(undefined, {month:"short", day:"numeric"});
      axis.append(el);
    }
    if (everyDay || dow === 1) {                      // vertical hairlines
      const v = document.createElement("div");
      v.className = "v"; v.style.left = x(d) + "px";
      grid.append(v);
    }
    if (dow === 6) {                                  // weekend wash
      const w = document.createElement("div");
      w.className = "w";
      w.style.left = x(d) + "px";
      w.style.width = 2 * ppd + "px";
      grid.append(w);
    }
  }
  for (const t of tasks) {
    t.bar.style.left = x(t.startDay) + "px";
    t.bar.style.width = Math.max(6, (t.endDay - t.startDay) * ppd) + "px";
  }
  placeNow();
}

function placeNow() {
  const nx = x(nowDay());
  $("now").style.left = nx - 1 + "px";
  $("nowtag").style.left = nx + "px";
  $("nowtag").textContent = "now · " + new Date().toLocaleDateString(
    undefined, {weekday:"short", month:"short", day:"numeric"});
}

// the adaptive part: only tasks whose bar crosses the visible window get a
// row, sorted by priority — scroll and the list re-forms around the window
function reflow() {
  const v0 = wrap.scrollLeft / ppd + d0,
        v1 = (wrap.scrollLeft + wrap.clientWidth) / ppd + d0;
  const vis = tasks.filter(t => t.endDay > v0 && t.startDay < v1);
  vis.sort((p, q) => q.prio - p.prio || p.startDay - q.startDay ||
    p.rel.localeCompare(q.rel));
  const seen = new Set(vis);
  vis.forEach((t, i) => {
    t.el.style.top = TOP + i * ROW + "px";
    t.el.classList.remove("off");
  });
  for (const t of tasks) if (!seen.has(t)) t.el.classList.add("off");
  rows.style.height = TOP + Math.max(vis.length, 5) * ROW + 10 + "px";
  const earlier = tasks.filter(t => t.endDay <= v0).length,
        later = tasks.filter(t => t.startDay >= v1).length;
  $("inview").textContent = vis.length + " of " + tasks.length + " in view";
  $("pillL").style.display = earlier ? "block" : "none";
  $("pillL").textContent = "◂ " + earlier + " earlier";
  $("pillR").style.display = later ? "block" : "none";
  $("pillR").textContent = later + " later ▸";
  $("empty").style.display = vis.length ? "none" : "flex";
  $("empty").textContent = tasks.length
    ? "no scheduled work in this window — scroll, or press fit"
    : "nothing scheduled — run plan";
}

let raf = 0;
wrap.addEventListener("scroll", () => {
  if (!raf) raf = requestAnimationFrame(() => { raf = 0; reflow(); });
});
addEventListener("resize", reflow);

function setZoom(f, keepPx) {
  const at = keepPx === undefined ? wrap.clientWidth / 2 : keepPx;
  const day = (wrap.scrollLeft + at) / ppd + d0;
  ppd = Math.min(160, Math.max(6, ppd * f));
  buildChrome();
  wrap.scrollLeft = (day - d0) * ppd - at;
  reflow();
}
$("zi").onclick = () => setZoom(1.3);
$("zo").onclick = () => setZoom(1 / 1.3);
$("fit").onclick = () => {
  ppd = Math.min(160, Math.max(6, (wrap.clientWidth - 20) / span));
  buildChrome(); wrap.scrollLeft = 0; reflow();
};
$("go").onclick = () => {
  wrap.scrollLeft = x(nowDay()) - wrap.clientWidth / 2; reflow();
};
wrap.addEventListener("wheel", e => {
  if (e.ctrlKey || e.metaKey) {
    e.preventDefault();
    setZoom(e.deltaY < 0 ? 1.15 : 1 / 1.15,
      e.clientX - wrap.getBoundingClientRect().left);
  }
}, {passive: false});
$("pillL").onclick = () => {
  const v0 = wrap.scrollLeft / ppd + d0;
  const t = tasks.filter(t => t.endDay <= v0)
    .sort((p, q) => q.endDay - p.endDay)[0];
  if (t) { wrap.scrollLeft = x(t.startDay) - 40; reflow(); }
};
$("pillR").onclick = () => {
  const v1 = (wrap.scrollLeft + wrap.clientWidth) / ppd + d0;
  const t = tasks.filter(t => t.startDay >= v1)
    .sort((p, q) => p.startDay - q.startDay)[0];
  if (t) {
    wrap.scrollLeft = x(t.endDay) - wrap.clientWidth + 40; reflow();
  }
};

// header, legend, table — built once
{
  const c = DATA.counts, bits = [tasks.length + " scheduled"];
  if (c.done) bits.push(c.done + " done");
  if (c.parked) bits.push(c.parked + " parked");
  if (c.containers) bits.push(c.containers + " parent(s) folded");
  bits.push("Σ" + fmtH(tasks.reduce((s, t) => s + t.est, 0)));
  bits.push("planned " + DATA.anchor + " @" + DATA.workers + " workers");
  $("stats").textContent = bits.join(" · ");
  const present = [...new Set(tasks.map(t => t.state))];
  const order = Object.keys(STATES);
  present.sort((p, q) => order.indexOf(p) - order.indexOf(q));
  $("legend").innerHTML = present.map(s => {
    const st = STATES[s];
    return "<span><i" + (st.hollow ? ' class="hollow"' : "") +
      ' style="background:' + (st.hollow ? "transparent" : st.c) +
      '"></i>' + s + "</span>";
  }).join("") + "<span><b></b>now</span>";
  if (DATA.unplanned.length)
    $("note").textContent = "not in the last plan (no bar): " +
      DATA.unplanned.join(", ") + " — re-run plan to schedule them";
  $("tbl").innerHTML =
    "<tr><th>prd</th><th>state</th><th>prio</th><th>est</th>" +
    "<th>wave</th><th>start</th><th>end</th></tr>" +
    tasks.slice().sort((p, q) => q.prio - p.prio ||
      p.startDay - q.startDay).map(t =>
      "<tr><td></td><td>" + t.state + "</td><td>" + t.prio + "</td><td>" +
      fmtH(t.est) + "</td><td>" + (t.wave || "") + "</td><td>" +
      fmtD(t.startDay) + "</td><td>" + fmtD(t.endDay) + "</td></tr>"
    ).join("");
  document.querySelectorAll("#tbl td:first-child").forEach((td, i) =>
    td.textContent = tasks.slice().sort((p, q) => q.prio - p.prio ||
      p.startDay - q.startDay)[i].rel);
}

$("fit").onclick();
$("go").onclick();
setInterval(placeNow, 60000);
</script>
</body>
</html>
"""
