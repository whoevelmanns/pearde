#!/usr/bin/env python3
"""The view's routes call the transition: `/edit` with `fm.state` and `/new`
go through transitions.py, forced, with `view` on the line. Driven
in-process — the daemon's Handler with a stub socket — so no daemon, no port
and no registry is touched. Prints one line per check and a count."""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "resources", "board"))
import serve  # noqa: E402

D = tempfile.mkdtemp()
B = subprocess.check_output([sys.executable, os.path.join(HERE, "fixture.py"),
                             D], text=True).strip()
b = serve.Board(B)
serve.BOARDS[b.name] = b
# the mirror pass is the daemon's own — it writes .plan.json and the daily
# .history.jsonl row — and is not what this probe measures
serve.mirror = lambda *a, **k: None


class Fake(serve.Handler):
    """The handler with the socket replaced: `path` and a JSON body in,
    (code, body) out. `reply` is captured, `q` is the real one."""
    def __init__(self, path, payload):
        self.path = path
        raw = json.dumps(payload).encode()
        self.headers = {"Content-Length": str(len(raw))}
        self.rfile = io.BytesIO(raw)
        self.out = None

    def reply(self, code, body, ctype="application/json"):
        self.out = (code, body)


def post(path, **payload):
    f = Fake(path, payload)
    f.do_POST()
    return f.out


def state(rel):
    for line in open(os.path.join(B, rel, "prd.md"), encoding="utf-8"):
        if line.startswith("state:"):
            return line.split(":", 1)[1].split("#")[0].strip()


n = ok = 0


def check(name, cond, note=""):
    global n, ok
    n += 1
    ok += bool(cond)
    print(f"  {'ok  ' if cond else 'FAIL'} {name}" + ("" if cond else f"\n       {note}"))


hist_before = open(os.path.join(B, ".history.jsonl"), "rb").read()
real_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    # a drag: next (specced, gated on building) → claimed. A command refuses
    # it; the view is a person and is forced through
    code, body = post("/edit", board=b.name, prd="next", fm={"state": "claimed"})
    line1 = sys.stdout.getvalue()
    sys.stdout = io.StringIO()
    code2, body2 = post("/edit", board=b.name, prd="asking",
                        append="**Q1** *(answered 2026-08-28 15:00)* — red",
                        heading="Answers", fm={"state": "open"})
    line2 = sys.stdout.getvalue()
    sys.stdout = io.StringIO()
    code3, body3 = post("/new", board=b.name, title="From the page",
                        priority=3, body="typed in")
    line3 = sys.stdout.getvalue()
    sys.stdout = io.StringIO()
    code4, body4 = post("/new", board=b.name, title="next")
    code5, body5 = post("/edit", board=b.name, prd="next",
                        fm={"priority": "99"})
finally:
    sys.stdout = real_stdout

print("/edit with fm.state")
check("the drag is forced through: 200 and wrote state", code == 200 and body["wrote"] == ["state"], f"{code} {body}")
check("next is claimed", state("next") == "claimed")
check("the daemon's line says forced · view", "▸ next: specced → claimed · forced · view · " in line1, line1)
check("  …and ends as view", line1.strip().endswith(" · as view"), line1)
check("the answer flow: append then state in one call, 200", code2 == 200 and body2["wrote"] == ["append", "state"], f"{code2} {body2}")
check("asking is open after it", state("asking") == "open")
check("no claim: written by a forced drag", "claim:" not in open(os.path.join(B, "next", "prd.md")).read())
check("a plain fm edit still writes without a transition", code5 == 200 and body5["wrote"] == ["priority"], f"{code5} {body5}")
print("/new")
check("/new files through add: 200 and the rel", code3 == 200 and body3 == {"prd": "from-the-page"}, f"{code3} {body3}")
check("  …state open from the template", state("from-the-page") == "open")
check("  …the line says — → open", "▸ from-the-page: — → open · " in line3, line3)
check("/new on a taken slug is refused with the gate: 409", code4 == 409 and "taken" in body4["error"], f"{code4} {body4}")
print("memory")
rows = [json.loads(l) for l in open(os.path.join(B, ".transitions.jsonl"))]
check("three rows in .transitions.jsonl", len(rows) == 3, str(rows))
hist_after = open(os.path.join(B, ".history.jsonl"), "rb").read()
check(".history.jsonl byte-identical", hist_before == hist_after)
check("transitions.py is in SOURCES", any(s.endswith("transitions.py") for s in serve.SOURCES))
shutil.rmtree(D, ignore_errors=True)
print(f"\n{n} checks · {ok} pass · {n - ok} fail")
sys.exit(0 if ok == n else 1)
