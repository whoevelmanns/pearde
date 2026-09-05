#!/usr/bin/env python3
"""pearde jira sync — mirrors a PRD's state onto its Jira issue, and reads
back the other direction (drift detection, new-ticket import).

    python3 jira_sync.py sync <prd-dir-name> <state> [note...]
    python3 jira_sync.py discover <PROJECT-KEY>   # (re)fetch that project's workflow graph
    python3 jira_sync.py check [PROJECT-KEY]      # env + reachability, prints what it finds
    python3 jira_sync.py drift                    # report PRDs whose Jira status has drifted
    python3 jira_sync.py import-new               # report "Selected"+assigned tickets with no PRD

Opt-in per board: `jira-sync: on` in prds/settings.md, and JIRA_BASE_URL,
JIRA_EMAIL, JIRA_API_TOKEN in the environment. Any of the three missing is
not an error — `sync` prints one line to stderr and exits 0, so a board
without Jira behind it, or a session that has not exported the token yet,
is unaffected. See README.md for the full design and why the
mapping looks like this.

The Jira issue key is read off the front of the PRD directory's own name:
`<PROJECT>-<number>`, case-folded to upper (`ab-621-...` -> `AB-621`). A PRD
whose directory does not start that way is skipped, one line, exit 0 — most
boards mix ticketed and non-ticketed PRDs on purpose.

Workflow graphs differ per Jira site and per project, so nothing about
statuses or transitions is hardcoded: `discover` reads the project's real
workflow (workflow scheme -> workflow definition -> status names, all via
the REST API) and caches it as `prds/.jira-graph-<PROJECT>.json`. `sync`
loads that cache, discovering lazily the first time a project is seen.
Delete the cache file (or run `discover` again) after a workflow edit in
Jira.

Moving between statuses walks the graph breadth-first and executes each hop
as its own transition, re-reading the live `.../transitions` list at every
step (so it survives an ID that differs from what the cache saw). If no
forward path exists — most workflows do not lead backward, and a ticket
found further along than pearde expects (worked in Jira directly, or ahead
of what pearde tracked) is a `Fertig`-like state pearde never told it to
reach mid-flight — nothing is forced: the status is left alone and only a
comment records what pearde tried to do. Never guess a destructive jump.

Python 3 stdlib only, like every other script in this skill.
"""
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import deque

# Frontmatter scan: reuse resources/board/plan.py's `scan`/`board_settings`
# rather than growing a third parser — same pattern plan.py itself uses to
# reach memos.py.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "resources", "board"))
import plan as planlib  # noqa: E402 — path set immediately above

KEY_RE = re.compile(r"^([A-Za-z]+)-(\d+)(?:-|$)")

# state -> (target status name, or None to only ever comment)
STATE_TARGET = {
    "open": "Offen",
    "analyzing": "Vorbereitung",
    "refine": None,       # handled specially — pause-if-possible, see sync()
    "question": None,     # handled specially — pause-if-possible, see sync()
    "blocked": None,      # handled specially — pause-if-possible, see sync()
    "specced": "Preparing Done",
    "claimed": "Implementing",
    "done": "Fertig",
    "failed": "Erneut geöffnet",
}
# states whose sync always writes a comment, in addition to any transition
ALWAYS_COMMENT = {"refine", "question", "blocked", "failed"}


# One override key per overridable state, `jira-<state>-status` in
# settings.md — `done`'s `jira-done-status` predates the rest and keeps its
# original name rather than gaining a `jira-done-status` alias.
STATE_TARGET_OVERRIDE_KEY = {
    "analyzing": "jira-analyzing-status",
    "specced": "jira-specced-status",
    "claimed": "jira-claimed-status",
    "done": "jira-done-status",
}


def state_target(board, state):
    """STATE_TARGET.get(state), with a per-board override via
    `jira-<state>-status` in settings.md — STATE_TARGET is a global constant
    shared by every board this skill runs on, so changing it outright would
    retarget that state for every other board too (e.g. a board whose
    workflow still expects "Fertig"). A board whose Jira project runs a
    workflow with none of the dev-pipeline status names at all (an ITSM
    board with only Offen/In Arbeit/Erledigt/Geschlossen, first seen
    2026-09-02: `analyzing`/`specced`/`claimed` all map to "In Arbeit" there
    since that workflow draws no finer line between them) sets these instead
    of editing the constant — same pattern as `selected_status_name()`
    above, generalized from `done`'s original `jira-done-status`."""
    key = STATE_TARGET_OVERRIDE_KEY.get(state)
    if key:
        v = planlib.board_settings(board).get(key)
        if isinstance(v, list):
            v = v[0] if v else None
        v = str(v).strip() if v else ""
        if v:
            return v
    return STATE_TARGET.get(state)


def _board_creds(board):
    """Local, per-board override for env() — `<board>/.jira-credentials.json`
    ({"base_url", "email", "api_token"}), gitignored, never committed. Lets
    one machine run pearde against more than one Jira site at once (the
    stock env() below is global, so a second board on a different site would
    otherwise fight the first for JIRA_BASE_URL/EMAIL/TOKEN). Missing file,
    or any of the three keys missing/blank, is not an error — falls through
    to the global env vars exactly as if this function did not exist."""
    if not board:
        return None
    path = os.path.join(board, ".jira-credentials.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    b, e, t = data.get("base_url"), data.get("email"), data.get("api_token")
    if not (b and e and t):
        return None
    return b.rstrip("/"), e, t


def env(board=None):
    local = _board_creds(board)
    if local is not None:
        return local
    b, e, t = (os.environ.get("JIRA_BASE_URL"), os.environ.get("JIRA_EMAIL"),
               os.environ.get("JIRA_API_TOKEN"))
    if not (b and e and t):
        return None
    return b.rstrip("/"), e, t


def issue_key(prd_dir_name):
    m = KEY_RE.match(os.path.basename(prd_dir_name.rstrip("/\\")))
    return f"{m.group(1).upper()}-{m.group(2)}" if m else None


def _request(method, base_url, auth, path, data=None):
    url = f"{base_url}{path}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
    req.add_header("Authorization", f"Basic {token}")
    req.add_header("Accept", "application/json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        print(f"jira_sync: {method} {path} -> HTTP {e.code}: {detail}",
              file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"jira_sync: {method} {path} -> {e}", file=sys.stderr)
        return None


def current_status(base_url, auth, key):
    d = _request("GET", base_url, auth,
                 f"/rest/api/3/issue/{key}?fields=status")
    return d["fields"]["status"]["name"] if d else None


def live_transitions(base_url, auth, key):
    """[(id, to_name, action_name), ...] from the issue's CURRENT status."""
    d = _request("GET", base_url, auth, f"/rest/api/3/issue/{key}/transitions")
    if not d:
        return []
    return [(t["id"], t["to"]["name"], t["name"]) for t in d["transitions"]]


def do_transition(base_url, auth, key, transition_id):
    return _request("POST", base_url, auth, f"/rest/api/3/issue/{key}/transitions",
                     {"transition": {"id": transition_id}}) is not None


def add_comment(base_url, auth, key, text):
    adf = {"type": "doc", "version": 1, "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": text}]}]}
    return _request("POST", base_url, auth, f"/rest/api/3/issue/{key}/comment",
                     {"body": adf}) is not None


# ── workflow graph discovery ────────────────────────────────────────────────

def _graph_path(board, project):
    return os.path.join(board, f".jira-graph-{project}.json")


def discover_graph(base_url, auth, project):
    """Read the project's real workflow off the API and return
    {status_display_name: [reachable_status_display_name, ...]}.

    Two endpoints, deliberately not one: the workflow definition
    (transitions, statuses-by-id) carries the workflow's own generic status
    names ("Open", "Preparing", ...), but a project can localize or rename
    the status a user actually sees ("Offen", "Vorbereitung", ...) — that
    renamed form is what an issue's `fields.status.name` and a transition's
    `to.name` report at sync time. `/project/{key}/statuses` is keyed by the
    same status ids and carries that display name, so it — not the workflow
    definition — is the id -> name table the graph is built with."""
    disp = _request("GET", base_url, auth, f"/rest/api/3/project/{project}/statuses")
    if not disp:
        return None
    id_to_name = {}
    for issue_type in disp:
        for s in issue_type["statuses"]:
            id_to_name[s["id"]] = s["name"]

    proj = _request("GET", base_url, auth, f"/rest/api/3/project/{project}")
    if not proj:
        return None
    scheme = _request("GET", base_url, auth,
                       f"/rest/api/3/workflowscheme/project?projectId={proj['id']}")
    if scheme and scheme.get("values"):
        wf_name = scheme["values"][0]["workflowScheme"]["defaultWorkflow"]
        from urllib.parse import quote
        wf = _request("GET", base_url, auth,
                      f"/rest/api/3/workflow/search?workflowName={quote(wf_name)}"
                      f"&expand=transitions,statuses")
        if not wf or not wf.get("values"):
            return None
        w = wf["values"][0]
        graph = {}
        for t in w["transitions"]:
            for f in t.get("from", []):
                fid = f.get("id") if isinstance(f, dict) else f
                frm = id_to_name.get(fid)
                if not frm:
                    continue
                to = id_to_name.get(t["to"], t["to"])
                graph.setdefault(frm, [])
                if to not in graph[frm]:
                    graph[frm].append(to)
        return graph

    # Team-managed ("next-gen"/simplified) project: no workflow scheme at
    # all — `/workflowscheme/project` legitimately returns {"values": []},
    # not an error. Its single per-project workflow lives in the newer
    # Workflows API instead (`GET /rest/api/3/workflows/search`, filtered
    # locally by `scope.project.id` since the API itself has no project
    # filter param), with a different transition shape: GLOBAL (no `links`,
    # reachable from every status in the workflow) or DIRECTED (`links[].
    # fromStatusReference` names the one status it fires from) — vs.
    # classic's explicit `from` id list per transition, above.
    return _discover_graph_nextgen(base_url, auth, proj["id"], id_to_name)


def _discover_graph_nextgen(base_url, auth, project_id, id_to_name):
    graph = {}
    start_at = 0
    found = False
    while True:
        page = _request("GET", base_url, auth,
                        "/rest/api/3/workflows/search?expand=values.transitions"
                        f"&maxResults=50&startAt={start_at}")
        if not page:
            return graph if found else None
        for w in page.get("values", []):
            if w.get("scope", {}).get("project", {}).get("id") != project_id:
                continue
            found = True
            all_names = [id_to_name[s["statusReference"]] for s in w.get("statuses", [])
                        if s["statusReference"] in id_to_name]
            for t in w.get("transitions", []):
                if t.get("type") == "INITIAL":
                    continue  # the creation transition, not between two existing statuses
                to = id_to_name.get(t.get("toStatusReference"))
                if not to:
                    continue
                links = t.get("links") or []
                froms = all_names if not links else [
                    id_to_name[l["fromStatusReference"]] for l in links
                    if l.get("fromStatusReference") in id_to_name
                ]
                for frm in froms:
                    graph.setdefault(frm, [])
                    if to not in graph[frm] and to != frm:
                        graph[frm].append(to)
        if page.get("isLast", True):
            break
        start_at += len(page.get("values", [])) or page.get("maxResults", 50)
    return graph if found else None


def load_graph(board, base_url, auth, project, refresh=False):
    path = _graph_path(board, project)
    if not refresh and os.path.isfile(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except (OSError, ValueError):
            pass
    graph = discover_graph(base_url, auth, project)
    if graph is None:
        return None
    try:
        json.dump(graph, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except OSError:
        pass
    return graph


def shortest_path(graph, start, target):
    """[status, status, ...] from start to target, excluding start. None if
    unreachable — most workflows do not lead backward, and that is a
    decision for a human, not a status this script forces."""
    if start == target:
        return []
    seen, q = {start}, deque([(start, [])])
    while q:
        node, path = q.popleft()
        for nxt in graph.get(node, []):
            if nxt == target:
                return path + [nxt]
            if nxt not in seen:
                seen.add(nxt)
                q.append((nxt, path + [nxt]))
    return None


# ── the sync rules — see README.md for the reasoning ─────────────

def _hold_transition(transitions):
    """The one transition (if exactly one) pausing the current phase."""
    holds = [(tid, to) for tid, to, _ in transitions if "on hold" in to.lower()]
    return holds[0] if len(holds) == 1 else None


def _resume_transition(transitions):
    """The one transition (if exactly one) named Resume… — un-pausing."""
    r = [(tid, to) for tid, to, name in transitions if name.lower().startswith("resume")]
    return r[0] if len(r) == 1 else None


def advance(base_url, auth, key, graph, target):
    """Walk the graph toward `target`, one live transition per hop. Returns
    (moved_through: [status,...], reached: bool)."""
    status = current_status(base_url, auth, key)
    if status is None:
        return [], False
    if status == target:
        return [], True
    path = shortest_path(graph, status, target) if graph else None
    if not path:
        return [], False
    moved = []
    for step in path:
        transitions = live_transitions(base_url, auth, key)
        hit = next((tid for tid, to, _ in transitions if to == step), None)
        if hit is None:
            return moved, False
        if not do_transition(base_url, auth, key, hit):
            return moved, False
        moved.append(step)
    return moved, True


def sync(board, prd_dir_name, state, note=None):
    e = env(board)
    if e is None:
        print("jira_sync: JIRA_BASE_URL/JIRA_EMAIL/JIRA_API_TOKEN not set — skipped",
              file=sys.stderr)
        return
    base_url, email, token = e
    auth = (email, token)
    key = issue_key(prd_dir_name)
    if key is None:
        print(f"jira_sync: '{prd_dir_name}' carries no <PROJECT>-<number> — skipped",
              file=sys.stderr)
        return
    project = key.split("-")[0]
    graph = load_graph(board, base_url, auth, project)

    target = state_target(board, state)
    moved, reached, mismatch = [], True, False

    if state in ("refine", "question", "blocked"):
        transitions = live_transitions(base_url, auth, key)
        hold = _hold_transition(transitions)
        if hold:
            do_transition(base_url, auth, key, hold[0])
            moved = [hold[1]]
    elif state == "open":
        # Never a forced move to "Offen": a ticket already "Selected" (or
        # further) was placed there on purpose — by a person in Jira, or by
        # an earlier sync — and un-selecting it back to the backlog just
        # because pearde's own state is `open` again (e.g. after refine, or
        # a question answered) would undo that. The only move `open` ever
        # makes is un-pausing a hold, which is always a step forward from
        # where the ticket already was, never a status regression — so a
        # ticket already resting past "Offen" is a silent no-op, not a
        # mismatch worth a comment.
        status = current_status(base_url, auth, key)
        if status and "on hold" in status.lower():
            transitions = live_transitions(base_url, auth, key)
            resume = _resume_transition(transitions)
            if resume:
                do_transition(base_url, auth, key, resume[0])
                moved = [resume[1]]
    elif target:
        moved, reached = advance(base_url, auth, key, graph, target)
        mismatch = not reached  # a real target we could not reach — flag it

    # A plain transition (open/analyzing/specced/claimed/done) is already
    # self-documenting in Jira's own activity log — a comment repeating
    # "status changed" adds noise, not information. Comment only where the
    # status change alone would not tell the story: a note was passed in, a
    # question/blocker/refine/failure needs its reason on the ticket, or the
    # graph could not get there and a human should know why not.
    if note or state in ALWAYS_COMMENT or mismatch:
        label = f"pearde: state -> {state}"
        if note:
            label += f"\n\n{note}"
        if moved:
            label += f"\n\nJira: {' -> '.join(moved)}"
        if mismatch:
            label += f"\n\n(no forward path to \"{target}\" from the current status — left unchanged)"
        add_comment(base_url, auth, key, label)

    where = " -> ".join(moved) if moved else "(unchanged)"
    print(f"jira_sync: {key} {state}: {where}")


# ── drift detection — read-only, Jira as an additional source ─────────────
# States that never carry a single forced target status: `open` is handled
# specially by sync() (only ever un-pauses, per README.md — the
# STATE_TARGET["open"] entry above is not actually used as a hard target),
# and refine/question/blocked pause into whichever "... on hold" the current
# phase offers, which is not one fixed name either. Comparing any of the
# four against a single expected status would be a guess, not a finding.
NO_DRIFT_TARGET = {"open", "refine", "question", "blocked"}


def drift(board):
    """Print one line per tracked PRD whose live Jira status no longer
    matches what its pearde `state` expects. Silent when clean, like
    memos.py check. Never changes a PRD's state — a report only, see
    README.md.

    A live status the graph reaches by walking *forward* from the target
    (not the target itself, but reachable from it) is not reported either:
    the ticket progressed past what pearde's own state machine tracks —
    e.g. `done` targets "Test" via `jira-done-status`, and a human later
    moves the ticket on to "Fertig" once real-world testing/deploy is done.
    That is exactly what `jira-done-status` is for, not a mismatch worth a
    human's look. Only a status neither equal to nor reachable from the
    target — off to the side, or behind — is real drift."""
    e = env(board)
    if e is None:
        print("jira_sync: JIRA_BASE_URL/JIRA_EMAIL/JIRA_API_TOKEN not set — skipped",
              file=sys.stderr)
        return
    base_url, email, token = e
    auth = (email, token)
    prds = planlib.scan(board)
    graphs = {}
    for rel in sorted(prds):
        p = prds[rel]
        state = p["state"]
        if state in NO_DRIFT_TARGET:
            continue
        target = state_target(board, state)
        if not target:
            continue
        key = issue_key(p["name"])
        if key is None:
            continue
        live = current_status(base_url, auth, key)
        if live is None or live == target:
            continue
        project = key.split("-")[0]
        if project not in graphs:
            graphs[project] = load_graph(board, base_url, auth, project)
        graph = graphs[project]
        if graph and shortest_path(graph, target, live) is not None:
            continue
        print(f'jira_sync: drift {rel} ({key}): state {state} expects '
              f'"{target}", Jira has "{live}"')


# ── ticket import — Jira as a source of new PRDs, report-only ─────────────
# import_new() never writes under prds/ — same one-writer rule as everything
# else in this skill: it reports, the orchestrator creates the PRD, exactly
# like the existing "Refine" loop step. See README.md.

def configured_projects(board):
    """Sorted, deduplicated project keys to scan for new tickets: every
    <PROJECT> prefix already used by a PRD directory name anywhere on the
    board (recursive — an epic's children nest under it), plus the optional,
    additive `jira-projects` setting (YAML list or comma-separated scalar) —
    the latter covers importing a brand-new project before any PRD with its
    prefix exists yet."""
    prds = planlib.scan(board)
    projects = set()
    for p in prds.values():
        key = issue_key(p["name"])
        if key:
            projects.add(key.split("-")[0])
    raw = planlib.board_settings(board).get("jira-projects", [])
    items = raw if isinstance(raw, list) else [raw]
    for item in items:
        for piece in str(item).split(","):
            piece = piece.strip().upper()
            if piece:
                projects.add(piece)
    return sorted(projects)


def backlog_status_name(board):
    """The Jira status name that means "not yet ready to start" for this
    board's import scan — the one status excluded from it, exact name
    match. Configurable via `jira-backlog-status`, default "Offen" (the
    same name STATE_TARGET["open"] targets everywhere in this file — one
    site-wide assumption, not a new one)."""
    v = planlib.board_settings(board).get("jira-backlog-status")
    if isinstance(v, list):
        v = v[0] if v else None
    v = str(v).strip() if v else ""
    return v or "Offen"


def _prd_for_key(prds, key):
    """The rel of the existing PRD that already covers `key`, or None.

    Primary: `key` matches the <PROJECT>-<number> prefix of a PRD directory
    name. Fallback: `key` (word-bounded, case-insensitive) appears in a
    PRD's own body — catches a PRD without a prefixed dir name that still
    names its own ticket. A PRD with neither (dir name unprefixed, body
    silent on its key — e.g. AB-625 / sortierung-erhalten-am-absteigend as
    of this writing) is a documented, pre-existing gap this cannot close;
    see spec02 and the parent+sibling report below, which is how that case
    stays visible to a human instead of silently duplicating."""
    key = key.upper()
    for rel, p in prds.items():
        if issue_key(p["name"]) == key:
            return rel
    word_re = re.compile(r"\b" + re.escape(key) + r"\b", re.IGNORECASE)
    for rel, p in prds.items():
        if word_re.search(p.get("body") or ""):
            return rel
    return None


def has_existing_prd(board, key):
    return _prd_for_key(planlib.scan(board), key) is not None


def adf_to_text(doc):
    """Best-effort plain text from an Atlassian Document Format node —
    every {"type": "text", "text": ...} leaf, paragraphs newline-separated.
    Not full ADF fidelity; the point is a readable body seed, not rendering."""
    if not isinstance(doc, dict):
        return ""

    def leaves(node):
        out = []
        if isinstance(node, dict):
            if node.get("type") == "text":
                out.append(node.get("text", ""))
            for child in node.get("content", []) or []:
                out.extend(leaves(child))
        return out

    paragraphs = []
    for node in doc.get("content", []) or []:
        text = "".join(leaves(node))
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs).strip()


def _search_jql(base_url, auth, jql, fields):
    """Yield every issue matching `jql`, walking every page.

    Verified live against the running Jira instance (2026-08-25,
    nicando.atlassian.net): /rest/api/3/search/jql pages with a
    `nextPageToken` string + boolean `isLast` — not the classic
    startAt/total pair the older /search endpoint used. The last page still
    carries a (now-stale) nextPageToken, so the loop stops on `isLast`
    being true, never on token absence alone."""
    from urllib.parse import urlencode
    token = None
    while True:
        params = {"jql": jql, "fields": fields, "maxResults": 50}
        if token:
            params["nextPageToken"] = token
        d = _request("GET", base_url, auth,
                     f"/rest/api/3/search/jql?{urlencode(params)}")
        if not d:
            return
        for issue in d.get("issues", []):
            yield issue
        if d.get("isLast", True) or not d.get("nextPageToken"):
            return
        token = d["nextPageToken"]


def import_new(board):
    """Print one block per Jira ticket assigned to JIRA_EMAIL's user that
    has no PRD on this board yet and is neither `backlog_status_name()`
    (not ready to start) nor in the Jira-native "Done" status category —
    everything in between, ready or further along, is a gap worth a human's
    look: a ticket a person pushed past "ready" directly in Jira, with no
    PRD ever tracking it, is not less of a gap than one still sitting at
    "ready" (found 2026-09-02: HAMA-1395 sat at "Vorbereitung" — one step
    past the old exact-match filter's "Selected" — for months, invisible to
    this scan, until asked about directly). The `statusCategory.key` field
    on each returned issue is used for the Done check, not a JQL
    `statusCategory` clause — this Jira site's category *display* names are
    localized (German), and the JQL clause's matching against a localized
    instance is untested; the structural `key` returned per-issue
    ("new"/"indeterminate"/"done") is not localized and always reliable.
    Never writes under prds/ — see module note above. Silent when nothing
    is found, like drift()."""
    e = env(board)
    if e is None:
        print("jira_sync: JIRA_BASE_URL/JIRA_EMAIL/JIRA_API_TOKEN not set — skipped",
              file=sys.stderr)
        return
    base_url, email, token = e
    auth = (email, token)
    prds = planlib.scan(board)
    projects = configured_projects(board)
    backlog = backlog_status_name(board)
    found = []
    for project in projects:
        jql = f'project = "{project}" AND assignee = currentUser() ORDER BY key'
        for issue in _search_jql(base_url, auth, jql,
                                  "summary,description,parent,status"):
            key = issue.get("key")
            if not key or _prd_for_key(prds, key) is not None:
                continue
            fields = issue.get("fields", {}) or {}
            status = fields.get("status") or {}
            if status.get("name") == backlog:
                continue
            if (status.get("statusCategory") or {}).get("key") == "done":
                continue
            summary = fields.get("summary", "") or ""
            desc = adf_to_text(fields.get("description") or {})[:300] or "(none)"
            parent = fields.get("parent") or {}
            pkey = parent.get("key")
            parent_line = "  parent: none -> flat"
            if pkey:
                prel = _prd_for_key(prds, pkey)
                if prel:
                    siblings = sorted(os.path.basename(c)
                                       for c in prds[prel].get("children", []))
                    parent_line = (f"  parent: {pkey} -> existing PRD {prel} "
                                   f"(siblings: {', '.join(siblings) or '(none)'})")
                else:
                    parent_line = f"  parent: {pkey} -> no existing PRD -> flat"
            found.append((key, summary, parent_line, desc))
    for key, summary, parent_line, desc in found:
        print(f'jira_sync: new {key} "{summary}"')
        print(parent_line)
        print(f"  description: {desc}")
    if found:
        print(f"jira_sync: import-new: {len(found)} ticket(s) without an existing PRD")


def find_board(arg):
    return planlib.find_board(arg)


def main(argv):
    # Windows' console default codepage mangles the ö/ß Jira sends back
    # (Selected, Erneut geöffnet, ...) — force UTF-8 on the streams that
    # print them. A no-op where the platform default already is UTF-8.
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8")
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "sync":
        if len(argv) < 4:
            print(__doc__.strip(), file=sys.stderr)
            return 2
        board = find_board(None)
        sync(board, argv[2], argv[3], " ".join(argv[4:]) or None)
        return 0
    if cmd == "discover":
        if len(argv) < 3:
            print(__doc__.strip(), file=sys.stderr)
            return 2
        board = find_board(None)
        e = env(board)
        if e is None:
            sys.exit("jira_sync: JIRA_BASE_URL/JIRA_EMAIL/JIRA_API_TOKEN not set")
        graph = load_graph(board, e[0], (e[1], e[2]), argv[2].upper(), refresh=True)
        if graph is None:
            sys.exit(f"jira_sync: could not read the workflow for project {argv[2]}")
        print(json.dumps(graph, ensure_ascii=False, indent=1))
        return 0
    if cmd == "drift":
        board = find_board(None)
        drift(board)
        return 0
    if cmd == "import-new":
        board = find_board(None)
        import_new(board)
        return 0
    if cmd == "check":
        board = find_board(None)
        e = env(board)
        if e is None:
            print("env: JIRA_BASE_URL/JIRA_EMAIL/JIRA_API_TOKEN — not fully set")
            return 1
        print(f"env: ok ({e[0]}, {e[1]})")
        if len(argv) > 2:
            graph = load_graph(board, e[0], (e[1], e[2]), argv[2].upper())
            print(f"workflow graph for {argv[2]}: "
                  f"{len(graph) if graph else 0} statuses"
                  + ("" if graph else " — could not read it"))
        return 0
    print(__doc__.strip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
