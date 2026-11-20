"""Author-side checks for the react track lessons (not part of the site build).

  python src/react/react_check.py

For every lesson: word count, banned beginner-hostile words in prose, required sections,
runs each js-run block in Node, and syntax-checks the <script> of each html-run block.
"""
import glob, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BANNED = re.compile(r"\b(simply|obviously|just|as you know)\b", re.I)
REQUIRED = ["**Before this lesson:**", "## In plain words", "## Glossary", "```quiz", "> **Source:**", "```mermaid", "## Summary", "## Pitfalls", "## Cheat sheet"]
bad = 0
for f in sorted(glob.glob(os.path.join(HERE, "lessons", "*.md"))):
    text = open(f, encoding="utf-8").read()
    name = os.path.basename(f)
    notes = []
    words = len(text.split())
    if words < 2400:
        notes.append(f"only {words} words")
    prose = re.sub(r"```.*?```", "", text, flags=re.S)
    prose = re.sub(r"`[^`\n]*`", "", prose)
    hits = sorted(set(m.group(0).lower() for m in BANNED.finditer(prose)))
    if hits:
        notes.append("banned words: " + ", ".join(hits))
    for r in REQUIRED:
        if r not in text:
            notes.append("missing " + r)
    if "html-run" not in text and "js-run" not in text:
        notes.append("no runnable block")
    for i, code in enumerate(re.findall(r"```js-run\s*\n(.*?)```", text, re.S)):
        r = subprocess.run(["node", "-e", code], capture_output=True, text=True, encoding="utf-8", timeout=20)
        if r.returncode != 0:
            notes.append(f"js-run #{i + 1} failed: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else '?'}")
    for i, page in enumerate(re.findall(r"```html-run\s*\n(.*?)```", text, re.S)):
        for script in re.findall(r"<script>(.*?)</script>", page, re.S):
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as t:
                t.write(script)
            r = subprocess.run(["node", "--check", t.name], capture_output=True, text=True, encoding="utf-8")
            os.unlink(t.name)
            if r.returncode != 0:
                notes.append(f"html-run #{i + 1} script syntax error")
    print(f"{words:6d}  {name}" + ("   <-- " + "; ".join(notes) if notes else ""))
    bad += bool(notes)
print(f"{bad} lesson(s) with notes")
sys.exit(1 if bad else 0)
