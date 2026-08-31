#!/usr/bin/env node
// page.js <url> — open the served board and print one JSON of what the page
// built for the-page-shows-the-round: the now strip, the round panel, the
// report view, the silent word, ⌘7, and pearde.replace on the two parts.
// Needs playwright-core (NODE_PATH) and a Chrome, like viewtest.js.
let chromium;
try { ({ chromium } = require("playwright-core")); }
catch (e) { console.error("page.js: needs playwright-core"); process.exit(2); }
const url = process.argv[2];
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  const errors = [];
  page.on("pageerror", e => errors.push(String(e.message).split("\n")[0]));
  page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });
  await page.goto(url, { waitUntil: "load" });
  await page.waitForTimeout(900);
  const strip = await page.evaluate(() => {
    const doors = [...document.querySelectorAll("#now .door")];
    return {
      light: !document.querySelector("#now").shadowRoot,
      tag: document.querySelector("#now").tagName.toLowerCase(),
      n: doors.length,
      text: doors.map(d => d.querySelector("b").textContent).join(" · "),
      labels: doors.map(d => d.querySelector("span").textContent),
      dim: doors.filter(d => d.classList.contains("dim")).length,
      dests: doors.map(d => JSON.parse(d.dataset.go)),
      top: document.querySelector("#now").getBoundingClientRect().top,
    };
  });
  const round = await page.evaluate(() => {
    const r = document.querySelector("#round");
    const heads = [...r.querySelectorAll("h5")].map(h => h.textContent.trim());
    return { light: !r.shadowRoot, tag: r.tagName.toLowerCase(),
             shown: getComputedStyle(r).display !== "none",
             heads, text: r.textContent.replace(/\s+/g, " ").trim() };
  });
  // the silent word: hover the held row's bar, read the tooltip
  const silent = await page.evaluate(() => {
    const t = pearde.data.tasks.find(t => t.rel === "building");
    return { field: t ? t.silent : "no task", list: pearde.data.all.length };
  });
  await page.evaluate(() => pearde.apply(pearde.data));
  // open the inspector on `building` and read its facts
  await page.evaluate(() => document.querySelector("[data-go]") && 0);
  await page.evaluate(() => { location.hash = "#prd=building"; });
  await page.waitForTimeout(700);
  const pane = await page.evaluate(() =>
    (document.querySelector("#dbody") || {}).innerText || "");
  // ⌘7 switches to the report view; the seventh tab exists
  const buttons = await page.evaluate(() => [...document.querySelectorAll("#views button")].map(b => b.dataset.v));
  await page.keyboard.press("Escape");
  await page.keyboard.press("Meta+7");
  await page.waitForTimeout(600);
  const report = await page.evaluate(() => {
    const s = document.querySelector('section[data-view="report"]');
    const el = document.querySelector("#report");
    return { view: location.hash, shown: !!s && getComputedStyle(s).display !== "none",
             light: !el.shadowRoot, tag: el.tagName.toLowerCase(),
             h2: [...el.querySelectorAll("h2")].map(h => h.textContent),
             text: el.textContent.replace(/\s+/g, " ").trim().slice(0, 200) };
  });
  // the waiting-on-you door lands on the list filtered to the band
  await page.evaluate(() => pearde.apply(pearde.data));
  const door = await page.evaluate(() => {
    const d = { view: "list", state: "hot" };
    location.hash = "#view=list&state=hot";
    return location.hash;
  });
  await page.waitForTimeout(400);
  const listRows = await page.evaluate(() => [...document.querySelectorAll("#list tr[data-go], #list [data-rel], #list .row")].length);
  // a zero is dimmed, never absent: hand the page a payload with nothing to collect
  const dimmed = await page.evaluate(async () => {
    // a fresh payload off the wire: the page's own is enriched in place and
    // circular after hydrate(), so it cannot be cloned
    const r = await fetch((window.__BASE || "") + "/data?board=" +
      encodeURIComponent(window.__BOARD));
    const p = (await r.json()).payload;
    p.cpm.collect = [];
    pearde.apply(p);
    await document.querySelector("#now").updateComplete;   // Lit renders on a microtask
    const doors = [...document.querySelectorAll("#now .door")];
    return { n: doors.length, dim: doors.filter(d => d.classList.contains("dim")).length,
             text: doors.map(d => d.querySelector("b").textContent).join(" · ") };
  });
  // the round panel swaps within two seconds of the file being rewritten —
  // over the served URL, through the daemon's own live loop
  let swap = null;
  const roundFile = process.argv[3];
  if (roundFile) {
    await page.evaluate(() => pearde.refresh());
    require("fs").writeFileSync(roundFile, "# Round — rewritten\n\n## Owed\n- SECOND-OWED\n");
    const t0 = Date.now();
    let text = "";
    while (Date.now() - t0 < 6000) {
      await page.waitForTimeout(200);
      text = await page.evaluate(() => document.querySelector("#round").textContent);
      if (/SECOND-OWED/.test(text)) break;
    }
    swap = { ms: Date.now() - t0, got: /SECOND-OWED/.test(text) };
  }
  // the two parts are replaceable through pearde.replace — last, because
  // after this the page's own strip and panel are gone
  const replaced = await page.evaluate(async () => {
    class MyNow extends HTMLElement { connectedCallback() { this.textContent = "MINE-NOW"; } }
    class MyRound extends HTMLElement { connectedCallback() { this.textContent = "MINE-ROUND"; } }
    customElements.define("my-now", MyNow); customElements.define("my-round", MyRound);
    pearde.replace("now", "my-now"); pearde.replace("round", "my-round");
    await pearde.refresh();
    return { now: document.querySelector("#now").textContent,
             round: document.querySelector("#round").textContent,
             tags: [document.querySelector("#now").tagName, document.querySelector("#round").tagName] };
  });
  await browser.close();
  console.log(JSON.stringify({ errors, strip, round, silent, pane, buttons, report, replaced, door, listRows, dimmed, swap }, null, 1));
})();
