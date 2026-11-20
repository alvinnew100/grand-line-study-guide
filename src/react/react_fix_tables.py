"""Author-side helper: escape `|` inside inline code in Markdown table rows (GFM needs \\| there).

  python src/react/react_fix_tables.py
"""
import glob, os

HERE = os.path.dirname(os.path.abspath(__file__))
BS = chr(92)


def fix_row(line):
    out, in_code, i = [], False, 0
    while i < len(line):
        ch = line[i]
        if ch == "`":
            in_code = not in_code
            out.append(ch)
        elif ch == "|" and in_code and (i == 0 or line[i - 1] != BS):
            out.append(BS + "|")
        else:
            out.append(ch)
        i += 1
    return "".join(out)


total = 0
for f in sorted(glob.glob(os.path.join(HERE, "lessons", "*.md"))):
    lines = open(f, encoding="utf-8").read().split("\n")
    fence, changed = False, 0
    for n, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fence = not fence
        if not fence and line.startswith("|") and "`" in line and line.count("`") % 2 == 0:
            new = fix_row(line)
            if new != line:
                lines[n] = new
                changed += 1
    if changed:
        open(f, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
        print(os.path.basename(f), changed)
        total += changed
print(total, "row(s) fixed")
