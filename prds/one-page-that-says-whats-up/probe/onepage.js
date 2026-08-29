/* probe — the one-page shape, applied to the live page as a DOM transform.
   No file in the footprint is edited: this proves the layout against the real
   view.css and the real 37-PRD payload before a line of it is committed. */
(() => {
  const $ = id => document.getElementById(id);

  // 1 — the round panel comes out. It is prds/.round.md, git-ignored.
  const round = $("round"); if (round) round.remove();

  // 2 — section 1: the report's opening, in the slot, with its age visible.
  let up = document.getElementById("whatsup");
  if (!up) {
    up = document.createElement("section");
    up.id = "whatsup";
    up.setAttribute("data-sect", "whatsup");
    const anchor = document.querySelector("section[data-view='timeline']");
    anchor.parentNode.insertBefore(up, anchor);
  }

  // 3 — every tab pane becomes a stacked section, in the PRD's order.
  const ORDER = ["timeline", "board", "analytics", "asks", "list", "memos"];
  const host = document.querySelector("section[data-view='timeline']").parentNode;
  for (const v of ORDER) {
    const s = document.querySelector(`section[data-view='${v}']`);
    if (!s) continue;
    s.classList.add("on");            // no pane is hidden any more
    s.style.display = "block";
    host.appendChild(s);              // reorder: analytics right after board
  }
  // the report pane is the source of section 1 now, not a destination
  const rep = document.querySelector("section[data-view='report']");
  if (rep) rep.setAttribute("data-hide", "1");

  // the plan's own toolbar lives OUTSIDE its section in the tabbed page.
  // On a stacked page it must travel with the plan or it floats over
  // whatever section happens to be under it.
  const tc = document.getElementById("tcontrols");
  const tl = document.querySelector("section[data-view='timeline']");
  if (tc && tl) tl.insertBefore(tc, tl.firstChild);

  // 4 — the stage stops being viewport-locked; it gets a real height in flow
  const st = document.createElement("style");
  st.id = "onepage-css";
  st.textContent = `
    section[data-view]{display:block !important;margin:0 0 34px}
    section[data-hide]{display:none !important}
    #stage{height:min(72vh,720px)}
    #whatsup{max-width:760px;margin:0 0 26px}
    #whatsup h2{font-size:19px;font-weight:600;margin:0 0 3px}
    #whatsup .age{font-size:12px;color:var(--ink3);margin:0 0 12px}
    #whatsup .age.stale{color:#b4690e}
    #whatsup p{margin:0 0 10px;line-height:1.55;color:var(--ink2);font-size:14px}
    #whatsup h3{font-size:12px;letter-spacing:.06em;text-transform:uppercase;
      color:var(--ink3);margin:16px 0 5px}
    .sectrule{font-size:11px;letter-spacing:.07em;text-transform:uppercase;
      color:var(--ink3);margin:0 0 9px;padding-top:4px;
      border-top:.5px solid var(--sep)}`;
  document.head.appendChild(st);

  // 5 — a heading over each section, so scrolling has landmarks
  const NAME = {timeline:"the plan", board:"the board", analytics:"the analytics",
                asks:"answered questions", list:"everything, as a table",
                memos:"decisions on record"};
  for (const v of ORDER) {
    const s = document.querySelector(`section[data-view='${v}']`);
    if (!s || s.querySelector(".sectrule")) continue;
    const h = document.createElement("div");
    h.className = "sectrule"; h.textContent = NAME[v];
    s.insertBefore(h, s.firstChild);
  }

  // 6 — fill section 1 from prds/report.md over the endpoint that already exists
  return fetch("/report?board=" + encodeURIComponent(location.pathname.split("/").pop()))
    .then(r => r.json()).then(j => {
      const text = j.text || "";
      const lines = text.split("\n");
      let title = "", date = "", lede = [], inwork = [], planned = [];
      let sec = "lede";
      for (const raw of lines) {
        const l = raw.trim();
        if (/^#\s/.test(l)) { title = l.replace(/^#\s+/, ""); continue; }
        if (/^##\s/.test(l)) {
          const h = l.replace(/^##\s+/, "").toLowerCase();
          sec = h.startsWith("in work") ? "inwork"
              : h.startsWith("planned") ? "planned" : "stop";
          continue;
        }
        if (/^\*[^*].*\*$/.test(l) && !date) { date = l.replace(/^\*|\*$/g, ""); continue; }
        if (!l) { (sec === "lede" ? lede : sec === "inwork" ? inwork : planned).push(""); continue; }
        if (sec === "lede") lede.push(l);
        else if (sec === "inwork") inwork.push(l);
        else if (sec === "planned") planned.push(l);
      }
      const para = arr => arr.join("\n").split(/\n\s*\n/)
        .map(p => p.replace(/\n/g, " ").trim()).filter(Boolean);
      const strip = s => s.replace(/\*\*(.+?)\*\*/g, "$1").replace(/`(.+?)`/g, "$1");
      const first = a => para(a)[0] || "";
      // two or three sentences, never a paragraph — the PRD's own bar. Cut on
      // sentence ends, not on a character count, so it never ends mid-clause.
      const sents = (s, n) => {
        const out = (s.match(/[^.!?]+[.!?]+(\s|$)/g) || [s]).slice(0, n);
        return out.join("").trim();
      };
      up.innerHTML =
        `<h2>${title}</h2>` +
        `<p class="age" id="reportage">${date}</p>` +
        `<p>${sents(strip(first(lede)), 2)}</p>` +
        (inwork.length ? `<h3>in work</h3><p>${sents(strip(first(inwork)), 3)}</p>` : "") +
        (planned.length ? `<h3>next</h3><p>${sents(strip(first(planned)), 2)}</p>` : "");
      return "whatsup filled: " + (title || "(no title)");
    });
})();
