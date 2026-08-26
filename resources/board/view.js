import { LitElement, html, css } from "lit";
"use strict";
/* ═══════════════════════════════════════════════════════════════════════════
   The page has one datum — the enriched payload — and five readings of it,
   in this order: the data and the tokens, the router that makes every number
   a door, the canvas that draws the plan, the inspector, the four other
   views.
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
  "st-claimed","st-done","crit","ok","float","link","grid","gridw","axis","wash",
  "hi","lo"];
let T = {};
function readTokens() {
  const cs = getComputedStyle(document.documentElement);
  for (const k of TOKENS) T[k] = cs.getPropertyValue("--" + k).trim();
}
readTokens();
const col = s => T[stTok(s)];
/* A PRD whose every acceptance box is closed while a worker still holds it is
   finished and waiting to be taken. It gets its own hue on the chart — the
   same green the column uses, so the bar and the row are one fact. */
const colOf = t => t.collect && !HOT[t.state] ? T.ok : T[stTok(t.state)];
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  readTokens(); draw(); drawMini(); if (view !== "timeline") repaintView();
});

const a = DATA.anchor.split("-").map(Number);
const anchor = new Date(a[0], a[1] - 1, a[2]);
const nowDay = () => (Date.now() - anchor.getTime()) / MS;
const dayDate = d => new Date(a[0], a[1] - 1, a[2] + Math.floor(d));
const fmtD = d => dayDate(d).toLocaleDateString(undefined,
  {month:"short", day:"numeric"});
const fmtW = w => w >= 40 ? Math.round(w) + "w"
  : (Math.round(w * 10) / 10 + "w").replace(".0w", "w");
const fmtHr = h => h >= 40 ? Math.round(h) + "h"   // est/actual records
  : (Math.round(h * 10) / 10 + "h").replace(".0h", "h");
const esc = s => String(s).replace(/[&<>"']/g,
  c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

/* how long a worker has held this PRD, off the `claim:` stamp. Computed in
   the page rather than shipped in the payload: it changes every minute, and
   the board does not write a file every minute. */
function heldFor(t) {
  const c = t.claim, ts = c && c.since ? Date.parse(
    /[Zz]|[+-]\d{2}:?\d{2}$/.test(c.since) ? c.since : c.since + "Z") : NaN;
  if (!c) return "";
  if (isNaN(ts)) return c.who ? " · " + esc(c.who) : "";
  const m = Math.max(0, (Date.now() - ts) / 60000);
  const ago = m < 90 ? Math.round(m) + "m" : (m / 60).toFixed(1) + "h";
  return " · " + (c.who ? esc(c.who) + " " : "") + "holding " + ago;
}

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
   vision: weight along the critical path. 0 is now, the right edge is the
   vision reached, and a bar's position is the soonest it could possibly run.
   dates:  the worker-limited calendar `plan` computed, for a human who wants
   a date. Everything downstream of MODE — grid, bars, minimap, arrows —
   reads u0/u1 and never knows which one it is drawing. */
let MODE, mode = "vision", M, ppu;
function remode() {
  MODE = {
    vision: {
      u0: t => t.es, u1: t => t.ef,
      // the axis is the whole track: the landed weight runs left of zero,
      // now is where done ends and the plan begins, the vision is the edge
      lo: -(CPM.landed || 0) * 1.02 - 1, hi: Math.max(CPM.length, 1) * 1.02 + 1,
      unit: "w", ppu: 9, min: 0.15, max: 400,
      zooms: [["fine", 34], ["mid", 9], ["whole", 2.2]],
      fmt: v => fmtW(v),
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
  tree:  {label:"tree", key:t => t.rel, sort:() => 0},
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
// a board with any shape to it opens as its own shape — the tree holds both
// nesting and, on a master, the member boards. A flat board is a flat list.
let groupBy = (DATA.boards || []).length || ALL.some(a => a.parent)
  ? "tree" : "none";
const collapsed = new Set();
const expanded = new Set();          // tree — branches the user forced open
let treeNodes = [], treeRoots = [];  // the last tree build
let selected = null, filter = "", critOnly = false, readyOnly = false;
// the panel is a preference, not a view — it outlives the reload
let landOpen = true;
try { landOpen = localStorage.getItem("pearde.land") !== "0"; } catch (e) {}
let collectOnly = false;
let stateSel = new Set();          // set by clicking the legend
let hover = -1;                    // row index under the pointer

$("grp").innerHTML = Object.entries(GROUPS)
  .map(([k, g]) => `<option value="${k}">${g.label}</option>`).join("");
$("grp").value = groupBy;

function matches(t) {
  if (critOnly && !t.critical) return false;
  if (readyOnly && !t.ready) return false;
  if (collectOnly && !t.collect) return false;
  if (stateSel.size && !stateSel.has(t.state)) return false;
  if (!filter) return true;
  const f = filter.toLowerCase();
  return t.rel.toLowerCase().includes(f) || t.state.includes(f) ||
    (t.title || "").toLowerCase().includes(f);
}
const anyFilter = () =>
  filter || critOnly || readyOnly || collectOnly || stateSel.size;

/* ── the row list ─────────────────────────────────────────────────────────
   One flat array, rebuilt on grouping, filter and collapse — never on scroll
   and never on zoom. A row that moves under the pointer as you scroll is what
   makes a big chart unreadable, so the order is stable: group, then earliest
   start, then how much the task unblocks. */
let rows = [];
function build() {
  if (groupBy === "tree") return buildTree();
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
  finish(collapsed.size);
}

/* ── the tree ─────────────────────────────────────────────────────────────
   The left column is the board's own shape: a PRD's children sit under it,
   indented, and a branch opens and closes. Two things decide whether a
   branch is open, in this order — what the reader last clicked, and then,
   for every branch they have not touched, whether it has anything inside
   the window they are looking at. A branch whose whole subtree is off to the
   left, already landed, or far out past the right edge is closed: a name
   with nothing under it in view is a row spent on nothing. Pan back over it
   and it opens itself again. */
/* the window, or null when there is none to read. While another view is on,
   the chart is display:none and every width it reports is zero — a window
   that says "nothing is in view" is not a fact about the plan, so the rule
   abstains rather than folding the whole tree away behind the reader. */
function viewU() {
  const w = plot.clientWidth - LEFT;
  if (w <= 0) return null;
  const v0 = scroll.scrollLeft / ppu + M.lo;
  return [v0, v0 + w / ppu];
}
function isOpen(n, win) {
  if (!n.kids.length) return true;
  if (collapsed.has(n.rel)) return false;      // the reader shut it
  if (expanded.has(n.rel)) return true;        // the reader opened it
  // a member board is the reader's one handle on a whole board: it folds
  // only by being asked, never because its work is off-window
  if (n.board) return true;
  if (!win) return n.open !== false;           // no window: stand where we did
  return n.hi >= win[0] && n.lo <= win[1];     // else: is any of it in view
}
function buildTree() {
  rows = [];
  const nodes = new Map();
  const node = rel => {
    let n = nodes.get(rel);
    if (n) return n;
    const row = allByRel.get(rel);
    n = {rel:rel, name:(row && row.name) || rel.split("/").pop(),
         t:byRel.get(rel) || null, kids:[], up:null, depth:0};
    nodes.set(rel, n);
    // the parent is the nearest ancestor path that is itself a PRD — a plain
    // directory in the middle of a rel is structure, not a row
    let p = rel, i;
    while ((i = p.lastIndexOf("/")) >= 0) {
      p = p.slice(0, i);
      if (allByRel.has(p)) { n.up = p; node(p).kids.push(n); break; }
    }
    // on a master, a member's PRDs live under their board — the one node in
    // the tree that is not a PRD, because the board is not one either
    if (!n.up && rel[0] === "@" && rel.includes("/")) {
      const b = rel.slice(0, rel.indexOf("/"));
      n.up = b;
      const r = node(b);
      r.name = b.slice(1);
      r.board = true;
      r.kids.push(n);
    }
    return n;
  };
  for (const t of tasks) if (matches(t)) node(t.rel);
  treeNodes = [...nodes.values()];
  treeRoots = treeNodes.filter(n => !n.up);

  const agg = n => {
    let lo = Infinity, hi = -Infinity, sum = 0, cnt = 0, ncrit = 0;
    if (n.t) {
      lo = M.u0(n.t); hi = M.u1(n.t); sum = n.t.est; cnt = 1;
      ncrit = n.t.critical ? 1 : 0;
    }
    for (const k of n.kids) {
      agg(k);
      lo = Math.min(lo, k.lo); hi = Math.max(hi, k.hi);
      sum += k.sum; cnt += k.n; ncrit += k.ncrit;
    }
    if (!isFinite(lo)) { lo = 0; hi = 0; }
    n.lo = lo; n.hi = hi; n.sum = sum; n.n = cnt; n.ncrit = ncrit;
    n.kids.sort(cmpNode);
  };
  treeRoots.forEach(agg);
  treeRoots.sort(cmpNode);

  const win = viewU();
  let closed = 0;
  const walk = (n, depth) => {
    n.depth = depth;
    n.open = isOpen(n, win);
    if (n.kids.length && !n.open) closed++;
    rows.push(n.t
      ? {kind:"task", t:n.t, key:n.rel, depth:depth,
         kids:n.kids.length, open:n.open, lo:n.lo, hi:n.hi}
      : {kind:"group", key:n.rel, label:n.name, depth:depth,
         kids:n.kids.length, open:n.open, n:n.n, sum:n.sum,
         ncrit:n.ncrit, lo:n.lo, hi:n.hi});
    if (n.open) for (const k of n.kids) walk(k, depth + 1);
  };
  treeRoots.forEach(n => walk(n, 0));
  finish(closed);
}
function cmpNode(p, q) {
  return p.lo - q.lo || (q.ncrit > 0) - (p.ncrit > 0) ||
         q.sum - p.sum || p.rel.localeCompare(q.rel);
}

/* what every build ends with: the counts above the chart, and the geometry */
function finish(closed) {
  const hidden = tasks.length - tasks.filter(matches).length;
  $("inview").innerHTML = tasks.length + " scheduled" +
    (hidden ? lnk(`${hidden} filtered out`, {clear:1}, "clear every filter",
                  "· ") : "") +
    (closed ? lnk(`${closed} collapsed`, {expand:1},
                  "open every branch", "· ") : "");
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
    (dest.hot ? " hot" : "") + (dest.collect ? " got" : "") +
    '" data-go="' + esc(JSON.stringify(dest)) +
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
     crit ready collect group mode   the timeline's own controls
     clear expand            the two undo-doors filters need           */
function go(d) {
  if (d.clear) {
    filter = ""; $("q").value = "";
    critOnly = readyOnly = collectOnly = false;
    stateSel.clear(); syncToggles(); build();
    return toast("filters cleared");
  }
  if (d.expand) {
    collapsed.clear();
    if (groupBy === "tree")
      for (const n of treeNodes) if (n.kids.length) expanded.add(n.rel);
    build();
    return;
  }
  if (d.mode && d.mode !== mode) setMode(d.mode);
  if (d.group && GROUPS[d.group]) {
    groupBy = d.group; $("grp").value = d.group;
    collapsed.clear(); expanded.clear(); lastWin = null; build();
  }
  if (d.crit !== undefined) { critOnly = !!d.crit; syncToggles(); build(); }
  if (d.ready !== undefined) { readyOnly = !!d.ready; syncToggles(); build(); }
  if (d.collect !== undefined) {
    collectOnly = !!d.collect; syncToggles(); build();
  }
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
   the chain that sets the finish — an ink outline with a glow behind it.

   `part` is the one live thing on the page: the fraction of this PRD's
   acceptance boxes an implementer has already closed. The bar is drawn whole
   and then the part NOT yet closed is ghosted back toward the page, so the
   solid length is evidence — checks that ran — and the edge between them
   moves while you watch. */
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
  const part = o.part === undefined ? -1 : Math.max(0, Math.min(1, o.part));
  if (o.ring && part > 0.001) {
    // a ring is a wall, not work in flight — but a wall whose boxes are
    // closing still says how much of it is already built
    ctx.save();
    rr(x0, y, w, h, r); ctx.clip();
    ctx.globalAlpha = (o.dim ? 0.5 : 1) * 0.32;
    ctx.fillStyle = c; ctx.fillRect(x0, y, w * part, h);
    ctx.restore();
  } else if (!o.ring && part >= 0 && part < 0.999) {
    const px = x0 + w * part;
    ctx.save();
    rr(x0, y, w, h, r); ctx.clip();
    ctx.globalAlpha = (o.dim ? 0.5 : 1) * 0.68;
    ctx.fillStyle = T.content;
    ctx.fillRect(px, y, x0 + w - px, h);
    ctx.restore();
    if (part > 0.001) line(px, y + 1, px, y + h - 1, T.ink, 1);
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
  const steps = unit === "w" ? [.5,1,2,4,8,12,24,48,96,168,336]
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
    for (let v = Math.ceil(M.lo / step) * step; v <= M.hi + step; v += step) {
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
    // a branch the reader has shut still says how far its children reach
    if (r.kids && !r.open && r.hi > r.lo)
      drawBar(x(r.lo), Math.max(5, (r.hi - r.lo) * ppu), y + 19, 4,
              T["st-done"], {flat:true});
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
    drawBar(x0, w, y + 6, 14, colOf(t),
            {ring:stRing(t.state), crit:t.critical, dim:dim,
             part:t.held && t.boxes && t.boxes[1] ? t.part : undefined});
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

  /* 5 — the header: the scale */
  ctx.save();
  ctx.beginPath(); ctx.rect(LEFT, 0, W - LEFT, HEAD); ctx.clip();
  ctx.fillStyle = T.content; ctx.fillRect(LEFT, 0, W - LEFT, HEAD);
  if (mode === "vision") {
    for (let v = Math.ceil(M.lo / step) * step; v <= M.hi + step; v += step) {
      text(v === 0 ? "now" : (v > 0 ? "+" : "−") + fmtW(Math.abs(v)),
           x(v) + 4, 33, T.ink3, F.tick);
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
  tag(mode === "vision" ? "vision · " + fmtW(CPM.length) + " of work in front"
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
      const ind = indentOf(r);
      text(r.open ? "▾" : "▸", ind - 1, mid, T.ink3, F.small);
      const meta = r.n + " · " + fmtW(r.sum) + (r.ncrit ? " · " + r.ncrit + "★" : "");
      ctx.font = F.meta;
      const mw = ctx.measureText(meta).width;
      text(fit(r.label || r.key, LEFT - ind - 22 - mw, F.grp),
           ind + 14, mid, T.ink, F.grp);
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
    let cx = indentOf(r);
    // a PRD that is itself a branch carries the caret before its swatch
    if (r.kids) { text(r.open ? "▾" : "▸", cx - 1, mid, T.ink3, F.small);
                  cx += 14; }
    if (stRing(t.state)) {
      rr(cx + 0.75, mid - 3.25, 6.5, 6.5, 2.5);
      ctx.strokeStyle = colOf(t); ctx.lineWidth = 1.5; ctx.stroke();
    } else {
      rr(cx, mid - 4, 8, 8, 3); ctx.fillStyle = colOf(t); ctx.fill();
    }
    cx += 15;
    // finished work still open on the board: the mark that says "this one is
    // yours to close", and the only glyph on the column that asks for an act
    if (t.collect) { text("✓", cx, mid, T.accent, F.small); cx += 12; }
    else if (t.critical) { text("★", cx, mid, T.ink, F.small); cx += 12; }
    // in flight, the boxes ARE the meta: how much of the contract stands.
    // The weight is already what is left of it, so printing both would
    // count the same work twice
    const meta = t.held && t.boxes && t.boxes[1]
      ? t.boxes[0] + "/" + t.boxes[1]
      : fmtW(t.est) + (t.unblocks ? " ▸" + fmtW(t.unblocks) : "");
    ctx.font = F.meta;
    const mw = ctx.measureText(meta).width;
    text(fit(t.name, LEFT - cx - mw - 20, F.cell), cx, mid,
         sel ? T.ink : T.ink, F.cell);
    text(meta, LEFT - 12, mid, T.ink3, F.meta, true);
    ctx.restore();
    if (y + ROW > HEAD)
      line(indentOf(r), y + ROW, LEFT, y + ROW, T["sep-2"]);
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
    tasks.length + " scheduled PRDs, " + fmtW(CPM.length) +
    " of work to the vision. The list view is the same data as a table.");
}

/* how far in a row sits, and how wide the part of it that toggles is */
const indentOf = r => 12 + (r.depth || 0) * 13;
const caretHit = (r, px) => r.kids && px < indentOf(r) + 14;

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
   makes a dependency graph unreadable. One row's kin is a fact you can hold. */
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
    mctx.fillStyle = colOf(t);
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

/* ── open and shut ────────────────────────────────────────────────────────
   A click is a decision, and it outlives the window: once the reader has
   opened or shut a branch, the visible-area rule stops speaking for it. */
function toggleRow(r) {
  const k = r.key;
  if (r.open) { collapsed.add(k); expanded.delete(k); }
  else { expanded.add(k); collapsed.delete(k); }
  build();
}
/* the window moved — reopen what came into view, shut what left it. Rows
   are otherwise never rebuilt on scroll, so this runs only when the answer
   for at least one untouched branch actually changed. */
let lastWin = null;
function retree() {
  if (groupBy !== "tree") return;
  const win = viewU();
  if (!win) return;                    // hidden: there is nothing to read yet
  if (lastWin && Math.abs(lastWin[0] - win[0]) < 1e-6 &&
      Math.abs(lastWin[1] - win[1]) < 1e-6) return;
  lastWin = win;
  for (const n of treeNodes)
    if (n.kids.length && n.open !== isOpen(n, win)) return build();
}

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
    tw.clear(); retree(); place();
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
    if (groupBy === "tree" && !caretHit(h.row, h.px)) {
      const t = taskFor(h.row.key);
      if (t) return openDrawer(t);
    }
    toggleRow(h.row);
  } else if (groupBy === "tree" && h.zone === "cell" &&
             caretHit(h.row, h.px)) {
    selected = h.row.t; toggleRow(h.row);
  } else {
    selected = h.row.t; draw(); openDrawer(h.row.t);
  }
});
scroll.addEventListener("scroll", () => { retree(); schedule(); },
                        {passive:true});
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
  const u = v => (v < 0 ? "−" : "+") + fmtW(Math.abs(v));
  const when = t.past
    ? `${u(t.es)} → ${u(t.ef)} — landed, behind now`
    : t.parked
      ? "parked at now — in a state the loop does not work"
      : mode === "vision"
        ? `${u(t.es)} → ${u(t.ef)} along the path`
        : `${fmtD(t.startDay)} → ${fmtD(t.endDay)}`;
  tip.innerHTML =
    '<div class="t"></div><div class="r rel"></div>' +
    '<div class="r"><span class="k">state</span> <span class="' +
      (HOT[t.state] ? "warn" : "") + '">' + esc(t.state) + "</span>" +
    ' · <span class="k">prio</span> ' + t.prio +
    ' · <span class="k">weight</span> ' + fmtW(t.est) +
    (t.after && t.after.length ? ' · <span class="k">after</span> ' +
      esc(t.after.map(d => d.split("/").pop()).join(", ")) + " (footprint)" : "") +
    (t.board ? ' · <span class="k">board</span> ' + esc(t.board) : "") +
    "</div>" +
    '<div class="r">' + when + "</div>" +
    (t.past || t.parked ? "" :
      '<div class="r">' + (t.critical
        ? "★ critical — every unit of weight cut here moves the vision closer"
        : '<span class="k">float</span> ' + fmtW(t.slack) +
          " before it becomes critical") + "</div>" +
      '<div class="r"><span class="k">unblocks</span> ' + fmtW(t.unblocks) +
        " across " + t.downstream + " PRD(s)" +
        (t.ready ? ' · <span class="k">ready now</span>' : "") + "</div>") +
    (t.held && t.boxes && t.boxes[1] ?
      '<div class="r"><span class="k">boxes</span> ' + t.boxes[0] + "/" +
        t.boxes[1] + " closed" + heldFor(t) + "</div>" : "") +
    (t.collect ?
      '<div class="r"><span class="k">✓ collect</span> every box closed — ' +
        "commit it and set done, and " + (t.downstream || "no") +
        " PRD(s) behind it move</div>" : "") +
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
  retree();
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
  lastWin = null;
  retree();
  place();
}

/* ═══ the column ═══════════════════════════════════════════════════════════
   What to do next, beside the plan rather than above it — a column has the
   one axis this list wants, and it neither pushes the gantt down nor truncates
   the frontier behind a "+N more".

   Three questions, in the order that answers them cheapest first:

     to collect  finished work still open on the board. Closing one costs a
                 commit and can open a whole frontier, which no dispatch can do
     ready now   the dispatch frontier — everything startable this second,
                 biggest door first. This IS the dispatch order
     to land     a lane branch main has never seen, whose PRD the board calls
                 finished. In flight underneath it: lanes still being worked

   Nothing is truncated here; the column scrolls.                            */
/* ── the frontier column, as an element ───────────────────────────────────
   What to do next: finished work to collect, the dispatch frontier, and the
   lanes main has not seen. A custom element rather than a string of HTML, so
   a board can register its own for the same job.

   Light DOM, not shadow. view.css carries 41 rules aimed at `#land .cap`,
   `#land .lrow` and their kin, and the stylesheet is the only place a colour
   is written down. A shadow root would cut every one of them off. */
class PeardeFrontier extends LitElement {
  static properties = { data: {}, cpm: {}, open: { type: Boolean } };
  createRenderRoot() { return this; }

  cap(label, n, dest, why, hue) {
    return html`<button class="cap" data-go=${JSON.stringify(dest)} title=${why}
      >${label}<span class="n ${hue && n ? "on" : ""}">${n}</span></button>`;
  }
  // the state mark: `st` carries the ink, `stRing` decides outline or fill
  mark(st) {
    return html`<span class="st" title=${st}
      style=${stRing(st) ? "border-color:" + stVar(st) : "background:" + stVar(st)}
    ></span>`;
  }
  // why a row is worth the eye: blocked or asking beats finished, finished
  // beats critical, and most rows are none of those and stay graphite
  rail(t, got) {
    return HOT[t.state] === undefined
      ? (got ? " got" : t.critical ? " crit" : "")
      : (t.state === "question" ? " ask" : " hot");
  }
  door(t, big) {
    return t.unblocks
      ? html`<span class="door ${big ? "big" : ""}"
          title="weight this unblocks downstream">▸${fmtW(t.unblocks)}</span>`
      : "";
  }
  bar(b) {
    return b[1]
      ? html`<span class="track ${b[0] === b[1] ? "full" : ""}"
          ><span style=${"width:" + (b[0] / b[1] * 100).toFixed(1) + "%"}></span
          ></span><span>${b[0]}/${b[1]}</span>`
      : "";
  }
  row(t, extra, cls) {
    return html`<button class="lrow${cls}" data-go=${JSON.stringify({prd: t.rel})}
      title=${(t.title || t.name) + " · " + t.state}>
      <div class="top">${this.mark(t.state)}${t.critical
        ? html`<span class="tick" title="on the critical chain">★</span>` : ""}
        <span class="nm">${t.name}</span></div>
      <div class="meta">${extra}</div></button>`;
  }
  lane(r) {
    return html`<button class="lrow ${r.ready ? "got" : "flight"}"
      data-go=${JSON.stringify({prd: r.rel})}
      title=${r.branch + (r.title ? " — " + r.title : "")}>
      <div class="top">${this.mark(r.state)}${r.ready
        ? html`<span class="tick">✓</span>` : ""}
        <span class="nm">${r.name}</span></div>
      <div class="meta">${r.board ? html`<span class="bd">${r.board}</span>` : ""}${
        r.boxes[1] ? this.bar(r.boxes)
                   : html`<span>${r.orphan ? "no PRD" : r.state}</span>`}</div>
      </button>`;
  }

  render() {
    if (!this.open || !this.data) return html``;
    const C = this.cpm || {};
    const collect = (C.collect || []).map(r => byRel.get(r)).filter(Boolean);
    const ready = (C.ready || []).map(r => byRel.get(r)).filter(Boolean);
    const all = this.data.landing || [], repos = this.data.repos || [];
    const land = all.filter(r => r.ready), flight = all.filter(r => !r.ready);
    // the biggest door in the frontier sets the ramp: anything worth half of
    // it is a door too, and says so in ink
    const top = Math.max(0, ...ready.map(t => t.unblocks || 0));
    const big = t => top > 0 && (t.unblocks || 0) >= top / 2;

    return html`<div class="rows">
      ${collect.length ? html`
        ${this.cap("to collect", collect.length, {view: "timeline", collect: 1},
                   "finished work waiting to be committed and closed", true)}
        ${collect.map(t => this.row(t,
            html`<span class="tick">✓</span>${this.bar(t.boxes)}${this.door(t, big(t))}`,
            this.rail(t, true)))}` : ""}

      ${this.cap("ready now", ready.length, {view: "timeline", ready: 1},
                 "everything dispatchable this second — this is the dispatch order")}
      ${ready.length
        ? ready.map(t => this.row(t,
            html`<span>${fmtW(t.est)}</span>${this.door(t, big(t))}`,
            this.rail(t, false)))
        : html`<div class="none">${tasks.length
            ? "nothing — every PRD left waits on another"
            : "nothing scheduled — run plan"}</div>`}

      ${all.length || repos.length ? html`
        ${this.cap("to land", land.length, {view: "timeline"},
                   "a lane branch main has never seen, whose PRD is finished", true)}
        ${land.length
          ? html`<div class="why">done and tested here — main has never seen it</div>`
          : ""}
        ${land.length ? land.map(r => this.lane(r))
          : html`<div class="none">${all.length
              ? "nothing finished yet — the lanes below are still open"
              : "nothing held back: every lane is merged"}</div>`}
        ${flight.length ? html`
          <div class="sub">in flight · ${flight.length}</div>
          ${flight.map(r => this.lane(r))}` : ""}` : ""}
    </div>
    ${repos.length ? html`<div class="feet">${repos.map(r => html`
      <div><b>${String(r.board)}</b>${r.ahead === null
        ? html`<span class="n">no remote</span>`
        : r.ahead
          ? html`<span class="n up"
              title="commits on main that origin has not got">↑${r.ahead}</span>`
          : html`<span class="n in">in sync</span>`}</div>`)}</div>` : ""}`;
  }
}
customElements.define("pearde-frontier", PeardeFrontier);

function drawSide() {
  const el = $("land");
  el.classList.toggle("off", !landOpen);
  el.open = landOpen;
  el.cpm = CPM;
  el.data = DATA;
}

function syncToggles() {
  $("landtog").classList.toggle("on", landOpen);
  $("onlycrit").classList.toggle("on", critOnly);
  $("onlyready").classList.toggle("on", readyOnly);
  $("onlycollect").classList.toggle("on", collectOnly);
  $("onlycollect").hidden = !(CPM.collect || []).length;
}

/* ── controls ─────────────────────────────────────────────────────────── */
$("mVision").onclick = () => setMode("vision");
$("mDates").onclick = () => setMode("dates");
$("zi").onclick = () => glide(ppu * 1.4);
$("zo").onclick = () => glide(ppu / 1.4);
$("ce").onclick = () => {
  if (groupBy === "tree") {
    const any = treeNodes.some(n => n.kids.length && n.open);
    expanded.clear(); collapsed.clear();
    for (const n of treeNodes) if (n.kids.length)
      (any ? collapsed : expanded).add(n.rel);
    return build();
  }
  const g = GROUPS[groupBy];
  if (collapsed.size) collapsed.clear();
  else for (const t of tasks) if (matches(t) && g.key(t) !== "")
    collapsed.add(g.key(t));
  build();
};
$("grp").onchange = () => { groupBy = $("grp").value;
                            collapsed.clear(); expanded.clear();
                            lastWin = null; build(); };
$("q").oninput = () => { filter = $("q").value.trim(); build(); };
$("onlycrit").onclick = () => { critOnly = !critOnly; syncToggles(); build(); };
$("onlyready").onclick = () => { readyOnly = !readyOnly; syncToggles(); build(); };
$("landtog").onclick = () => {
  landOpen = !landOpen;
  try { localStorage.setItem("pearde.land", landOpen ? "1" : "0"); } catch (e) {}
  syncToggles(); drawSide(); resize(); place();   // the plot just changed width
};
/* ── the board switcher ───────────────────────────────────────────────────
   Every board the daemon watches, under the title of the one you are on. The
   list comes from /status at open time rather than from the payload: the
   payload knows a master's members, the daemon knows every board registered,
   and those are not the same set. A page served from a file has no daemon to
   ask, so the chevron does not appear at all.                              */
let picksOpen = false;

async function boards() {
  try {
    const r = await fetch(API + "/status");
    return (await r.json()).boards || [];
  } catch (e) { return []; }
}

function drawPicks(list) {
  list = list.slice().sort((a, b) => a.name.localeCompare(b.name));
  const mine = list.filter(b => (b.members || []).length);
  const flat = list.filter(b => !(b.members || []).length);
  const row = b =>
    '<button class="b' + (b.name === BOARD_KEY ? " on" : "") +
    '" role="option" aria-selected="' + (b.name === BOARD_KEY) +
    '" data-b="' + esc(b.name) + '" title="' + esc(b.path) + '">' +
    '<span class="tick">' + (b.name === BOARD_KEY ? "✓" : "") + "</span>" +
    '<span class="nm">' + esc(b.name) + "</span>" +
    (b.last_error ? '<span class="n bad" title="' + esc(b.last_error) +
       '">error</span>'
     : (b.members || []).length
       ? '<span class="n">' + b.members.length + " boards</span>" : "") +
    "</button>";
  $("picks").innerHTML = list.length
    ? (mine.length ? '<div class="hd">merged</div>' + mine.map(row).join("") +
        (flat.length ? '<div class="sep"></div>' : "") : "") +
      flat.map(row).join("")
    : '<div class="hd">no other board registered</div>';
}

async function openPicks() {
  if (!SERVED) return;
  picksOpen = true;
  $("pick").setAttribute("aria-expanded", "true");
  $("picks").hidden = false;
  drawPicks(await boards());
}

function closePicks() {
  picksOpen = false;
  $("pick").setAttribute("aria-expanded", "false");
  $("picks").hidden = true;
}

$("pick").onclick = e => {
  e.stopPropagation();
  picksOpen ? closePicks() : openPicks();
};
$("picks").onclick = e => {
  const b = e.target.closest("[data-b]");
  if (!b) return;
  if (b.dataset.b === BOARD_KEY) return closePicks();
  location.href = API + "/board/" + encodeURIComponent(b.dataset.b);
};
document.addEventListener("click", e => {
  if (picksOpen && !e.target.closest("#picks, #pick")) closePicks();
});

$("onlycollect").onclick = () => {
  collectOnly = !collectOnly; syncToggles(); build();
};

let rt = 0;
addEventListener("resize", () => {
  clearTimeout(rt);
  rt = setTimeout(() => { resize(); retree(); place(); movePill(); }, 60);
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
  else if (e.key === "b") $("pick").click();
  else if (e.key === "c") $("onlycrit").click();
  else if (e.key === "r") $("onlyready").click();
  else if (e.key === "l") $("landtog").click();
  else if (e.key === "x") $("onlycollect").click();
  else if (e.key === "+" || e.key === "=") glide(ppu * 1.4);
  else if (e.key === "-") glide(ppu / 1.4);
  else if (e.key === "Escape") {
    if (picksOpen) closePicks();
    else if ($("drawer").classList.contains("open")) closeDrawer();
    else if (anyFilter()) go({clear:1});
    else { selected = null; draw(); }
  }
});

function focusTask(t) {
  selected = t;
  openDrawer(t);
  if (byRel.has(t.rel)) {
    if (view !== "timeline") setView("timeline");
    if (groupBy === "tree") {
      for (let r = t.rel, i; (i = r.lastIndexOf("/")) >= 0; ) {
        r = r.slice(0, i);
        if (allByRel.has(r)) { collapsed.delete(r); expanded.add(r); }
      }
    } else collapsed.delete(GROUPS[groupBy].key(t));
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
  const planned = tasks.filter(t => !t.past && !t.parked);
  const cal = Math.max(...planned.map(t => t.endDay), 0) * (DATA.dayHours || 8);
  const bits = [];
  const S = '<span class="sep">·</span>';
  // the whole track first: how far along the chain the board already is
  if (CPM.landed) {
    const track = CPM.landed + CPM.length;
    bits.push(lnk("<b>" + Math.round(CPM.landed / track * 100) +
                  "%</b> of the track", {view:"timeline", mode:"vision"},
                  fmtW(CPM.landed) + " landed behind now, " +
                  fmtW(CPM.length) + " of chain ahead — the axis is the " +
                  "whole track, done work left of zero"));
  }
  bits.push(lnk("<b>" + planned.length + "</b> left", {view:"list", state:"live"},
                "every PRD still to do, as a table"));
  bits.push(lnk('<span class="crit"><b>' + fmtW(CPM.length) +
                "</b> to the vision</span>",
                {view:"timeline", crit:1, mode:"vision"},
                "the chain that sets the finish — nothing else moves it"));
  bits.push(lnk("Σ" + fmtW(CPM.total) + " of work", {view:"analytics"},
                "how the work is distributed"));
  bits.push(lnk("peak <b>" + CPM.peak + "</b> agents",
                {view:"timeline", mode:"dates"},
                "the fastest path wants this many at its widest — " +
                "the calendar is what " + DATA.workers + " workers costs"));
  if (cal > CPM.length * 1.05)
    bits.push(lnk("at " + DATA.workers + " workers: " + fmtW(cal),
                  {view:"timeline", mode:"dates"}));
  const collect = (CPM.collect || []).map(r => byRel.get(r)).filter(Boolean);
  if (collect.length)
    bits.push(lnk('<b>' + collect.length + "</b> to collect",
                  {view:"timeline", collect:1, mode:"vision"},
                  "finished work still open — commit it and set it done, " +
                  "and everything behind it moves"));
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
    "<kbd>r</kbd> ready · <kbd>x</kbd> collect · <kbd>f</kbd> fit · " +
    "<kbd>↑↓</kbd> select</span>";
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
// the live page updates itself on every board change. It must not do that
// while someone is halfway through typing into this panel, and a board's own
// script may hold it too — see `pearde.onHold`.
const HOLDS = [() => dDirty];
window.__pearde_hold = () => HOLDS.some(f => f());

// one `## Heading` section out of a body, ending at the next heading
/* The wall's heading is written by whoever hit it — `## Blocked on a human
   with a browser` is the same section as `## Blocked`. Matched by prefix, so
   only the exact-name lookups stay strict. */
function sectionLike(body, prefix) {
  const re = new RegExp("^##\\s+" + prefix + "\\b[^\\n]*$", "im");
  const m = re.exec(body || "");
  if (!m) return "";
  const rest = body.slice(m.index + m[0].length);
  const nxt = rest.search(/^##\s+/m);
  return (nxt < 0 ? rest : rest.slice(0, nxt))
    .replace(/<!--[\s\S]*?-->/g, "").trim();
}

function section(body, name) {
  const re = new RegExp("^##\\s+" + name + "\\s*$", "im");
  const m = re.exec(body || "");
  if (!m) return "";
  const rest = body.slice(m.index + m[0].length);
  const nxt = rest.search(/^##\s+/m);
  return (nxt < 0 ? rest : rest.slice(0, nxt))
    .replace(/<!--[\s\S]*?-->/g, "").trim();
}

/* ── questions as questions ───────────────────────────────────────────────
   drill.md's round format, parsed: `### Q1: title`, the fork as prose, then
   exactly three prepared answers as a numbered list, one `(recommended)`.
   Parsed here so answering is a pick — the analyst writes the three, the
   user's job is one click or their own words. A section that does not parse
   falls back to raw text and a textarea, so every PRD gets answered.       */
function parseQuestions(txt) {
  if (!txt) return null;
  const re = /^###\s+(Q?\d+[a-z]?)\s*[:.—-]?\s*(.*)$/gim;
  const marks = [];
  let m;
  while ((m = re.exec(txt)))
    marks.push({i: m.index, end: m.index + m[0].length,
                id: m[1].toUpperCase().startsWith("Q") ? m[1] : "Q" + m[1],
                title: m[2].trim()});
  const blocks = marks.length
    ? marks.map((mk, k) => ({id: mk.id, title: mk.title,
        body: txt.slice(mk.end, k + 1 < marks.length ? marks[k + 1].i
                                                     : txt.length).trim()}))
    : [{id: "Q1", title: "", body: txt.trim()}];
  const qs = [];
  for (const b of blocks) {
    const at = b.body.search(/^1[.)]\s/m);
    const issue = (at < 0 ? b.body : b.body.slice(0, at)).trim();
    const opts = [];
    if (at >= 0)
      for (const part of b.body.slice(at).split(/^(?=\d+[.)]\s)/m)) {
        const om = /^(\d+)[.)]\s+([\s\S]*)$/.exec(part.trim());
        if (!om) continue;
        let text = om[2].trim();
        const rec = /\((?:recommended|default)\)\s*$/i.test(text);
        text = text.replace(/\s*\((?:recommended|default)\)\s*$/i, "").trim();
        let label = "";
        const lm = /^\*\*(.+?)\*\*\s*[—–:-]*\s*([\s\S]*)$/.exec(text);
        if (lm) { label = lm[1].trim(); text = lm[2].trim() || lm[1].trim(); }
        opts.push({label, text, rec});
      }
    qs.push({id: b.id, title: b.title, issue, opts});
  }
  // parsed means pickable: without options there is nothing to click, and
  // the raw <pre> + textarea says that more honestly than an empty card
  return qs.some(q => q.opts.length) ? qs : null;
}

function questionsHTML(qs, prefix) {
  return qs.map((q, i) => {
    const name = prefix + "-" + i;
    return '<div class="qq" data-qid="' + esc(q.id) + '">' +
      '<div class="qt">' + esc(q.id) + (q.title ? " · " + esc(q.title) : "") +
      "</div>" +
      (q.issue ? '<div class="qi">' + esc(q.issue) + "</div>" : "") +
      q.opts.map((o, j) =>
        '<label class="opt"><input type="radio" name="' + name +
        '" value="' + j + '"' + (o.rec ? " checked" : "") + '><span class="ot">' +
        (o.label ? "<b>" + esc(o.label) + "</b>" +
          (o.text !== o.label ? " — " : "") : "") +
        (o.text !== o.label || !o.label ? esc(o.text) : "") +
        (o.rec ? '<span class="rec">recommended</span>' : "") +
        "</span></label>").join("") +
      '<label class="opt own"><span class="ohd"><input type="radio" name="' +
      name + '" value="own"><span class="ot">your own answer</span></span>' +
      '<textarea placeholder="in your words — typing here picks this"></textarea>' +
      "</label>" +
      '<div class="qfoot"><button class="act qsend" data-qi="' + i +
      '">answer ' + esc(q.id) + '</button>' +
      '<span class="qdone">answered</span></div></div>';
  }).join("");
}

/* Check the recommended option on every question that has one. The radios
   render pre-checked, so this only matters after a reader has changed some —
   and it is the one click that says "the analyst was right". */
function takeRecommended(root) {
  for (const qq of root.querySelectorAll(".qq")) {
    const rec = qq.querySelector(".opt .rec");
    if (rec) rec.closest(".opt").querySelector("input").checked = true;
  }
}

function wireQuestions(root, qs, send) {
  // typing an own answer is picking it — nobody types a sentence they do not
  // mean, and forcing the radio first loses the first keystroke
  for (const ta of root.querySelectorAll(".qq .opt.own textarea"))
    ta.addEventListener("input", () => {
      const r = ta.closest(".opt").querySelector("input");
      if (ta.value.trim()) r.checked = true;
    });
  if (!send) return;
  // each question answers on its own. The round only reopens the PRD once
  // nothing in it is left unanswered — answering Q1 must not lose Q2.
  root.querySelectorAll(".qq .qsend").forEach(btn => {
    btn.onclick = async () => {
      const el = btn.closest(".qq");
      const i = +btn.dataset.qi;
      const text = answerText(el, qs[i]);
      if (!text) { toast("Pick an answer or write one", true); return; }
      btn.disabled = true;
      const ok = await send("**" + qs[i].id + "** — " + text, () =>
        [...root.querySelectorAll(".qq")].every(x =>
          x === el || x.classList.contains("answered")));
      btn.disabled = false;
      if (ok) markAnswered(el);
    };
  });
}

/* Which questions are already answered is on disk, not in this page: an
   answer writes `**Q1** — …` under `## Answers`. Reading it back means a
   redraw, a reload and a second reader all agree, and nothing is answered
   twice. */
function markAnsweredFrom(root, qs, answers) {
  if (!answers) return;
  const done = new Set();
  const re = /^\s*\*\*(Q?[\w-]+)\*\*/gim;
  let m;
  while ((m = re.exec(answers))) done.add(m[1].toUpperCase());
  root.querySelectorAll(".qq").forEach((el, i) => {
    const id = (qs[i] && qs[i].id || el.dataset.qid || "").toUpperCase();
    if (done.has(id)) markAnswered(el);
  });
}

function markAnswered(el) {
  el.classList.add("answered");
  for (const inp of el.querySelectorAll("input, textarea, button"))
    inp.disabled = true;
}

function answerText(el, q) {
  const pick = el.querySelector("input:checked");
  if (!pick) return "";
  if (pick.value === "own")
    return el.querySelector(".opt.own textarea").value.trim();
  const o = q.opts[+pick.value];
  return (o.label && o.text !== o.label ? o.label + " — " : "") + o.text;
}

function collectAnswers(root, qs) {
  // `**Q1** — <the decision>` per drill.md; a question left unpicked is left
  // unanswered — the orchestrator re-asks what remains, it never guesses
  const out = [];
  root.querySelectorAll(".qq").forEach((el, i) => {
    const q = qs[i];
    if (el.classList.contains("answered")) return;   // already written
    const text = answerText(el, q);
    if (!text) return;
    out.push("**" + q.id + "** — " + text);
  });
  return out.join("\n\n");
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
  const facts = t.plain ? [["weight", fmtW(t.est)], ["prio", t.prio],
                          ["state", t.state], ["not in the plan", "—"]] : [
    ["weight", fmtW(t.est)], ["prio", t.prio],
    ["after", t.after && t.after.length
      ? t.after.map(d => d.split("/").pop()).join(", ") : "—"],
    ["starts", "+" + fmtW(t.es)], ["ends", "+" + fmtW(t.ef)],
    ["float", t.critical ? "★ critical" : fmtW(t.slack)],
    ["unblocks", fmtW(t.unblocks) + " · " + t.downstream + " PRD(s)"],
    ["dates", fmtD(t.startDay) + " → " + fmtD(t.endDay)],
  ];
  // the run's own record, when there is one to read
  if (!t.plain && t.held && t.boxes && t.boxes[1])
    facts.push(["boxes", t.boxes[0] + "/" + t.boxes[1] + " closed" +
                         heldFor(t).replace(/^ · /, " · ")]);
  let h = '<h4>state</h4><div class="fields">' +
    '<select id="dstate">' + STATE_LIST.map(s =>
      `<option${s === t.state ? " selected" : ""}>${s}</option>`).join("") +
    "</select>" +
    '<input type="number" id="dprio" step="1" value="' + t.prio + '">' +
    "</div>";
  h += '<h4>plan</h4><div class="facts">' + facts.map(([k, v]) =>
    `<span>${k} <b>${esc(v)}</b></span>`).join("") + "</div>";
  if (t.collect)
    h += '<h4>collect</h4><p class="hint2">Every acceptance box is closed. ' +
      "Commit the footprint and set this <b>done</b> — " +
      (t.downstream ? t.downstream + " PRD(s) behind it are waiting on that."
                    : "it is the last of its chain.") + "</p>";
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
  let dQs = null;
  if (d) {
    const qs = section(d.body, "Questions");
    dQs = parseQuestions(qs);
    if (t.state === "question" || qs)
      h += '<div class="ask"><h5>' +
        (t.state === "question" ? "waiting on you" : "questions") + "</h5>" +
        (dQs ? questionsHTML(dQs, "dq")
             : (qs ? "<pre>" + esc(qs) + "</pre>" : "") +
               '<textarea class="say" id="dsay" placeholder="the answer — ' +
               'numbered to match"></textarea>') +
        '<div class="row2">' +
        '<button id="danswer">answer &amp; reopen</button>' +
        (dQs && dQs.some(x => x.opts.some(o => o.rec))
          ? '<button id="drec">take the recommended</button>' : "") +
        '<span class="hint">writes ## Answers, reopens once the round is ' +
        'answered</span></div></div>';
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
  if (d && d.specs && d.specs.length) {
    const bx = d.specs.reduce((a2, sp) =>
      [a2[0] + ((sp.boxes || [0, 0])[0]), a2[1] + ((sp.boxes || [0, 0])[1])],
      [0, 0]);
    h += "<h4>specs · " + d.specs.length +
      (bx[1] ? " · " + bx[0] + "/" + bx[1] + " boxes closed" : "") + "</h4>" +
      d.specs.map(sp => {
        const b2 = sp.boxes || [0, 0];
        return `<div class="spec"><div>${esc(sp.title)}</div>` +
          (b2[1] ? '<div class="track2"><span style="width:' +
            (b2[0] / b2[1] * 100).toFixed(1) + '%"></span></div>' : "") +
          `<div class="f">${esc(sp.file)}` +
          (b2[1] ? " · " + b2[0] + "/" + b2[1] : "") +
          `${sp.state ? " · " + esc(sp.state) : ""}</div></div>`;
      }).join("");
  }
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
  if (ansBtn) {
    const askEl = ansBtn.closest(".ask");
    if (dQs) {
      markAnsweredFrom(askEl, dQs, section(d.body, "Answers"));
      wireQuestions(askEl, dQs, (text, isLast) =>
        answerOne(dTask.rel, text, isLast()));
    }
    const send = () => answer(dTask.rel,
      dQs ? collectAnswers(askEl, dQs) : $("dsay").value);
    ansBtn.onclick = send;
    const recBtn = $("drec");
    if (recBtn) recBtn.onclick = () => { takeRecommended(askEl); send(); };
  }
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

/* One question of a round, written on its own. The PRD reopens only on the
   last one — answering Q1 must not set the PRD `open` and take Q2 off the
   asks view with it. */
async function answerOne(rel, text, last) {
  const body = {append: text, heading: "Answers"};
  if (last) body.fm = {state: "open"};
  const out = await save(rel, body);
  toast(out.error ? "Not saved — " + out.error
        : last ? "Answered — " + rel.split("/").pop() + " is open again"
               : "Answered — the rest of the round still waits",
        !!out.error);
  if (out.error) return false;
  prdCache.delete(rel);
  if (last) {
    const row = allByRel.get(rel);
    if (row) row.state = "open";              // optimistic, until /data lands
    refresh();
  }
  return true;
}

/* the one write the board is waiting for */
async function answer(rel, text) {
  text = (text || "").trim();
  if (!text) {
    toast("Nothing to send — pick an answer or write one", true);
    return {error: "nothing to say"};
  }
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
    unblocks: 0, downstream: 0, startDay: 0, endDay: 0, after: [],
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
  if (replaced.has(view)) return;   // a board's own element draws itself
  if (view === "board") drawBoard();
  else if (view === "list") drawList();
  else if (view === "asks") drawAsks();
  else if (view === "analytics") drawAnalytics();
  else if (view === "memos") drawMemos();
  else { resize(); retree(); place(); }
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
  $("inview").style.display = v === "timeline" ? "" : "none";
  repaintView();
  syncHash();
}
for (const b of $("views").querySelectorAll("button"))
  b.onclick = () => setView(b.dataset.v);

/* ── board ─────────────────────────────────────────────────────────────── */
/* ── the board, as an element ─────────────────────────────────────────────
   Kanban by state, one column each, a card per PRD. Drag a card to write its
   `state:` — the drop is the edit, applied optimistically and reconciled by
   the save. Light DOM keeps every `#board .col` rule in the one stylesheet. */
class PeardeBoard extends LitElement {
  static properties = { rows: {}, served: { type: Boolean } };
  createRenderRoot() { return this; }

  async drop(e, st) {
    e.preventDefault();
    e.currentTarget.classList.remove("over");
    const rel = e.dataTransfer.getData("text/plain");
    const row = allByRel.get(rel);
    if (!row || row.state === st) return;
    row.state = st;                       // optimistic: the drop is the edit
    drawBoard();
    const out = await save(rel, { fm: { state: st } });
    if (out.error) toast("Not saved — " + out.error, true);
    else { prdCache.delete(rel); refresh(); }
  }

  card(r) {
    const t = byRel.get(r.rel);
    return html`<div class="card" draggable=${this.served} data-rel=${r.rel}
      @click=${() => { const x2 = taskFor(r.rel); if (x2) openDrawer(x2); }}
      @dragstart=${e => { e.dataTransfer.setData("text/plain", r.rel);
                          e.currentTarget.classList.add("drag"); }}
      @dragend=${e => e.currentTarget.classList.remove("drag")}
      ><div class="t">${t && t.critical ? html`<span class="star">★ </span>` : ""
      }${r.title || r.name}</div><div class="m">${
        r.board ? html`<span class="chip">${r.board}</span>` : ""
      }<span>p${r.prio}</span>${
        r.weight ? html`<span>${fmtW(r.weight)}</span>` : ""}</div></div>`;
  }

  column(st, rowsIn) {
    const w = rowsIn.reduce((a, r) => a + (r.weight || 0), 0);
    const CAP = st === "done" ? 40 : 200;
    return html`<div class="col ${rowsIn.length ? "" : "bare"}" data-state=${st}
      @dragover=${e => { e.preventDefault(); e.currentTarget.classList.add("over"); }}
      @dragleave=${e => e.currentTarget.classList.remove("over")}
      @drop=${e => this.drop(e, st)}
      ><h3 data-go=${JSON.stringify({ view: "list", state: st })}
        title=${st + " as a table"}><i class=${stRing(st) ? "ring" : ""}
        style=${(stRing(st) ? "color:" : "background:") + stVar(st)}></i>${st
        }<span class="n">${rowsIn.length}${w ? " · " + fmtW(w) : ""
        }</span></h3><div class="cards">${rowsIn.slice(0, CAP).map(r => this.card(r))}${
        rowsIn.length > CAP
          ? html`<div class="card" style="cursor:pointer" draggable="false"
              data-go=${JSON.stringify({ view: "list", state: st })}
              ><div class="m">+${rowsIn.length - CAP} more — the list has all of them</div></div>`
          : ""}</div></div>`;
  }

  render() {
    const cols = new Map();
    for (const s of STATE_ORDER) cols.set(s, []);
    for (const r of this.rows || []) {
      if (!cols.has(r.state)) cols.set(r.state, []);  // a state of the user's own
      cols.get(r.state).push(r);
    }
    const out = [];
    for (const [st, rowsIn] of cols) {
      if (!rowsIn.length && !STATE_ORDER.includes(st)) continue;
      rowsIn.sort((p, q) => q.prio - p.prio || p.rel.localeCompare(q.rel));
      out.push(this.column(st, rowsIn));
    }
    return out;
  }
}
customElements.define("pearde-board", PeardeBoard);

function drawBoard() {
  const el = $("board");
  el.served = SERVED;
  el.rows = ALL;
  el.requestUpdate();
}

/* ── asks: the board waiting on a person ──────────────────────────────────
   `question` means an agent stopped and wants an answer. `blocked` means it
   hit a wall. Both are the board waiting on you. This is the inbox: the
   question as written, and the box that answers it — the same two edits
   (`## Answers`, state back to open) the orchestrator makes when the answer
   is typed at a terminal.                                                  */
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
        (r.weight ? " · " + fmtW(r.weight) : "") +
        // what answering it releases: the reason to take this one first
        (t.unblocks ? " · unblocks " + fmtW(t.unblocks) +
          (t.downstream ? " · " + t.downstream + " PRD" +
            (t.downstream === 1 ? "" : "s") : "") : "") +
        "</div></div>" +
      '<span class="flag' + (blocked ? " blocked" : "") + '">' +
        (blocked ? "blocked" : "question") + "</span></div>" +
      '<div class="q skel">reading the PRD…</div>' +
      (SERVED ? '<div class="foot"><textarea placeholder="' +
        (blocked ? "what unblocks it — this goes in as the answer"
                 : "the answer — numbered to match") + '"></textarea>' +
      '<div class="row2"><button class="act send primary">answer &amp; reopen' +
      '</button>' + '<button class="act rec" hidden>take the ' +
        'recommended</button>' + (blocked
        ? '<button class="act reopen">just reopen</button>' : "") +
      '<span class="hint">writes ## Answers · reopens once the round is ' +
      'answered</span>' +
      "</div></div>"
        : '<div class="foot"><span class="hint">read-only — open this board ' +
          "through the service to answer here</span></div>") + "</div>";
  }).join("");
  el.querySelectorAll(".ask2").forEach((card, ci) => {
    const rel = card.dataset.rel;
    const blocked = asks[ci].state === "blocked";
    const box = card.querySelector("textarea");
    const send = card.querySelector(".send");
    if (!SERVED) {
      card.querySelector(".q").textContent =
        "the question is in the PRD — open this board through the service to " +
        "read and answer it here";
      return;
    }
    let cardQs = null;                    // parsed round, once the PRD loads
    const fire = async only => {
      send.disabled = true;
      const out = only === "reopen"
        ? await save(rel, {fm: {state: "open"}})
        : await answer(rel, cardQs ? collectAnswers(card, cardQs) : box.value);
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
    // the question text itself, read live out of the PRD. A round in
    // drill.md's format renders as picks — the fork, three prepared answers,
    // an own-answer box per question — and the card's one textarea goes
    // away: the options carry their own
    fetchPrd(rel).then(d => {
      // the frontmatter the payload does not carry, the way the inspector
      // shows it — what breaks if this is answered wrong
      const blast = d.fm && d.fm["blast-radius"];
      if (blast) {
        const line = card.querySelector(".rel");
        if (line) line.textContent += " · " + blast + " blast";
      }
      const q = card.querySelector(".q");
      const qtxt = section(d.body, "Questions") ||
        (blocked ? sectionLike(d.body, "Blocked") : "");
      cardQs = parseQuestions(qtxt);
      q.classList.remove("skel");
      if (cardQs) {
        q.style.display = "none";
        const holder = document.createElement("div");
        holder.className = "qs";
        holder.innerHTML = questionsHTML(cardQs, "aq-" + esc(rel));
        q.after(holder);
        markAnsweredFrom(holder, cardQs, section(d.body, "Answers"));
        wireQuestions(holder, cardQs, async (text, isLast) => {
          const last = isLast();
          const ok = await answerOne(rel, text, last);
          if (ok && last) {
            card.classList.add("gone");
            setTimeout(() => { if (view === "asks") drawAsks(); },
                       reduced ? 0 : 280);
          }
          return ok;
        });
        if (box) box.style.display = "none";
        // every question the analyst recommended an answer to, in one click
        const rec = card.querySelector(".act.rec");
        if (rec && cardQs.some(x => x.opts.some(o => o.rec))) {
          rec.hidden = false;
          rec.onclick = () => { takeRecommended(holder); fire(); };
        }
        return;
      }
      const txt = qtxt || sectionLike(d.body, "Blocked") ||
        section(d.body, "Notes") || (d.body || "").slice(0, 700);
      q.textContent = txt || "(the PRD says nothing yet)";
    }).catch(err => {
      // say which PRD and why — a bare "could not read" hides the cause
      console.error("asks: " + rel + " — " + (err && err.message || err));
      const q = card.querySelector(".q");
      q.textContent = "could not read the PRD — " + (err && err.message || err);
    });
  });
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

/* ── the list, as an element ──────────────────────────────────────────────
   All of it, sortable and filterable, one row per PRD. Light DOM so the table
   keeps its rules from the one stylesheet, and the header and rows carry
   their own handlers rather than being re-bound after every paint. */
const LIST_COLS = [["rel", "prd"], ["state", "state"], ["prio", "prio"],
                   ["weight", "weight"], ["actual", "actual"], ["board", "board"],
                   ["unblocks", "unblocks"]];

class PeardeList extends LitElement {
  static properties = { rows: {}, by: {}, desc: { type: Boolean } };
  createRenderRoot() { return this; }

  sortBy(k) {
    listDesc = listBy === k ? !listDesc : true;
    listBy = k;
    drawList();
  }
  render() {
    const rowsOut = this.rows || [];
    if (!rowsOut.length)
      return html`<div class="none">nothing matches${
        listState || listBoard || listQ
          ? html` — <button class="lnk"
              data-go=${JSON.stringify({state: null, board: null, q: ""})}
              >clear the filters</button>` : ""}</div>`;
    // no whitespace between cells: a text node inside a <tr> is stray, and
    // the table this replaces emitted none
    const th = ([k, l]) => html`<th data-k=${k} class=${listBy === k ? "by" : ""
      } @click=${() => this.sortBy(k)}>${l}${
      listBy === k ? (listDesc ? " ↓" : " ↑") : ""}</th>`;
    const tr = r => {
      const t = byRel.get(r.rel) || {};
      return html`<tr class="r" data-rel=${r.rel} @click=${() => {
        const x2 = taskFor(r.rel); if (x2) openDrawer(x2); }}><td><i
        class=${stRing(r.state) ? "ring" : ""} style=${
        (stRing(r.state) ? "color:" : "background:") + stVar(r.state)
        }></i>${r.rel}</td><td><span class="st ${
        r.state === "question" ? "warn" : HOT[r.state] ? "danger" : ""
        }">${r.state}</span></td><td>${r.prio}</td><td>${
        r.weight ? fmtW(r.weight) : ""}</td><td>${
        r.actual ? fmtHr(r.actual) : ""}</td><td>${
        r.board || ""}</td><td>${t.unblocks ? fmtW(t.unblocks) : ""}</td></tr>`;
    };
    return html`<table><thead><tr>${LIST_COLS.map(th)}</tr></thead><tbody>${
      rowsOut.map(tr)}</tbody></table>`;
  }
}
customElements.define("pearde-list", PeardeList);

function drawList() {
  const rowsOut = listRows().sort((p, q) => {
    const k = listBy;
    const A = k === "unblocks" ? ((byRel.get(p.rel) || {}).unblocks || 0) : p[k];
    const B = k === "unblocks" ? ((byRel.get(q.rel) || {}).unblocks || 0) : q[k];
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
  const el = $("list");
  el.rows = rowsOut; el.by = listBy; el.desc = listDesc;
  $("lcount").textContent = rowsOut.length + " of " + ALL.length +
    " · click a row for the PRD";
}
$("lq").oninput = () => { listQ = $("lq").value; drawList(); };

/* ── memos: the board's decisions, read where the work is ─────────────── */
let memosLoaded = null;
/* ── memos, as an element ─────────────────────────────────────────────────
   The board's decisions, read where the work is. Light DOM, so view.css keeps
   styling `.memo` and its parts from the one stylesheet. */
class PeardeMemos extends LitElement {
  static properties = { memos: {}, served: { type: Boolean } };
  createRenderRoot() { return this; }
  render() {
    if (!this.served)
      return html`<div class="blank">memos are read live — open this board
        through the service to see them</div>`;
    const ms = this.memos || [];
    if (!ms.length)
      return html`<div class="blank">no memos yet — a decision gets one when
        there is a decision</div>`;
    return ms.map(m => html`<div class="memo">
      <h3>${m.subject || m.slug}</h3>
      <div class="f"><b>${m.slug}</b> · ${m.kind || ""} · ${m.status || ""} ·
        ${m.date || ""}${m.prds && m.prds.length ? html` · governs ${
          m.prds.map(pr => html`<button class="lnk"
            data-go=${JSON.stringify({prd: pr})}>${pr}</button> `)}` : ""}</div>
      <pre>${(m.body || "").slice(0, 3000)}</pre></div>`);
  }
}
customElements.define("pearde-memos", PeardeMemos);

async function drawMemos() {
  const el = $("memos");
  el.served = SERVED;
  if (!SERVED) return;
  if (!memosLoaded) {
    try {
      const r = await fetch(API + "/memos?board=" + encodeURIComponent(BOARD_KEY));
      memosLoaded = (await r.json()).memos || [];
    } catch (e) { memosLoaded = []; }
  }
  el.memos = memosLoaded;
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
  const wLeft = live.reduce((a, r) => a + (r.weight || 0), 0);
  const pct = Math.round(done.length /
    Math.max(ALL.length - parked.length, 1) * 100);
  const ready = tasks.filter(t => t.ready).length;
  const collectN = tasks.filter(t => t.collect).length;
  const waiting = ALL.filter(r => r.state === "question").length;
  const blocked = ALL.filter(r => r.state === "blocked").length;
  const cal = Math.max(...tasks.map(t => t.endDay), 0) * (DATA.dayHours || 8);
  $("tiles").innerHTML =
    tile("done", pct + "%", done.length + " of " +
         (ALL.length - parked.length) + " PRDs", {view:"list", state:"done"}) +
    tile("left", live.length, fmtW(wLeft) + " of weight",
         {view:"list", state:"live"}) +
    tile("to the vision", fmtW(CPM.length),
         "of " + fmtW(CPM.total) + " in the plan",
         {view:"timeline", crit:1, mode:"vision"}) +
    tile("peak agents", CPM.peak, "at " + DATA.workers + " workers: " +
         fmtW(cal), {view:"timeline", mode:"dates"}) +
    tile("ready now", ready, "dispatchable this second",
         {view:"timeline", ready:1, mode:"vision"}) +
    tile("to collect", collectN, "finished — commit and close",
         {view:"timeline", collect:1, mode:"vision"}, collectN > 0) +
    tile("waiting on you", waiting + blocked,
         waiting + " question · " + blocked + " blocked", {view:"asks"},
         waiting + blocked > 0);

  // 1 — where the work sits
  const byState = [];
  for (const st of STATE_ORDER.concat(
        [...new Set(parked.map(r => r.state))])) {
    const rowsIn = ALL.filter(r => r.state === st);
    if (rowsIn.length) byState.push({k: st, v: rowsIn.length,
      h: rowsIn.reduce((a, r) => a + (r.weight || 0), 0)});
  }
  // 2 — where the weight is: members on a master, top-level trees otherwise
  const master = (DATA.boards || []).length;
  const key = master ? (r => r.board || DATA.board)
                     : (r => r.rel.split("/")[0]);
  const groups = new Map();
  for (const r of live) groups.set(key(r), (groups.get(key(r)) || 0) + (r.weight || 0));
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
    "weight · click a state for its list</p>" +
    bars(byState, r => stVar(r.k), r => r.v + (r.h ? " · " + fmtW(r.h) : ""),
         r => ({view:"list", state:r.k})) + "</div>" +

    '<div class="chart"><h3>Where the weight is</h3>' +
    '<p class="sub">' + (master ? "weight left per member board"
      : "weight left per top-level tree") + "</p>" +
    (byGroup.length ? bars(byGroup, (r, i) => CAT[i % CAT.length],
      r => fmtW(r.v), r => master ? {view:"list", board:r.k, state:"live"}
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

    '<div class="chart"><h3>Weight left over time</h3>' +
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
  g += `<text class="lbl" x="${W - 4}" y="${H - 8}" text-anchor="end">est ${fmtHr(mx)}</text>`;
  g += `<text class="lbl" x="4" y="14">actual ${fmtHr(mx)}</text>`;
  for (const r of rowsIn)
    g += `<circle class="dot" cx="${X(r.est).toFixed(1)}" cy="${Y(r.actual).toFixed(1)}" r="4.5"` +
      ` data-rel="${esc(r.rel)}"><title>${esc(r.name)} — est ${fmtHr(r.est)}, actual ${fmtHr(r.actual)}</title></circle>`;
  return g + "</svg>";
}

function burndown(h) {
  const W = 460, H = 220, pad = 34;
  const mx = Math.max(...h.map(r => r.hleft || 0), 1);
  const X = i => pad + (h.length < 2 ? 0 : i / (h.length - 1)) * (W - pad - 8);
  const Y = v => H - pad - v / mx * (H - pad - 12);
  const pts = h.map((r, i) => `${X(i).toFixed(1)},${Y(r.hleft || 0).toFixed(1)}`);
  let g = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="weight left over time">`;
  g += `<line class="ax" x1="${pad}" y1="${H - pad}" x2="${W - 4}" y2="${H - pad}"/>`;
  if (h.length >= 4)
    g += `<polygon class="area" points="${X(0).toFixed(1)},${H - pad} ${pts.join(" ")} ${X(h.length - 1).toFixed(1)},${H - pad}"/>`;
  g += `<polyline class="line" points="${pts.join(" ")}"/>`;
  h.forEach((r, i) => {
    g += `<circle class="dot" cx="${X(i).toFixed(1)}" cy="${Y(r.hleft || 0).toFixed(1)}" r="3.5">` +
      `<title>${esc(r.d)} — ${fmtW(r.hleft || 0)} left, ${r.done} done</title></circle>`;
  });
  g += `<text class="lbl" x="${pad}" y="${H - 10}">${esc(h[0].d)}</text>`;
  g += `<text class="lbl" x="${W - 4}" y="${H - 10}" text-anchor="end">${esc(h[h.length - 1].d)}</text>`;
  g += `<text class="lbl" x="4" y="14">${fmtW(mx)}</text>`;
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
   worker reports, the planner re-orders. The daemon's change notice fetches
   the payload and swaps it in: the rows move, nothing else does. A reload
   would throw away the scroll, the zoom, the selection and whatever is
   half-typed.                                                              */
let refreshing = null;
async function refresh() {
  if (!SERVED) return;
  if (refreshing) return refreshing;
  refreshing = (async () => {
    try {
      const r = await fetch(API + "/data?board=" + encodeURIComponent(BOARD_KEY));
      const out = await r.json();
      if (out.payload) apply(out.payload);
    } catch (e) { /* the daemon went away. The page still reads fine */ }
    refreshing = null;
  })();
  return refreshing;
}

function apply(payload) {
  if (!payload || !payload.cpm) return;      // an unenriched payload is stale
  const keepRel = selected ? selected.rel : null;
  const sx = scroll.scrollLeft, sy = scroll.scrollTop;
  DATA = payload;
  slotsApply();          // a board's own elements see every swap too
  hydrate();
  remode(); M = MODE[mode];
  if (!GROUPS[groupBy]) groupBy = "none";
  selected = keepRel ? byRel.get(keepRel) || null : null;
  lastWin = null;
  build();
  scroll.scrollLeft = sx; scroll.scrollTop = sy;
  retree();
  drawHeader(); drawLegend(); drawSide();
  memosLoaded = null;
  if (view !== "timeline") repaintView();
  if (dTask) {                                  // keep the inspector honest
    const t = taskFor(dTask.rel);
    if (t && !dDirty) { dTask = t; drawBody(); }
  }
}
// the daemon's live loop calls this when the board's sequence moves
// Lit is bound and usable — the harness reads this
window.__litOK = typeof LitElement === "function";

window.__pearde_apply = apply;
window.__pearde_refresh = refresh;

/* ── seams: where a board's own elements render ────────────────────────────
   A board registers a custom element for a seam and the page renders it,
   passing the payload down as `data` and updating it on every swap. The
   browser owns the element contract, so this file does not invent one — it
   only says where an element goes and when its data changes. */
const SEAMS = ["toolbar", "sidebar", "inspector"];
const slotted = [];

function slot(name, tag) {
  if (!SEAMS.includes(name)) return;          // an unknown seam is ignored
  const host = $("seam-" + name);
  if (!host) return;
  const el = document.createElement(tag);
  el.data = DATA;
  host.appendChild(el);
  slotted.push(el);
  return el;
}

/* Replacing a view outright. A custom element name is unique per document, so
   a board cannot define its own `pearde-list` over ours — it registers a
   different element for the view instead, and the page hands that element the
   view rather than drawing its own. */
const VIEWS_REPLACEABLE = ["board", "asks", "list", "analytics", "memos"];
const replaced = new Set();

function replace(view, tag) {
  if (!VIEWS_REPLACEABLE.includes(view)) return;
  const section = document.querySelector(`section[data-view="${view}"]`);
  if (!section) return;
  const el = document.createElement(tag);
  el.data = DATA;
  section.replaceChildren(el);
  replaced.add(view);          // the built-in draw for it stops running
  slotted.push(el);            // it sees every payload swap like any other
  if (view === currentView()) repaintView();
  return el;
}

function currentView() { return view; }

// every slotted element sees the payload the page is drawing
function slotsApply() { for (const el of slotted) el.data = DATA; }

// The surface a board's own `view.user.js` may use. The `__pearde_*` globals
// above stay: serve.py injects LIVE_JS into this page and calls them by name.
window.pearde = {
  slot,
  replace,
  get data() { return DATA; },   // a getter — `apply` replaces the payload
  get board() { return BOARD_KEY; },
  refresh,
  apply,
  onHold(f) { HOLDS.push(f); },
};

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
  if (view === "timeline" && collectOnly) p.push("collect=1");
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
    else if (k === "collect") d.collect = 1;
    else if (k === "q") d.q = v;
  }
  if (Object.keys(d).length) go(d);
}
addEventListener("hashchange", () => { if (!hashLock) readHash(); });

/* ── boot ──────────────────────────────────────────────────────────────── */
resize();
if (!SERVED) $("pick").classList.add("solo");
syncToggles();
setMode("vision");
drawHeader();
drawLegend();
drawSide();
readHash();
// the clock ticks for two reasons: the calendar's now-line, and how long a
// worker has been holding a PRD. Both are read off Date.now(), so both go
// stale between board changes if nothing repaints.
setInterval(() => {
  if (mode === "dates" || tasks.some(t => t.held)) draw();
}, 60000);
if (SERVED) setInterval(refresh, 90000);   // a floor under the live loop
