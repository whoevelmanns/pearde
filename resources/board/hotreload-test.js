#!/usr/bin/env node
/* pearde hot-reload test — a live page must re-import a moved view.js in
   place: no reload, the scroll kept, a half-typed inspector kept. It drives
   the real LIVE_JS loop against a real daemon: open the served page, dirty
   the inspector, then move `view.js` on disk and watch the page notice via
   /wait, re-fetch the payload, and import the fresh module over itself.

   The re-import is proven three ways: the window marker survives (no reload),
   a NEW module instance mounted (the old copy's refresh was stashed on window
   before the move; the page's live refresh is a different object now), and
   the dirty body/scroll the old copy handed over came back.

   Usage: node hotreload-test.js http://127.0.0.1:PORT/board/<name>
   Needs playwright-core and Chrome, like viewtest.js. */
let chromium;
try { ({ chromium } = require("playwright-core")); }
catch (e) {
  console.error("hotreload: needs playwright-core — npm i playwright-core");
  process.exit(2);
}
const fs = require("fs");
const path = require("path");

const url = process.argv[2];
if (!/^https?:\/\//.test(url || "")) {
  console.error("hotreload: usage — node hotreload-test.js <served-board-url>");
  process.exit(2);
}
const VIEW = path.join(__dirname, "view.js");
const orig = fs.readFileSync(VIEW, "utf8");
const PROBE = "\n/* pearde hot-reload probe */\n";

(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  const errors = [];
  page.on("pageerror", e => errors.push(String(e.message).split("\n")[0]));
  page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });
  page.on("response", r => {
    if (r.status() >= 400) errors.push(`${r.status()} ${r.url()}`);
  });

  await page.goto(url, { waitUntil: "load" });
  await page.waitForTimeout(900);

  // stash the CURRENT module instance's refresh where the new instance can
  // leave its own; if the page reloads, everything on window is wiped
  const ready = await page.evaluate(() => {
    if (!(window.pearde && typeof window.pearde.refresh === "function")) {
      return false;
    }
    window.__pearde_old_refresh = window.pearde.refresh;
    window.__hotmark = "still here";
    return true;
  });
  if (!ready) {
    console.error("hotreload: served page has no live pearde — "
                  + "is the daemon running this checkout?");
    process.exit(1);
  }

  // open the inspector on the first PRD the frontier offers, then dirty it:
  // a reload or a data swap would destroy this text — its survival is the
  // whole point of the feature
  const opener = await page.evaluate(() => {
    const doors = [...document.querySelectorAll("#land [data-go]")];
    for (const door of doors) {
      try {
        const d = JSON.parse(door.dataset.go);
        if (d && d.prd) { door.click(); return d.prd; }
      } catch (e) { /* not a door we can read */ }
    }
    return null;
  });
  if (opener === null) {
    console.error("hotreload: no PRD door in the frontier column");
    process.exit(1);
  }
  await page.waitForTimeout(1400);   // the drawer's PRD fetch lands

  const typed = "half-typed body — survive the re-import";
  const setup = await page.evaluate(t => {
    const ta = document.getElementById("dbodytext");
    if (!ta) return { ok: false, why: "no #dbodytext" };
    ta.value = t;
    ta.dispatchEvent(new Event("input", { bubbles: true }));
    const sc = document.getElementById("scroll");
    // the gantt may not overflow this viewport, and then the value clamps —
    // what must survive is whatever scroll the user had, so capture it
    sc.scrollLeft = 99999; sc.scrollTop = 99999;   // hit the end, whatever it is
    return {
      ok: true,
      open: document.getElementById("drawer").classList.contains("open"),
      unsaved: /unsaved/.test(
        document.getElementById("dmsg").textContent || ""),
      sl: Math.round(sc.scrollLeft), st: Math.round(sc.scrollTop),
    };
  }, typed);
  if (!setup.ok || !setup.open || !setup.unsaved) {
    console.error("hotreload: setup failed —", JSON.stringify(setup));
    process.exit(1);
  }

  // move the view's code — a real file change on disk, as an edit would
  fs.appendFileSync(VIEW, PROBE);
  await page.waitForTimeout(5000);   // daemon poll + /wait + data + import

  const after = await page.evaluate(() => {
    const sc = document.getElementById("scroll");
    return {
      mark: window.__hotmark,                          // gone = reload
      oldRefreshStillLive:
        window.pearde && window.pearde.refresh === window.__pearde_old_refresh,
      drawerOpen: document.getElementById("drawer")
        .classList.contains("open"),
      val: document.getElementById("dbodytext")?.value || null,
      dmsg: document.getElementById("dmsg")?.textContent || "",
      sl: sc ? Math.round(sc.scrollLeft) : null,
      st: sc ? Math.round(sc.scrollTop) : null,
    };
  });

  await browser.close();
  fs.writeFileSync(VIEW, orig);      // put the view back exactly as it was
  const noteSuffix = `(sl ${setup.sl}→${after.sl}, st ${setup.st}→${after.st})`;

  const checks = [
    ["no page error or bad response along the way", errors.length === 0,
     errors.slice(0, 2).join(" | ")],
    ["the page never reloaded", after.mark === "still here",
     "window markers wiped — a reload happened"],
    ["a NEW module instance mounted",
     after.oldRefreshStillLive === false,
     "old instance still owns the page — the re-import did not take"],
    ["the inspector is still open", after.drawerOpen, ""],
    ["the half-typed body survived", after.val === typed,
     `got ${JSON.stringify(after.val)}`],
    ["it is still marked unsaved", /unsaved/.test(after.dmsg),
     `dmsg: ${after.dmsg || "(empty)"}`],
    ["the scroll position survived", after.sl === setup.sl &&
        after.st === setup.st, noteSuffix],
  ];
  let bad = 0;
  for (const [name, ok, note] of checks) {
    if (!ok) bad++;
    // notes are the failure story; on a pass, only the scroll check's own
    // before→after is worth printing
    const passNote = ok && name === "the scroll position survived"
      ? ` (${noteSuffix})` : "";
    const failNote = ok ? "" : (note ? `  — ${note}` : "");
    console.log(`  ${ok ? "ok  " : "FAIL"}  ${name}${passNote}${failNote}`);
  }
  console.log(`\n${checks.length - bad}/${checks.length} passed`);
  process.exit(bad ? 1 : 0);
})();
