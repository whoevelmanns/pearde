#!/usr/bin/env node
// The view's half of "## Done when", without a browser: pull the three
// functions that turn a `## Questions` section into the asks card out of
// view.js, run them over the clean fixture question, and assert what a person
// sees. viewtest.js needs playwright-core and a Chrome; this needs neither, so
// it can be the spec's verify command.
//
//   node viewprobe.js        exit 0 when the card is clean
const fs = require("fs");
const path = require("path");
const src = fs.readFileSync(
  path.join(__dirname, "../../../../resources/board/view.js"), "utf8");

function grab(name) {
  const at = src.indexOf("function " + name + "(");
  if (at < 0) throw new Error("view.js has no function " + name);
  let i = src.indexOf("{", at), depth = 0;
  for (let j = i; j < src.length; j++) {
    if (src[j] === "{") depth++;
    else if (src[j] === "}" && --depth === 0)
      return src.slice(at, j + 1);
  }
  throw new Error("unbalanced " + name);
}

const esc = s => String(s).replace(/[&<>"']/g,
  c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const scope = {esc};
for (const n of ["stripAnchor", "parseQuestions", "questionsHTML"])
  scope[n] = new Function("esc", "stripAnchor", "parseQuestions",
    "questionsHTML", "return (" + grab(n) + ")")(
      esc, scope.stripAnchor, scope.parseQuestions, scope.questionsHTML);

const section = `
### Q1: What the page shows first

You are choosing what a person sees first when they open the board: the work
in progress, or the questions waiting on them. Whichever is first is what
they will act on; the other needs a click?

1. **Questions first** — the page opens on what is waiting on you; the work is one click away. (recommended)
2. **Work first** — the page opens on what is happening; your questions are one click away.
3. **Ask each time** — the page remembers whichever you opened last.

<!-- for the board: serve.py \`/\` default route; the-page-shows-the-round spec02 -->
`;

const qs = scope.parseQuestions(section);
const html = qs ? scope.questionsHTML(qs, "aq") : "";
const fails = [];
if (!qs) fails.push("the clean question did not parse into a pickable card");
if (qs && qs.length !== 1) fails.push("parsed " + qs.length + " questions, want 1");
if (qs && qs[0].opts.length !== 3)
  fails.push("parsed " + qs[0].opts.length + " answers, want 3");
if (/for the board:|serve\.py|spec02|&lt;!--/.test(html))
  fails.push("the technical anchor reached the card");
if (!/or write your own/.test(html))
  fails.push("the card does not say `or write your own`");
if (!/class="rec"/.test(html))
  fails.push("the recommended answer is not marked");
if (scope.stripAnchor("a <!-- x --> b") !== "a  b")
  fails.push("stripAnchor left a comment behind");

if (fails.length) { for (const f of fails) console.error("viewprobe: " + f);
  process.exit(1); }
console.log("viewprobe: the asks card is clean — no anchor, three answers, " +
            "recommended marked, `or write your own` shown");
