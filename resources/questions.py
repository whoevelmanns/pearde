#!/usr/bin/env python3
"""pearde questions — the round a PRD puts to the user, checked.

    python3 questions.py check [board]   one problem per line; silent when clean
    python3 questions.py list  [board]   prd · questions · answered · state

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

# `## Questions`, `## Questions — from the analyst pass`, `## Questions for
# the human`. The suffix is the round's own label and is never the contract.
Q_RE = re.compile(r"^##\s+Questions\b", re.M)
A_RE = re.compile(r"^##\s+Answers\b", re.M)
H2_RE = re.compile(r"^##\s+\S", re.M)

# One item inside the round: `### 1. …`, `### Q1: …`, or a numbered item at
# the top level of the section. Both spellings are live on real boards.
ITEM_RE = re.compile(r"^(###\s+\S.*|\d+\.\s+\S.*)$", re.M)

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
CLOSED = ("done", "deferred", "out-of-scope")


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
    """The round split into its questions. A section with items is those
    items; a section with prose and no item shape is one question."""
    heads = list(ITEM_RE.finditer(text))
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
    """(rel, path) for every PRD on the board, deepest name first."""
    out = []
    for root, _dirs, files in os.walk(board):
        if "prd.md" in files and root != board:
            out.append((os.path.relpath(root, board),
                        os.path.join(root, "prd.md")))
    return sorted(out)


def check(board):
    """Every problem, one string each. Empty means the rounds are clean."""
    bad = []
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

        for head, text in ans:
            if not text.strip():
                bad.append(f"{rel}: `{head}` with nothing under it — "
                           "unanswered reads the same as unasked")
            elif not any(t.strip() for _h, t in qs):
                bad.append(f"{rel}: `{head}` with no `## Questions` above it — "
                           "an answer to a question nobody wrote down")

        waiting = state.lower() in WAITING or mode.lower() in WAITING
        said = f"state `{state}`" if state.lower() in WAITING \
            else f"mode `{mode}`"
        if waiting and state.lower() in CLOSED:
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


def rows(board):
    for rel, path in prds(board):
        fm, body = parse(path)
        nq = sum(len([q for q in questions_in(t) if is_question(q)])
                 for _h, t in sections(body, Q_RE) if t.strip())
        na = sum(1 for _h, t in sections(body, A_RE) if t.strip())
        yield rel, nq, na, str(fm.get("state", "-"))


def find_board(arg):
    if arg:
        p = os.path.abspath(arg)
        if os.path.basename(p) == "prds" and os.path.isdir(p):
            return p
        if os.path.isdir(os.path.join(p, "prds")):
            return os.path.join(p, "prds")
        sys.exit(f"questions: no prds/ board at {arg}")
    d = os.getcwd()
    while True:
        if os.path.isdir(os.path.join(d, "prds")):
            return os.path.join(d, "prds")
        nxt = os.path.dirname(d)
        if nxt == d:
            sys.exit("questions: no prds/ board found walking up from the cwd")
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
            if nq or na:
                print(f"{rel:44} {nq:2} asked  {na:2} answered  {state}")
        return 0
    print(__doc__.strip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
