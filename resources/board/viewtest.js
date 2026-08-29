#!/usr/bin/env node
// pearde viewtest — open a rendered board page in a real browser and report
// what it built.
//
//   node viewtest.js <path-to-.view.html>
//   node viewtest.js http://127.0.0.1:8443/board/<name>
//   node viewtest.js --example            a fresh copy of the example board,
//                                         rendered and opened as a file
//
// Give it the served URL as well as the file. They are different code paths —
// the service injects its own head script and live loop — and a page that is
// fine as a file can be broken as a service.
//
// Exit 0 when every check passes, 1 when one fails, 2 when the browser driver
// is missing. It is a development gate, not part of the view: nothing here is
// loaded by the page and the skill ships no dependency.
//
// It needs `playwright-core` and a Chrome. Install the driver wherever you run
// this — `npm i playwright-core` — and it uses the Chrome already on the
// machine. A real browser rather than a DOM shim, because the page is an ES
// module and the common shims skip module scripts silently, reporting a blank
// page as a pass.

let chromium;
try {
  ({ chromium } = require("playwright-core"));
} catch (e) {
  console.error("viewtest: needs playwright-core — npm i playwright-core");
  console.error("viewtest: it drives the Chrome already installed here.");
  process.exit(2);
}

const path = require("path");
const fs = require("fs");
const os = require("os");
const { spawnSync } = require("child_process");

// --example: copy resources/board/example to a temp dir, plan and render it
// there, and open that page. Never the directory itself — a check that ticks
// a box in the example changes what every other check sees. The copy is
// removed on exit; the snapshots it writes under --snap are keyed by the
// board's own name, `example`.
let arg = process.argv[2];
let scratch = null;
if (arg === "--example") {
  scratch = fs.mkdtempSync(path.join(os.tmpdir(), "pearde-example-"));
  fs.cpSync(path.join(__dirname, "example"), scratch, { recursive: true });
  const r = spawnSync("python3", [path.join(__dirname, "plan.py"), "gantt", scratch],
                      { encoding: "utf8" });
  if (r.status !== 0) {
    console.error("viewtest: could not render the example copy\n" + (r.stderr || r.stdout));
    fs.rmSync(scratch, { recursive: true, force: true });
    process.exit(2);
  }
  arg = path.join(scratch, "prds", ".view.html");
  process.on("exit", () => fs.rmSync(scratch, { recursive: true, force: true }));
}
const served = /^https?:\/\//.test(arg || "");
if (!arg || (!served && !fs.existsSync(arg))) {
  console.error("viewtest: node viewtest.js <path-to-.view.html | url | --example>");
  process.exit(2);
}
const file = served ? arg : path.resolve(arg);
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  const errors = [];
  page.on("pageerror", e => errors.push(String(e.message).split("\n")[0]));
  page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });
  page.on("response", r => {
    if (r.status() >= 400) errors.push(`${r.status()} ${r.url()}`);
  });

  // count real canvas work without a stub: wrap the 2D context up front
  await page.addInitScript(() => {
    window.__draws = 0;
    const g = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (...a) {
      const ctx = g.apply(this, a);
      if (!ctx || ctx.__wrapped) return ctx;
      ctx.__wrapped = true;
      for (const k of ["fillRect", "strokeRect", "fillText", "stroke", "fill",
                       "drawImage", "arc", "moveTo", "lineTo", "roundRect"]) {
        const f = ctx[k];
        if (typeof f === "function") ctx[k] = function (...b) { window.__draws++; return f.apply(this, b); };
      }
      return ctx;
    };
  });

  await page.goto(served ? file : "file://" + file, { waitUntil: "load" });
  await page.waitForTimeout(700);

  const r = await page.evaluate(() => {
    const $ = s => document.querySelector(s), q = s => [...document.querySelectorAll(s)];
    const P = window.pearde;
    return {
      lit: window.__litOK === true,
      slot: !!(window.pearde && typeof window.pearde.slot === "function"),
      seams: ["toolbar", "sidebar", "inspector"]
        .every(n => !!document.getElementById("seam-" + n)),
      seamsQuiet: ["toolbar", "sidebar", "inspector"].every(n => {
        const el = document.getElementById("seam-" + n);
        return el.children.length > 0 || getComputedStyle(el).display === "none";
      }),
      pearde: !!P && typeof P === "object",
      data: !!(P && P.data && P.data.cpm),
      board: !!(P && "board" in P),
      refresh: !!(P && typeof P.refresh === "function"),
      apply: !!(P && typeof P.apply === "function"),
      onHold: !!(P && typeof P.onHold === "function"),
      hold: typeof window.__pearde_hold === "function",
      titlebar: !!$("#titlebar"),
      views: q("#views a").length,
      canvas: !!$("#cv"),
      draws: window.__draws,
      land: !!$("#land"),
      frontierIsElement: $("#land")?.tagName.toLowerCase() === "pearde-frontier",
      frontierLightDom: !$("#land")?.shadowRoot,
      frontierRows: $("#land") ? $("#land").querySelectorAll("[data-go]").length : 0,
      stats: (($("#stats") || {}).textContent || "").trim().length,
      drawer: !!$("#drawer"),
      canvasPainted: (() => {
        const c = $("#cv"); if (!c) return false;
        return c.width > 0 && c.height > 0;
      })(),
    };
  });

  const checks = [
    ["no page error", errors.length === 0, errors.slice(0, 2).join(" | ")],
    ["Lit is bound, offline", r.lit, ""],
    ["pearde.slot is callable", r.slot, ""],
    ["all three seams present", r.seams, ""],
    ["an unused seam renders nothing", r.seamsQuiet, ""],
    ["window.pearde published", r.pearde, ""],
    ["pearde.data is the payload", r.data, ""],
    ["pearde.board is the key", r.board, ""],
    ["pearde.refresh callable", r.refresh, ""],
    ["pearde.apply callable", r.apply, ""],
    ["pearde.onHold callable", r.onHold, ""],
    ["hold hook still wired", r.hold, ""],
    ["the toolbar built", r.titlebar, ""],
    ["seven section anchors", r.views === 7, `got ${r.views}`],
    ["the canvas is sized", r.canvasPainted, ""],
    ["the gantt drew", r.draws > 20, `${r.draws} draw ops`],
    ["the frontier column built", r.land, ""],
    ["the frontier is a component", r.frontierIsElement, ""],
    ["it renders into light DOM", r.frontierLightDom, ""],
    ["its rows are doors", r.frontierRows > 0, `${r.frontierRows} doors`],
    ["the stats bar has numbers", r.stats > 0, ""],
    ["the inspector exists", r.drawer, ""],
  ];

  // ── one page, seven sections ───────────────────────────────────────────
  // The three things this page is, asserted rather than eyeballed: the
  // sections are in the PRD's order, every one of them has drawn before
  // anything was clicked, and the page does not scroll sideways on a phone.
  const page1 = await page.evaluate(() => {
    const secs = [...document.querySelectorAll("section[data-view]")];
    const h = e => Math.round(e.getBoundingClientRect().height);
    const head = s => s.querySelector("h2.sect, details.fold > summary");
    return {
      order: secs.map(s => s.dataset.view),
      hidden: secs.filter(s => getComputedStyle(s).display === "none")
                  .map(s => s.dataset.view),
      // a section that never drew is an empty frame: its own height is its
      // heading and nothing else. This is the check that would have caught
      // the one-draw-per-repaint dispatcher.
      undrawn: secs.filter(s => h(s) <= h(head(s) || s) + 4)
                   .map(s => s.dataset.view),
      // and the stronger form: the content is in the DOM even while a fold
      // is shut, so the fold is presentation and the draw is eager
      emptyHosts: secs.filter(s => {
        const host = s.querySelector(
          "pearde-board,pearde-list,pearde-memos,pearde-report,#asks,#tiles");
        return host && host.querySelectorAll("*").length === 0;
      }).map(s => s.dataset.view),
      whatsup: !!document.querySelector("pearde-whatsup"),
      whatsupAbovePlan: (() => {
        const w = document.querySelector("pearde-whatsup");
        const t = document.querySelector('section[data-view="timeline"]');
        return !!w && !!t && (w.compareDocumentPosition(t) &
                              Node.DOCUMENT_POSITION_FOLLOWING) !== 0;
      })(),
      tcontrolsInside: !!document.querySelector(
        'section[data-view="timeline"] #tcontrols'),
      purposeInside: !!document.querySelector(
        'section[data-view="timeline"] #purpose'),
    };
  });
  const ORDER = ["timeline", "board", "analytics", "asks", "list", "memos",
                 "report"];
  checks.push(["the sections are in the PRD's order",
               page1.order.join(",") === ORDER.join(","), page1.order.join(" ")]);
  checks.push(["no section is hidden", page1.hidden.length === 0,
               page1.hidden.join(" ")]);
  checks.push(["every section drew on first load, no click",
               page1.undrawn.length === 0,
               page1.undrawn.length ? "empty frames: " + page1.undrawn.join(" ") : ""]);
  checks.push(["...and a folded section has already drawn its body",
               page1.emptyHosts.length === 0, page1.emptyHosts.join(" ")]);
  checks.push(["the prose section is the first thing above the plan",
               page1.whatsup && page1.whatsupAbovePlan, ""]);
  checks.push(["the plan's toolbar is inside the plan's section",
               page1.tcontrolsInside, ""]);
  checks.push(["the vision line is too", page1.purposeInside, ""]);

  // narrow: the page must not scroll sideways. Before this PRD it did —
  // `body.scrollWidth` 543 against a 390 client, the bar alone 449.
  const wide0 = page.viewportSize();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(400);
  const narrow = await page.evaluate(() => ({
    body: document.body.scrollWidth,
    client: document.documentElement.clientWidth,
    culprits: [...document.querySelectorAll("body *")]
      .filter(e => e.getBoundingClientRect().width >
                   document.documentElement.clientWidth + 1)
      .filter(e => !e.closest("#list"))     // the table scrolls in its own box
      .slice(0, 4)
      .map(e => e.tagName.toLowerCase() + (e.id ? "#" + e.id : "")),
  }));
  checks.push(["at 390px the page does not scroll sideways",
               narrow.body === narrow.client,
               `body ${narrow.body} vs client ${narrow.client}` +
               (narrow.culprits.length ? " — " + narrow.culprits.join(" ") : "")]);
  if (wide0) await page.setViewportSize(wide0);
  await page.waitForTimeout(300);

  for (const v of ["timeline", "board", "asks", "list", "analytics", "memos", "report"]) {
    const before = errors.length;
    await page.click(`#views a[data-v="${v}"]`).catch(e => errors.push(`${v}: ${e.message}`));
    await page.waitForTimeout(120);
    const shown = await page.evaluate(n => {
      const s = document.querySelector(`section[data-view="${n}"]`);
      return !!s && getComputedStyle(s).display !== "none";
    }, v);
    checks.push([`section "${v}" jumps clean`, errors.length === before && shown,
                 errors.slice(before).join(" | ") || (shown ? "" : "section not shown")]);
    // asks reads each PRD over the wire and renders its round as picks. A card
    // that could not read, or a parsed round showing no options, is the view
    // degrading quietly — which is exactly what it used to do.
    if (v === "asks") {
      await page.waitForTimeout(900);
      const a = await page.evaluate(() => {
        const cards = [...document.querySelectorAll(".ask2")];
        return {
          n: cards.length,
          broken: cards.filter(c => /could not read the PRD/.test(c.textContent)).length,
          withPicks: cards.filter(c => c.querySelector(".qq .opt")).length,
          // a round that parsed but rendered no options is the failure mode:
          // a card showing an empty question block answers nothing
          emptyRounds: cards.filter(c =>
            c.querySelector(".qq") && !c.querySelector(".qq .opt")).length,
          // every rendered round must offer a recommendation to take
          recWithoutButton: cards.filter(c =>
            c.querySelector(".qq .rec") && c.querySelector(".act.rec")?.hidden).length,
          // every question answers on its own, and one already written back
          // is not in the inbox at all — it is in the answered panel
          roundsMissingSend: [...document.querySelectorAll("#asks .qq")].filter(q =>
            !q.classList.contains("answered") && !q.querySelector(".qsend")).length,
          answeredStillAsking: document.querySelectorAll("#asks .qq.answered")
            .length,
          panel: !!document.querySelector("#answered .ahd"),
          panelRows: document.querySelectorAll("#answered .adone").length,
          panelUnsorted: (() => {
            // newest first, and an undated answer sorts under the dated ones
            const d = [...document.querySelectorAll("#answered .when")]
              .map(w => w.textContent.trim());
            return d.filter((x, i) => i && d[i - 1] !== "undated" &&
              x !== "undated" && d[i - 1] < x).length;
          })(),
        };
      });
      checks.push(["no ask card failed to read its PRD", a.broken === 0,
                   `${a.broken} of ${a.n}`]);
      checks.push(["no card renders a round with no options", a.emptyRounds === 0,
                   `${a.withPicks} of ${a.n} cards carry picks`]);
      checks.push(["a recommended round offers the one-click take",
                   a.recWithoutButton === 0, ""]);
      checks.push(["every open question has its own submit",
                   a.roundsMissingSend === 0, ""]);
      checks.push(["an answered question has left the inbox",
                   a.answeredStillAsking === 0, ""]);
      checks.push(["the answered panel built", a.panel,
                   `${a.panelRows} answered`]);
      checks.push(["the answered panel is in date order",
                   a.panelUnsorted === 0, `${a.panelUnsorted} out of order`]);
    }
  }

  // --snap <dir> writes each view's DOM; --check <dir> compares against it.
  // A port is provable when every view's markup is unchanged.
  const mode = process.argv[3], dir = process.argv[4];
  if (mode === "--snap" || mode === "--check") {
    fs.mkdirSync(dir, { recursive: true });
    // the board's own name, not its directory — every board's dir is `prds`,
    // so a directory-derived key collides across boards
    const tag = (await page.evaluate(() => (window.pearde && window.pearde.data
      && window.pearde.data.board) || "board")).replace(/[^A-Za-z0-9_.-]/g, "-");
    for (const v of ["timeline", "board", "asks", "list", "analytics", "memos", "report"]) {
      await page.click(`#views a[data-v="${v}"]`).catch(() => {});
      await page.waitForTimeout(150);
      const dom = await page.evaluate(n => {
        const s = document.querySelector(`section[data-view="${n}"]`);
        const land = document.querySelector("#land");
        // Lit stamps a random marker id per page load, the service prints
        // "3s ago", and a claim written at a fixed time renders "holding 40m"
        // that grows with the clock. None is a change to the markup.
        const clean = h => h
          .replace(/lit\$\d+\$/g, "lit$M$")
          .replace(/>[^<]*?\b\d+[smhd] ago\b[^<]*?</g, ">AGO<")
          .replace(/holding \d+(?:\.\d+)?[mh]\b/g, "holding AGO")
          .replace(/\s+/g, " ").trim();
        const text = e => (e ? e.textContent : "").replace(/\s+/g, " ").trim();
        return {
          markup: clean((s ? s.innerHTML : "") + "||" + (land ? land.innerHTML : "")),
          text: (text(s) + " || " + text(land)).replace(/\b\d+[smhd] ago\b/g, "AGO")
            .replace(/holding \d+(?:\.\d+)?[mh]\b/g, "holding AGO"),
        };
      }, v);
      const at = path.join(dir, `${tag}.${v}.html`);
      const atText = path.join(dir, `${tag}.${v}.txt`);
      if (mode === "--snap") {
        fs.writeFileSync(at, dom.markup);
        fs.writeFileSync(atText, dom.text);
      } else {
        for (const [what, file, got] of [["markup", at, dom.markup],
                                          ["text", atText, dom.text]]) {
          const want = fs.existsSync(file) ? fs.readFileSync(file, "utf8") : null;
          checks.push([`view "${v}" ${what} unchanged`, want !== null && want === got,
                       want === null ? "no snapshot"
                         : want === got ? ""
                         : `differs at char ${[...got].findIndex((c, i) => c !== want[i])}`]);
        }
      }
    }
    if (mode === "--snap") console.log(`  snapshots written to ${dir}`);
  }

  await browser.close();
  let bad = 0;
  for (const [name, ok, note] of checks) {
    if (!ok) bad++;
    console.log(`  ${ok ? "ok  " : "FAIL"}  ${name}` + (note ? (ok ? `  (${note})` : `  — ${note}`) : ""));
  }
  console.log(`\n${checks.length - bad}/${checks.length} passed`);
  process.exit(bad ? 1 : 0);
})();
