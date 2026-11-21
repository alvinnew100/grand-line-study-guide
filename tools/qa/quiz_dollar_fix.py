"""Escape literal dollar signs in quiz JSON strings so KaTeX does not read them as math.

Only strings with two or more unprotected dollars (outside code spans) are changed; each such dollar
becomes a JSON-escaped backslash-dollar, which the app renders as a plain "$" (AUTHORING.md rule).
Usage: python quizdollar_fix.py <src dir> <track> [<track> ...]
"""
import json
import pathlib
import re
import sys

BT = chr(96)
BS = chr(92)
FENCE = BT * 3
root = pathlib.Path(sys.argv[1])
tracks = sys.argv[2:]
str_lit = re.compile('"(?:[^"' + BS + BS + ']|' + BS + BS + '.)*"')


def unprotected(raw):
    """Indexes of dollars in a raw JSON literal that are outside code spans and not escaped."""
    idx, in_code = [], False
    for i, c in enumerate(raw):
        if c == BT:
            in_code = not in_code
        elif c == "$" and not in_code and raw[i - 1] != BS:
            idx.append(i)
    return idx


def fix_literal(m):
    raw = m.group(0)
    idx = unprotected(raw)
    if len(idx) < 2:
        return raw
    out = list(raw)
    for i in reversed(idx):
        out[i] = BS + BS + "$"
    return "".join(out)


changed = 0
for t in tracks:
    for p in sorted((root / t / "lessons").glob("*.md")):
        text = p.read_bytes().decode("utf-8")  # bytes: keep LF / CRLF exactly as they are

        def fix_block(m):
            body = m.group(2)
            new = "\n".join(str_lit.sub(fix_literal, ln) for ln in body.split("\n"))
            json.loads(new)  # must still be valid JSON
            return m.group(1) + new + m.group(3)

        new_text = re.sub("(" + FENCE + "quiz\r?\n)(.*?)(" + FENCE + ")", fix_block, text, flags=re.S)
        if new_text != text:
            p.write_bytes(new_text.encode("utf-8"))
            changed += 1
            print("fixed", p)
print(changed, "file(s) changed")
