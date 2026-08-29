#!/usr/bin/env node
// tokens-per-transition — open a rendered page, switch to analytics, print
// what the two cost charts say. Exit 2 without a browser driver.
//   NODE_PATH=<node_modules> node viewcheck.js <path-to-.view.html>
let chromium;
try { ({ chromium } = require("playwright-core")); }
catch (e) { console.error("viewcheck: needs playwright-core"); process.exit(2); }
const path = require("path");
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  const errors = [];
  page.on("pageerror", e => errors.push(String(e.message).split("\n")[0]));
  await page.goto("file://" + path.resolve(process.argv[2]), { waitUntil: "load" });
  await page.waitForTimeout(500);
  await page.click('#views a[data-v="analytics"], #views button[data-v="analytics"]');
  await page.waitForTimeout(200);
  const r = await page.evaluate(() => {
    const charts = [...document.querySelectorAll("#charts .chart")];
    const byTitle = t => charts.find(c => c.querySelector("h3")?.textContent === t);
    const calls = byTitle("Calls per transition"), ref = byTitle("Refusals per session");
    return {
      charts: charts.length,
      calls: calls ? calls.textContent.replace(/\s+/g, " ").trim() : "",
      callsDots: calls ? calls.querySelectorAll("circle").length : -1,
      refusals: ref ? ref.textContent.replace(/\s+/g, " ").trim() : "",
      refusalRows: ref ? ref.querySelectorAll(".brow").length : -1,
    };
  });
  await browser.close();
  console.log(JSON.stringify({ errors, ...r }));
})();
