---
complexity: 3
workflow: implement-a-spec
footprint:
  - resources/board/serve.py
---

# spec02 — the daemon serves `.round.md` and `report.md`

`GET /round?board=<name>` and `GET /report?board=<name>` answer
`{"text": <the file or null>, "path": <where it was read>}`, read from disk
on each call like `/prd`. Neither is parsed by the daemon: the page renders
the text. An absent file is `null`, which the page draws as nothing.

## What already stands

The probe left both routes in `resources/board/serve.py` — one branch
`if path in ("/round", "/report")` before `/wait`, and two lines in the
module docstring's HTTP API list between `/prd` and `/memos`. `ROUTES` was
not touched: the branch answers before that tuple is consulted. The live
daemon re-exec'd on the edit and eight other boards stayed up. Nothing is
left to write unless a check fails.

## Acceptance

Fixture: a copy of the example board registered on the running daemon with
`python3 resources/board/serve.py ensure $D/b/prds` — a temp path registers
but never persists — and unregistered at the end with `POST /unregister`.

- [x] `GET /round?board=<name>` on the copy with no `.round.md` is `200` and `text` is `null`
- [x] after writing `$D/b/prds/.round.md`, the same call returns the file's text, first line intact — no restart, no sync call
- [x] `GET /report?board=<name>` behaves the same over `$D/b/prds/report.md`
- [x] `GET /round?board=no-such` is `404`
- [x] `python3 resources/board/serve.py status` says `up` and `curl -s http://127.0.0.1:8443/board/<name> | head -c 200` returns the page, after the edit

## Verify and Proof

```sh
D=$(mktemp -d); python3 resources/board/plan.py example $D/b >/dev/null; python3 resources/board/serve.py ensure $D/b/prds
N=$(curl -s http://127.0.0.1:8443/status | python3 -c "import json,sys;print([b['name'] for b in json.load(sys.stdin)['boards'] if b['path']=='$D/b/prds'][0])")   # resources/board/serve.py keys it
curl -s "http://127.0.0.1:8443/round?board=$N"                    # resources/board/serve.py /round → {"text": null, ...}
printf '# Round — x\n\n## Owed\n- y\n' > $D/b/prds/.round.md; curl -s "http://127.0.0.1:8443/round?board=$N" | head -c 80   # resources/board/serve.py reads the file
curl -s -o /dev/null -w '%{http_code}\n' "http://127.0.0.1:8443/round?board=no-such"   # resources/board/serve.py → 404
python3 resources/board/serve.py status | head -1
curl -s -X POST http://127.0.0.1:8443/unregister -d "{\"board\":\"$N\"}"; rm -rf $D   # resources/board/serve.py forgets the copy
```
