#!/usr/bin/env python3
"""pearde questions — the round a PRD puts to the user, checked.

    python3 questions.py check [board]   one problem per line; silent when clean
    python3 questions.py list  [board]   prd · open · answered · state

A question round is `## Questions` in a `prd.md`, in the format
@references/drill.md sets: each question is the fork, ending in `?`, with
prepared answers, one of them recommended. `## Answers` is what the
orchestrator writes back. @references/templates/prd.md ships both headings
commented, and this file is what keeps the comment honest.

Why it exists, measured rather than argued. Across two boards on 2026-08-27:
ten PRDs carried `## Questions` and `## Answers` as bare headings with nothing
under them — a heading that says a round exists when none does; one carried
`## Answers` holding a reader's two remarks and no answer, under a PRD with no
`## Questions` at all; one sat parked on the user for three sessions without
ever writing down what it was asking; and one carried a whole sentence in
`needs:`, which `plan` resolves to nothing and reports nowhere. Every one of
them reads, from the outside, exactly like a board that is waiting on you.

The two rules that judge a written question are the two the format is for: it
asks something, and it comes with an answer you can pick. Option *count* is
deliberately not checked — a yes/no fork with a recommendation is a good
question, and a checker that demanded three would have failed six real ones.

Python 3 stdlib only.
"""
import os
import re
import sys

# win: a cp1252 console cannot encode the glyphs the board files carry
# (the "->" arrow of a workflow table, every umlaut of a German PRD), and
# the output dies on UnicodeEncodeError. Force UTF-8 out.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# `## Questions`, `## Questions — from the analyst pass`, `## Questions for
# the human`. The suffix is the round's own label and is never the contract.
Q_RE = re.compile(r"^##\s+Questions\b", re.M)
A_RE = re.compile(r"^##\s+Answers\b", re.M)
H2_RE = re.compile(r"^##\s+\S", re.M)

# One item inside the round. Two spellings are live on real boards: `###`
# heads — `### 1. …`, `### Q1: …` — and numbered items at the top level of the
# section. A section that carries heads is split on the heads alone: under
# one, a `1.` line at the top level is a prepared answer of that question,
# the shape @references/drill.md prescribes, not an item of its own. A section
# with no head keeps the numbered reading.
HEAD_RE = re.compile(r"^###\s+\S.*$", re.M)
ITEM_RE = re.compile(r"^\d+\.\s+\S.*$", re.M)

# …and which of those items is a question. A round also carries dividers and
# notes — `### Round 2 — raised by the analyst`, `### What answering these
# unlocks`, `### Answered 2026-08-24` — and those are prose about the round,
# not entries in it. A question is numbered, or it asks something. An
# unnumbered heading that asks nothing is neither.
NUMBERED_RE = re.compile(r"^(question\s*)?(q\s*)?\d+[.:)\s]", re.I)

# An answered question is not owed a recommendation: a recommendation exists
# so the user can pick, and the picking is done. Both spellings that mark it
# on real boards — a struck title, and a bold `Answered` — are read here.
ANSWERED_RE = re.compile(r"~~|^\s*\**Answered\b", re.M | re.I)

REC_RE = re.compile(r"recommend", re.I)

# A PRD name is a directory name, or `@member/dir` on a master board. Prose in
# `needs:` is silently ignored by `plan` — the failure this catches.
NAME_RE = re.compile(r"^@?[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*$")

KEY_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_-]*):\s*(.*?)\s*$")
ITEM_LIST_RE = re.compile(r"^\s*-\s+(.*?)\s*$")

# The nine states are @references/parts/states.md. `question` is the one that
# means "blocked on the user" by name; anything outside the table is parked,
# and a parked PRD that names a human is making the same claim without the
# word. Both owe a round.
WAITING = ("question", "hitl", "waiting", "blocked-on-user", "user")

# Terminal: nothing waits on anyone. A closed PRD still flying a
# waiting-on-a-human label is the label outliving the work, and it is why a
# board reports someone as blocked on a node that closed months ago.
# `superseded` is terminal the same way the drill count is concerned —
# work another PRD replaced cannot still be owed a question — so it sits
# here beside `done` rather than in a second tuple every reader merges.
CLOSED = ("done", "deferred", "superseded", "out-of-scope")


def strip_comment(v):
    return re.sub(r"\s+#.*$", "", v).strip().strip("\"'")


# A heading inside an HTML comment is not a heading — @references/templates/
# prd.md names all three in comments so a fresh copy ships none of them live.
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def parse(path):
    """(frontmatter, body). Mirrors @resources/board/plan.py's dialect: a
    `---` fence, one `key: value` per line, `- item` for lists. Commented-out
    markdown is dropped from the body before anything reads it."""
    text = open(path, encoding="utf-8", errors="replace").read()
    lines = text.splitlines()
    fm, start = {}, 0
    if lines and lines[0].strip() == "---":
        i, cur = 1, None
        while i < len(lines) and lines[i].strip() != "---":
            m, it = KEY_RE.match(lines[i]), ITEM_LIST_RE.match(lines[i])
            if m:
                key, val = m.group(1), strip_comment(m.group(2))
                fm[key], cur = (val, None) if val else ([], key)
            elif it and cur is not None:
                v = strip_comment(it.group(1))
                if v:
                    fm[cur].append(v)
            i += 1
        start = i + 1
    return fm, COMMENT_RE.sub("", "\n".join(lines[start:]))


def sections(body, pattern):
    """Every `## <name>` section the pattern matches: (heading, its lines)."""
    out = []
    for m in pattern.finditer(body):
        head_end = body.find("\n", m.start())
        head_end = len(body) if head_end < 0 else head_end
        nxt = H2_RE.search(body, head_end)
        out.append((body[m.start():head_end].strip(),
                    body[head_end:nxt.start() if nxt else len(body)]))
    return out


def questions_in(text):
    """The round split into its questions. A section with `###` heads is
    those heads, each with the numbered answers under it; one with numbered
    items and no head is those items; one with prose and no item shape is one
    question."""
    heads = list(HEAD_RE.finditer(text)) or list(ITEM_RE.finditer(text))
    if not heads:
        return [text] if text.strip() else []
    return [text[h.start():(heads[i + 1].start() if i + 1 < len(heads)
                            else len(text))]
            for i, h in enumerate(heads)]


def is_question(q):
    """An entry in the round, as against a divider or a note about it. A
    question is numbered (`### 1.`, `### Q1:`, `Question *Q1*:`) or it asks
    something; an unnumbered heading that asks nothing is neither."""
    first = q.strip().splitlines()[0] if q.strip() else ""
    plain = re.sub(r"[#*_~]", "", first).strip()
    return bool(NUMBERED_RE.match(plain)) or "?" in q


def settled(q):
    """Answered in place — a recommendation is owed to an open fork only."""
    first = q.strip().splitlines()[0] if q.strip() else ""
    return bool(ANSWERED_RE.search(first) or ANSWERED_RE.search(q[:400]))


def label(q, n):
    first = q.strip().splitlines()[0] if q.strip() else ""
    first = re.sub(r"^#+\s*", "", first).strip(" *_")
    return f"question {n} ({first[:56]}…)" if len(first) > 56 \
        else f"question {n} ({first})" if first else f"question {n}"


def prds(board):
    """(rel, path) for every PRD on the board, deepest name first.

    Walks `<board>/prds`, not `board` itself — same reason
    `memos.py board_prds` and `workflows.py _refs_one` do: the PRD tree is
    one level under the board root, and walking `board` would label every
    PRD `prds/<name>`, one level off from what a reader expects."""
    root_dir = os.path.join(board, "prds")
    if not os.path.isdir(root_dir):
        return []
    out = []
    for root, _dirs, files in os.walk(root_dir):
        if "prd.md" in files and root != root_dir:
            out.append((os.path.relpath(root, root_dir),
                        os.path.join(root, "prd.md")))
    return sorted(out)


# ── the plain-words rule ──────────────────────────────────────────────────────
# @references/drill.md sets what a question may not say, as a table: no
# tree-shaped word for a reader with no tree open, no name that is a ticket
# number to someone who did not write it, no board vocabulary — that belongs to
# the orchestrator — and a length past which the fork stopped being a fork and
# became a briefing. This is that table as a mechanism, one predicate per row,
# each naming the word it caught so the analyst can see what to take out.
#
# Scope is the fork, the answer labels and the answer text. The `### Qn: title`
# is not checked — it is the round's own index, and `Q1` there is the id every
# other reader matches on. The technical anchor an analyst writes under the
# third answer is an HTML comment, and `parse` drops every comment from the
# body before anything here sees it, so it is never checked and never reported.

FORK_WORDS = 60
ANSWER_WORDS = 25

# The five of the nine states that are also ordinary English — `open`,
# `question`, `blocked`, `done`, `failed` — are words a person uses about their
# own work ("what they see when they open the board" is drill.md's own worked
# example), and a bare-word check on them fails correct questions. They are
# caught in their board spelling only, which is the backtick ROW_TICK already
# refuses. What is left is board-only vocabulary, safe to catch bare.
STATE_WORDS = ("analyzing", "specced", "claimed", "refine", "deferred")
FM_KEYS = ("frontmatter", "blast-radius", "footprint", "priority", "complexity",
           "needs:", "workflow:", "origin:", "state:", "repo:")
ROLE_WORDS = ("analyst", "implementer", "orchestrator", "persona", "engineer",
              "skeptic", "verdict", "dispatch", "dispatched", "prd", "prds",
              "backlog", "spec", "specs", "brief")

TICK_RE = re.compile(r"`")
PATH_RE = re.compile(r"(?<![\w/])[\w.-]*[\w-]/[\w./-]*[\w-]")
EXT_RE = re.compile(r"\b[\w-]+\.(?:md|py|js|jsx|ts|css|sh|json|ya?ml|toml"
                    r"|txt|html|cfg|ini)\b", re.I)
QREF_RE = re.compile(r"\bQ\s?\d+\b")
HEDGE_RE = re.compile(r"\bshould we (?:also|maybe|additionally)\b"
                      r"|\bdo we (?:also )?(?:want|need) to\b"
                      r"|\bshall we also\b", re.I)

WORDS_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\u2019-]*")
ANSWER_RE = re.compile(r"^(\d+)[.)]\s+(.*)$", re.M)
REC_MARK_RE = re.compile(r"\s*\((?:recommended|default)\)\s*", re.I)


def words(text):
    return len(WORDS_RE.findall(text))


def bare(text, vocab):
    """The first word of `vocab` present in `text` as a whole word, or None.
    Whole-word so `opens` is not `open` and `specced` is not `spec`."""
    low = text.lower()
    for w in vocab:
        if w.endswith(":"):
            if w in low:
                return w
        elif re.search(r"(?<![\w-])" + re.escape(w) + r"(?![\w-])", low):
            return w
    return None


def split_question(q):
    """(fork, [answer, …]) for one question of a round. The head line is
    dropped — it is the index, not the question."""
    body = q.strip()
    if body.startswith("#"):
        body = body.split("\n", 1)[1] if "\n" in body else ""
    at = ANSWER_RE.search(body)
    fork = (body[:at.start()] if at else body).strip()
    answers = []
    if at:
        for part in re.split(r"^(?=\d+[.)]\s)", body[at.start():], flags=re.M):
            m = ANSWER_RE.match(part.strip())
            if m:
                answers.append(REC_MARK_RE.sub(" ", m.group(2)).strip())
    return fork, answers


def plain(rel, n, q, slugs=()):
    """Every plain-words problem in one question, one string each."""
    bad = []
    fork, answers = split_question(q)
    where = [("the fork", fork, FORK_WORDS)]
    where += [(f"answer {i}", a, ANSWER_WORDS)
              for i, a in enumerate(answers, start=1)]

    def say(part, why):
        bad.append(f"{rel}: {label(q, n)} — {part} {why}")

    for part, text, limit in where:
        if not text:
            continue
        if TICK_RE.search(text):
            say(part, "quotes code — a backtick, for a reader with no tree open")
        m = EXT_RE.search(text) or PATH_RE.search(text)
        if m:
            say(part, f"names a file — `{m.group(0)}`, which the reader "
                      "cannot open")
        for s in slugs:
            if re.search(r"(?<![\w-])" + re.escape(s) + r"(?![\w-])", text):
                say(part, f"names a PRD — `{s}` is a ticket number to "
                          "someone who did not write it")
                break
        m = QREF_RE.search(text)
        if m:
            say(part, f"cross-references `{m.group(0)}` — each question is "
                      "answered on its own")
        w = (bare(text, STATE_WORDS) or bare(text, FM_KEYS)
             or bare(text, ROLE_WORDS))
        if w:
            say(part, f"says `{w}` — board vocabulary is the orchestrator's")
        if words(text) > limit:
            say(part, f"runs {words(text)} words, over {limit} — past that "
                      "it is a briefing, not a fork")
        m = HEDGE_RE.search(text)
        if m:
            say(part, f"hedges — `{m.group(0)}` asks for a fact a build "
                      "would find, not a decision")
    return bad


def slugs_of(board):
    """Every PRD name on the board that is safe to look for inside prose — a
    hyphenated directory name. A one-word name is an ordinary word and a
    substring check on it would refuse correct English."""
    out = set()
    for rel, _path in prds(board):
        for name in (rel, os.path.basename(rel)):
            if "-" in name:
                out.add(name)
    return sorted(out, key=len, reverse=True)


def check(board):
    """Every problem, one string each. Empty means the rounds are clean."""
    bad = []
    slugs = slugs_of(board)
    for rel, path in prds(board):
        fm, body = parse(path)
        qs = sections(body, Q_RE)
        ans = sections(body, A_RE)
        state = str(fm.get("state", "")).strip()
        mode = str(fm.get("mode", "")).strip()

        for head, text in qs:
            if not text.strip():
                bad.append(f"{rel}: `{head}` with nothing under it — a heading "
                           "that says a round exists when none does")
                continue
            if re.search(r"\banswered\b", head, re.I):
                continue              # `## Questions (round 1, answered)`
            for n, q in enumerate(questions_in(text), start=1):
                if not is_question(q) or settled(q):
                    continue
                if "?" not in q:
                    bad.append(f"{rel}: {label(q, n)} asks nothing — a fork "
                               "ends in `?` or it is a note, not a question")
                if not REC_RE.search(q):
                    bad.append(f"{rel}: {label(q, n)} carries no recommended "
                               "answer — the round hands over a fork with no "
                               "way to pick")
                bad.extend(plain(rel, n, q, slugs))

        # A CLOSED PRD'S RECORDED ANSWER IS HISTORY AND IS LEFT ALONE. The
        # drill's own rule, and the reason this branch is guarded: the six
        # `## Answers`-without-`## Questions` sections on this board's closed
        # decision nodes hold real calls — fzf, tinty, odin, shift-select —
        # taken in conversation and written down afterwards. Reporting them
        # asks an author either to invent the fork that was never typed, or
        # to delete the decision. Both are worse than the flag.
        #
        # An OPEN node with the same shape is still reported: there the
        # missing round is a live gap, not a record.
        closed = state.lower() in CLOSED
        for head, text in ans:
            if not text.strip():
                bad.append(f"{rel}: `{head}` with nothing under it — "
                           "unanswered reads the same as unasked")
            elif not any(t.strip() for _h, t in qs) and not closed:
                bad.append(f"{rel}: `{head}` with no `## Questions` above it — "
                           "an answer to a question nobody wrote down")

        # `mode:` IS A PROPERTY OF THE WORK, NOT A POSITION IN A QUEUE. The
        # template defines it as `afk | hitl (needs the human: naming, taste,
        # money)`, and on a closed node `hitl` stays a TRUE statement: that
        # work did need a human. Reading it as a state made every finished
        # hitl node a defect for having been honest about itself — eight of
        # them on one board — and the only way to green them was to delete
        # the true label.
        #
        # `state:` is still read as a state, because it is one: a PRD parked
        # in `question` while closed really is a contradiction.
        waiting_state = state.lower() in WAITING
        waiting = waiting_state or (mode.lower() in WAITING and not closed)
        said = f"state `{state}`" if waiting_state else f"mode `{mode}`"
        if waiting and closed:
            bad.append(f"{rel}: state `{state}` and {said} — a closed PRD that "
                       "still says it is waiting on you; the label outlived "
                       "the work")
        elif waiting and not any(t.strip() for _h, t in qs):
            bad.append(f"{rel}: {said} — parked on the user with no "
                       "`## Questions` round saying what is being asked")

        needs = fm.get("needs", [])
        for n in (needs if isinstance(needs, list) else [needs]):
            if n and not NAME_RE.match(str(n)):
                bad.append(f"{rel}: `needs: {str(n)[:48]}…` is prose, not PRD "
                           "names — `plan` resolves none of it and says so "
                           "nowhere; put the sentence in the body")
    return bad


# ── the drill count ──────────────────────────────────────────────────────────
# An unanswered question is a `### Qn:` head under `## Questions` with no
# matching `**Qn**` under `## Answers`, on any PRD whose state is not terminal
# — `CLOSED` above — and this is the ONE count both readers take: `list`
# prints it, `plan.py scan` prints it, gates by it and reads it beside the
# round file's `## Asked`. Two readers sharing a rule here is how the scan
# and the list stopped being able to disagree about what still stands.

# An answer as the drill writes it: `**Q1** — …`, optionally stamped
# `*(answered 2026-08-28 14:22)*`. Only the id matches, never the text.
ANSWER_ID_RE = re.compile(r"(?m)^\s*\*\*\s*Q?\s*(\d{1,2}[a-z]?)\s*\*\*")

# The question's own id in the round: `### Q1: <title>` — also `### 1. <t>` —
# the two characters a prepared answer's `**Q1**` points back at.
QHEAD_RE = re.compile(r"^###\s+(?:question\s+)?[Qq]?\s?(\d{1,2}[a-z]?)"
                      r"\s*[:.—–-]?\s*(.*)$")


def unanswered(board):
    """[(rel, qid, title)] — every question still on the board's frontier.

    A question is unanswered when a `### Qn:` head stands under `## Questions`
    with no matching `**Qn**` under `## Answers`, on any PRD whose state is
    not `CLOSED`. One reader: `questions.py list` prints it and `plan.py`
    counts it — `drill_questions` there reads the round file beside it — so
    the two can never disagree about how many questions the board owes.

    A `### Qn:` head with no `###`-in-shape match (prose, a note) is not part
    of this count, and neither is a head whose block is not asking or is
    settled in place — `check` and `settled` are the rules it keeps to."""
    out = []
    for rel, path in prds(board):
        fm, body = parse(path)
        if str(fm.get("state", "")).strip().lower() in CLOSED:
            continue
        answered = {"Q" + m.group(1).upper()
                    for _h, atext in sections(body, A_RE)
                    for m in ANSWER_ID_RE.finditer(atext)}
        for _head, text in sections(body, Q_RE):
            if re.search(r"\banswered\b", _head, re.I):
                continue
            for q in questions_in(text):
                if not is_question(q) or settled(q):
                    continue
                first = q.strip().splitlines()[0]
                m = QHEAD_RE.match(first)
                if not m:
                    continue
                qid = "Q" + m.group(1).upper()
                if qid in answered:
                    continue          # answered — not on the frontier
                title = m.group(2).strip()
                if not title:
                    title = " ".join(q.strip().splitlines()[1:]).strip()[:72]
                out.append((rel, qid, title))
    return out


def rows(board):
    """(rel, open, answers, state) per PRD — the `list` line. `open` is the
    drill count (`unanswered`), so a PRD whose round is answered prints its
    state out of the way: it holds an answer, not a question."""
    open_qs = {}
    for rel, _qid, _title in unanswered(board):
        open_qs[rel] = open_qs.get(rel, 0) + 1
    for rel, path in prds(board):
        fm, body = parse(path)
        na = sum(1 for _h, t in sections(body, A_RE) if t.strip())
        if open_qs.get(rel, 0) or na:
            yield rel, open_qs.get(rel, 0), na, str(fm.get("state", "-"))


# Duplicated from @resources/board/plan.py's own BOARD_DIR rather than
# imported — same reason @resources/guard.py gives: this reader keeps its
# own error prefix and does not depend on the planner to resolve a board.
BOARD_DIR = ".pearde"


def find_board(arg):
    if arg:
        p = os.path.abspath(arg)
        if os.path.basename(p) == BOARD_DIR and os.path.isdir(p):
            return p
        if os.path.isdir(os.path.join(p, BOARD_DIR)):
            return os.path.join(p, BOARD_DIR)
        sys.exit(f"questions: no {BOARD_DIR}/ board at {arg}")
    d = os.getcwd()
    while True:
        if os.path.isdir(os.path.join(d, BOARD_DIR)):
            return os.path.join(d, BOARD_DIR)
        nxt = os.path.dirname(d)
        if nxt == d:
            sys.exit(f"questions: no {BOARD_DIR}/ board found walking up from the cwd")
        d = nxt


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "check"
    board = find_board(argv[2] if len(argv) > 2 else None)
    if cmd == "check":
        bad = check(board)
        if bad:
            print("\n".join(bad))
        return 1 if bad else 0
    if cmd == "list":
        for rel, nq, na, state in rows(board):
            print(f"{rel:44} {nq:2} open  {na:2} answered  {state}")
        return 0
    print(__doc__.strip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
