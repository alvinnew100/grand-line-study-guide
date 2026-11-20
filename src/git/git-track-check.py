"""Author-side checks for the git track (not part of the site build).

  python src/git/git-track-check.py            # word counts, block checks, run python-run blocks
"""
import io, json, re, sys, contextlib, pathlib

HERE = pathlib.Path(__file__).parent
bad = 0
for f in sorted((HERE / "lessons").glob("*.md")):
    text = f.read_text(encoding="utf-8")
    words = len(text.split())
    notes = []
    if words < 2400:
        notes.append("SHORT")
    quizzes = re.findall(r"```quiz\s*\n(.*?)```", text, re.S)
    nq = 0
    for q in quizzes:
        try:
            items = json.loads(q)
            nq += len(items)
            for it in items:
                assert 0 <= it["answer"] < len(it["options"]) and it.get("explain")
        except Exception as e:  # noqa: BLE001
            notes.append("QUIZ-ERR %s" % e)
    if not 6 <= nq <= 8:
        notes.append("quiz=%d" % nq)
    prose = re.sub(r"```.*?```", "", text, flags=re.S)
    for w in re.findall(r"\b(simply|obviously|just|as you know)\b", prose, re.I):
        notes.append("BANNED:" + w)
    if "-b" in sys.argv:
        for ln in prose.splitlines():
            if re.search(r"\b(simply|obviously|just|as you know)\b", ln, re.I):
                print("   >>", ln[:160])
    for tag in ("[!INTERVIEW]", "[!TIP]", "[!WARNING]", "```mermaid", "```bash", "> **Source:**", "## In plain words", "**Before this lesson", "## Glossary"):
        if tag not in text:
            notes.append("missing " + tag)
    if text.count("```") % 2:
        notes.append("ODD FENCES")
    for n, code in enumerate(re.findall(r"```python-run\s*\n(.*?)```", text, re.S)):
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                exec(compile(code, "%s#%d" % (f.name, n), "exec"), {"__name__": "__main__"})
        except Exception as e:  # noqa: BLE001
            notes.append("PYRUN-ERR block %d: %r" % (n, e))
        if "-v" in sys.argv:
            print("---", f.name, n); print(buf.getvalue())
    if any(x != x.lower() or x.startswith("quiz") or x.startswith("missing") for x in notes):
        bad += 1
    print("%-36s %5d words  %s" % (f.name, words, "; ".join(notes)))
print("lessons needing attention:", bad)
