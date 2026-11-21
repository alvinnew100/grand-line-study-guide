"""List quiz strings whose unprotected dollar signs would be parsed as KaTeX math."""
import collections
import json
import pathlib
import re
import sys

BT = chr(96)
FENCE = BT * 3
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "src")
only = set(sys.argv[2:])
code_span = re.compile(BT + "[^" + BT + "]*" + BT)
hits = collections.defaultdict(list)


def strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, list):
        for y in x:
            yield from strings(y)
    elif isinstance(x, dict):
        for y in x.values():
            yield from strings(y)


for p in sorted(root.glob("*/lessons/*.md")):
    track = p.parent.parent.name
    if only and track not in only:
        continue
    text = p.read_text(encoding="utf-8")
    for block in re.findall(FENCE + "quiz\n(.*?)" + FENCE, text, re.S):
        try:
            data = json.loads(block)
        except ValueError:
            hits[track].append((p.name, "UNPARSEABLE QUIZ JSON"))
            continue
        for s in strings(data):
            bare = code_span.sub("", s)
            n = sum(1 for i, c in enumerate(bare) if c == "$" and (i == 0 or bare[i - 1] != chr(92)))
            if n >= 2:
                hits[track].append((p.name, s[:110]))

for track, items in sorted(hits.items(), key=lambda kv: -len(kv[1])):
    print(track, len(items))
    for name, s in items[:3]:
        print("   ", name, "|", s)
