#!/usr/bin/env bash
# Builds the acceptance fixture of "## Done when" in a directory made at run
# time — never under prds/, where a dir holding prd.md is a PRD — and runs the
# checker over it. Usage: bash fixture.sh [dir]
set -u
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
DIR="${1:-$(mktemp -d)}"
B="$DIR/prds"
mkdir -p "$B/a-fork" "$B/the-page-shows-the-round"

# a second PRD, so its name is "a PRD slug of this board"
cat > "$B/the-page-shows-the-round/prd.md" <<'EOF'
---
state: open
---
# the page shows the round
EOF

cat > "$B/a-fork/prd.md" <<'EOF'
---
state: question
priority: 50
---
# a fork

## Questions

### Q1: What the page shows first

You are choosing what a person sees first when they open the board: the work
in progress, or the questions waiting on them. Whichever is first is what
they will act on; the other needs a click?

1. **Questions first** — the page opens on what is waiting on you; the work is one click away. (recommended)
2. **Work first** — the page opens on what is happening; your questions are one click away.
3. **Ask each time** — the page remembers whichever you opened last.

<!-- for the board: serve.py `/` default route; the-page-shows-the-round spec02 -->

### Q2: Where the round lands

You are choosing where the answer is written down, and the-page-shows-the-round
is the one that reads it back?

1. **Beside the question** — the answer sits under the question that asked it. (recommended)
2. **In one place** — every answer collects in a single list.
3. **Both** — the answer is written twice, once in each place.

### Q3: When the work is handed on

You are choosing the moment the work leaves you. Once it is specced nobody
asks you again, so the handover is the last point you can change your mind?

1. **On the answer** — the work leaves the moment you pick. (recommended)
2. **On your word** — nothing moves until you say go.
3. **On a timer** — it waits an hour, then goes.

### Q4: Which page opens

You are choosing which page a person lands on, and the setting for it lives in
resources/board/serve.py where the default route is written?

1. **The waiting page** — you land on what needs you. (recommended)
2. **The timeline** — you land on the whole plan.
3. **The last one** — you land where you left off.

### Q5: How much the page says at once

You are choosing how much a person is shown the moment the page arrives,
because there is a real difference between a page that puts everything in
front of you and trusts you to look away and a page that shows one thing and
keeps the rest a click away, and that difference decides whether the page
feels calm or feels like it is hiding the work, so which is it?

1. **Everything** — you see the whole thing at once. (recommended)
2. **One thing** — you see what matters now.
3. **You choose** — a switch decides it.
EOF

echo "--- questions check ---"
python3 "$REPO/resources/questions.py" check "$DIR"
echo "exit=$?"
echo "--- fixture at $DIR ---"
