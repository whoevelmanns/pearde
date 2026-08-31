#!/usr/bin/env python3
"""The collect's workflow half, run rather than described — probe code.

@references/parts/loop.md step 6 gives the orchestrator five actions on a
report carrying `## Workflow <slug>`. Those are prose: a session reads them and
does them, and nothing in the shipped tree runs this file. It exists so the
PRD's `## Verify` dry run is a command with an exit code instead of a paragraph
about what a careful reader would do.

    python3 collect.py <board> <report.md> \
        [--apply  <atomic>:<## Section>] \
        [--refuse <atomic>:<## Section>:<whose fault>] \
        [--today YYYY-MM-DD]

What it does, in the order the loop lists:

1. Read the rows — the `## Workflow <slug>` table. Which atomics ran, and how.
   The PRD's transition is not this file's business.
2. Apply each `--apply` edit, refuse each `--refuse` one and print which. The
   fault call is the orchestrator's judgment, so it is an argument here, not a
   heuristic: a script that guessed whose fault a failure was would be the
   workflow engine @references/parts/workflows.md rejects.
3. `runs` +1 on the workflow and on every atomic that ran — once per atomic per
   collect, not once per traversal, so a back-edge does not double-count.
   `updated: <today>` only where the text changed.
4. `workflows.py check` — printed, and a non-empty result is a non-zero exit.
5. The commit is the orchestrator's and is not attempted here.
"""
import argparse
import os
import re
import subprocess
import sys

ROW = re.compile(r"^\s*\|\s*(\d+)\s*\|\s*([a-z0-9-]+)\s*\|\s*([^|]*?)\s*\|")
EDIT = re.compile(r"^\*\*([a-z0-9-]+)\*\*\s*—\s*`(##[^`]*)`\s*—\s*(.*)$")


def report_rows(text):
    """[(n, atomic, outcome)] from `## Workflow <slug>`, and the slug."""
    slug, rows, on = None, [], False
    for line in text.splitlines():
        if line.startswith("## Workflow "):
            slug, on = line[len("## Workflow "):].strip(), True
            continue
        if on and line.startswith("### "):
            break
        if not on:
            continue
        m = ROW.match(line)
        if m:
            rows.append((int(m.group(1)), m.group(2), m.group(3)))
    return slug, rows


def report_edits(text):
    """{(atomic, section): replacement}. A replacement runs to the next
    `**<slug>** —` line, so an edit may be several lines of body."""
    out, key, buf = {}, None, []
    started = False
    for line in text.splitlines():
        if line.strip() == "### Edits":
            started = True
            continue
        if not started:
            continue
        m = EDIT.match(line)
        if m:
            if key:
                out[key] = "\n".join(buf).strip("\n")
            key, buf = (m.group(1), m.group(2).strip()), [m.group(3)]
        elif key is not None:
            buf.append(line)
    if key:
        out[key] = "\n".join(buf).strip("\n")
    return out


def split_fm(text):
    if not text.startswith("---\n"):
        sys.exit("collect: no frontmatter fence")
    end = text.index("\n---\n", 3)
    return text[4:end + 1], text[end + 5:]


def bump(path, today, changed):
    """`runs` +1, and `updated: <today>` when the text changed."""
    text = open(path, encoding="utf-8").read()
    fm, body = split_fm(text)
    lines = fm.rstrip("\n").split("\n")
    keys = [l.split(":", 1)[0].strip() for l in lines]
    if "runs" in keys:
        i = keys.index("runs")
        lines[i] = "runs: %d" % (int(lines[i].split(":", 1)[1].strip() or 0) + 1)
    else:
        lines.append("runs: 1")
        keys.append("runs")
    if changed:
        if "updated" in keys:
            lines[keys.index("updated")] = "updated: %s" % today
        else:
            # after `date:`, which the format lists it after
            i = keys.index("date") + 1 if "date" in keys else len(lines)
            lines.insert(i, "updated: %s" % today)
    open(path, "w", encoding="utf-8").write(
        "---\n" + "\n".join(lines) + "\n---\n" + body)


def replace_section(path, heading, replacement):
    """Fold the lesson into the section named. The section's old body is
    REPLACED, never appended to — @references/parts/workflows.md, `Fold, do
    not log`."""
    text = open(path, encoding="utf-8").read()
    lines = text.split("\n")
    start = None
    for i, l in enumerate(lines):
        if l.strip() == heading:
            start = i
            break
    if start is None:
        sys.exit("collect: %s has no `%s`" % (os.path.basename(path), heading))
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    new = lines[:start + 1] + [""] + replacement.split("\n") + [""] + lines[end:]
    open(path, "w", encoding="utf-8").write("\n".join(new))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("report")
    ap.add_argument("--apply", action="append", default=[])
    ap.add_argument("--refuse", action="append", default=[])
    ap.add_argument("--today", required=True)
    a = ap.parse_args(argv[1:])

    lib = os.path.join(a.board, "workflows")
    text = open(a.report, encoding="utf-8").read()

    # 1. read the rows
    slug, rows = report_rows(text)
    if not slug:
        sys.exit("collect: the report carries no `## Workflow <slug>`")
    edits = report_edits(text)
    ran = []
    for _, atomic, outcome in rows:
        if atomic not in ran:
            ran.append(atomic)
        print("  ran      %-24s %s" % (atomic, outcome))

    # 2. apply / refuse — the fault call is the orchestrator's, so it is given
    changed = set()
    for spec in a.apply:
        atomic, section = spec.split(":", 1)
        key = (atomic, section)
        if key not in edits:
            sys.exit("collect: the report proposes no `%s` edit to %s"
                     % (section, atomic))
        replace_section(os.path.join(lib, atomic + ".md"), section, edits[key])
        changed.add(atomic)
        print("  applied  %-24s %s — the atomic's" % (atomic, section))
    for spec in a.refuse:
        atomic, section, fault = spec.split(":", 2)
        if (atomic, section) not in edits:
            sys.exit("collect: the report proposes no `%s` edit to %s"
                     % (section, atomic))
        print("  refused  %-24s %s — %s" % (atomic, section, fault))

    # 3. runs +1 on the workflow and on every atomic that ran
    bump(os.path.join(lib, slug + ".md"), a.today, slug in changed)
    for atomic in ran:
        bump(os.path.join(lib, atomic + ".md"), a.today, atomic in changed)
    print("  counted  %-24s runs +1" % slug)
    print("  counted  %s" % ", ".join(ran))

    # 4. check before the commit
    wf = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "..", "..", "..", "resources", "workflows.py")
    r = subprocess.run([sys.executable, os.path.normpath(wf), "check", a.board],
                       capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if out:
        print("  CHECK    refused — the edit breaks the format, "
              "and is not repaired here:")
        print("\n".join("    " + l for l in out.split("\n")))
        return 1
    print("  check    silent")

    # 5. the commit is the orchestrator's
    print("  commit   not this file's — @references/parts/commits.md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
