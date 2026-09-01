#!/usr/bin/env python3
"""pearde edit — the writers. Every change the view makes to a board goes
through here. Nothing else in the tree writes a `prd.md`.

Each writer touches the smallest thing that can be touched: one frontmatter
line, the `# title` line, the body under the frontmatter, or a `## Section`
appended to. Frontmatter and body are never written in the same call — a body
edit cannot lose a `state:`, and a state edit cannot reflow prose. Every write
is atomic, a temp file and a rename — the daemon reads these files a second at
a time.

Python 3 stdlib only.
"""
import os
import re


def write_atomic(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)

def split_fm(text):
    """(before, fm_lines, after) — the frontmatter block, or None for fm_lines
    when the file has none."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return "", None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "".join(lines[:1]), lines[1:i], "".join(lines[i:])
    return "", None, text

def set_key(path, key, value):
    """Set one scalar frontmatter key, in place, keeping the file's own
    indentation and any trailing comment. A key the file does not have is
    appended to the block; a file with no frontmatter gets one."""
    text = open(path, encoding="utf-8").read()
    head, fm, tail = split_fm(text)
    line_re = re.compile(r"^(\s*)" + re.escape(key) + r":\s*(.*?)(\s+#.*)?$")
    if fm is None:
        return write_atomic(path, f"---\n{key}: {value}\n---\n\n" + text)
    for i, line in enumerate(fm):
        m = line_re.match(line.rstrip("\n"))
        if m:
            fm[i] = f"{m.group(1)}{key}: {value}{m.group(3) or ''}\n"
            break
    else:
        fm.append(f"{key}: {value}\n")
    write_atomic(path, head + "".join(fm) + tail)

def del_key(path, key):
    text = open(path, encoding="utf-8").read()
    head, fm, tail = split_fm(text)
    if fm is None:
        return
    keep = [l for l in fm
            if not re.match(r"^\s*" + re.escape(key) + r":\s", l)]
    if len(keep) != len(fm):
        write_atomic(path, head + "".join(keep) + tail)

def set_body(path, body):
    """Replace everything under the frontmatter. The frontmatter is never
    touched — it is the machine-read half, and a body edit must not be able to
    lose a `state:`."""
    text = open(path, encoding="utf-8").read()
    head, fm, _ = split_fm(text)
    keep = head + "".join(fm) + "---\n" if fm is not None else ""
    write_atomic(path, keep + "\n" + body.rstrip("\n") + "\n")

def append_section(path, heading, text):
    """Append text under `## <heading>`, creating the heading at the end of
    the body when it is not there. Additive only — nothing already written is
    touched, so the daemon can do it unsupervised."""
    body = open(path, encoding="utf-8").read().rstrip("\n")
    mark = f"## {heading}"
    block = text.strip()
    m = re.search(r"(?m)^" + re.escape(mark) + r"\s*$", body)
    if m:
        # into the existing section, at its end: answers accumulate in order
        i = m.start()
        j = body.find("\n## ", i + 1)
        head, mid, tail = ((body[:i], body[i:j], body[j:]) if j > 0
                           else (body[:i], body[i:], ""))
        body = head + mid.rstrip("\n") + "\n\n" + block + "\n" + tail
    else:
        body += f"\n\n{mark}\n\n{block}\n"
    write_atomic(path, body.rstrip("\n") + "\n")

def set_title(path, title):
    """The `# ` line is the PRD's title — sync reads it, not the directory
    name. Rewrite the first one; a PRD without a heading gets one."""
    text = open(path, encoding="utf-8").read()
    head, fm, tail = split_fm(text)
    lines = tail.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith("# "):
            lines[i] = f"# {title}\n"
            break
    else:
        i = 1 if lines and lines[0].strip() == "---" else 0
        lines.insert(i, f"\n# {title}\n")
    write_atomic(path, head + ("".join(fm) if fm else "") + "".join(lines))
